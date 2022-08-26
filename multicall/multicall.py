import asyncio
from collections import ChainMap
import itertools
import json
import multiprocessing
from time import time
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
from web3 import Web3
from web3.providers import HTTPProvider

from multicall import Call
from multicall.constants import MULTICALL2_ADDRESSES, MULTICALL_ADDRESSES
from multicall.errors import EthRPCError
from multicall.loggers import setup_logger
from multicall.utils import chunks, chain_id


logger = setup_logger(__name__)

CallResponse = Tuple[Union[None, bool], bytes]


def get_args(
    calls: List[Call], require_success: bool = True
) -> List[Union[bool, List[List[Any]]]]:
    if require_success is True:
        return [[[call.target, call.data] for call in calls]]
    return [require_success, [[call.target, call.data] for call in calls]]


def unpack_aggregate_outputs(outputs: Any) -> Tuple[CallResponse, ...]:
    return tuple((None, output) for output in outputs)


def unpack_batch_results(batch_results: List[List[CallResponse]]) -> List[CallResponse]:
    return [result for batch in batch_results for result in batch]


def _initialize_multiprocessing():
    if multiprocessing.get_start_method(allow_none=True) is None:
        start_methods = multiprocessing.get_all_start_methods()
        if "forkserver" in start_methods:
            multiprocessing.set_start_method("forkserver")
        elif "spawn" in start_methods:
            multiprocessing.set_start_method("spawn")

    if multiprocessing.get_start_method(allow_none=False) == "fork":
        logger.warning(
            "Using fork as multiprocessing start_method, memory usage may be high."
        )


class Multicall:
    def __init__(
        self,
        calls: List[Call],
        batch_size: Optional[int] = None,
        block_id: Optional[int] = None,
        gas_limit: Optional[int] = 1 << 31,
        retries: int = 3,
        require_success: bool = True,
        _w3: Optional[Web3] = None,
        max_conns: int = 20,
        max_workers: int = min(12, multiprocessing.cpu_count() - 1),
        # when the number of function calls to execute is above this threshold, multiprocessing is used
        parallel_threshold: int = 1,
        # timeout in seconds for a multicall batch
        batch_timeout: int = 300,
    ) -> None:
        self.calls = calls
        self.batch_size = (
            batch_size if batch_size is not None else -(-len(calls) // max_conns)
        )
        self.block_id = block_id
        self.gas_limit = gas_limit
        self.retries = retries
        self.require_success = require_success
        self.node_uri = _w3.provider.endpoint_uri if _w3 else None
        self.max_workers = max_workers
        self.parallel_threshold = parallel_threshold if max_workers > 1 else 1 << 31
        self.max_conns = max_conns
        self.chainid = chain_id(_w3)
        if require_success is True:
            multicall_map = (
                MULTICALL_ADDRESSES
                if self.chainid in MULTICALL_ADDRESSES
                else MULTICALL2_ADDRESSES
            )
            self.multicall_sig = "aggregate((address,bytes)[])(uint256,bytes[])"
        else:
            multicall_map = MULTICALL2_ADDRESSES
            self.multicall_sig = "tryBlockAndAggregate(bool,(address,bytes)[])(uint256,uint256,(bool,bytes)[])"
        self.multicall_address = multicall_map[self.chainid]
        self.batch_timeout = batch_timeout

    def __repr__(self) -> str:
        return f'Multicall {", ".join(set(map(lambda call: call.function, self.calls)))}, {len(self.calls)} calls'

    def __call__(self) -> Dict[str, Any]:
        if len(self.calls) == 0:
            return {}

        start = time()
        response: Dict[str, Any]
        if -(-len(self.calls) // self.batch_size) > self.parallel_threshold:
            with multiprocessing.Pool(processes=self.max_workers) as p:
                response = self.fetch_outputs(p)
        else:
            response = self.fetch_outputs()
        logger.debug(f"Multicall took {time() - start}s")
        return response

    def encode_args(self, calls_batch: List[Call]) -> List[Dict]:
        args = get_args(calls_batch, self.require_success)
        calldata = f"0x{self.aggregate.signature.encode_data(args).hex()}"

        args = [
            {"to": self.aggregate.target, "data": calldata},
            self.block_id if self.block_id is not None else "latest",
        ]

        if self.gas_limit:
            args[0]["gas"] = f"0x{self.gas_limit:x}"

        return args

    def decode_outputs(self, calls_batch: List[Call], result: bytes):
        if self.require_success is True:
            _, outputs = Call.decode_output(
                result, self.aggregate.signature, self.aggregate.returns
            )
            outputs = unpack_aggregate_outputs(outputs)
        else:
            _, _, outputs = Call.decode_output(
                result, self.aggregate.signature, self.aggregate.returns
            )

        outputs = [
            Call.decode_output(output, call.signature, call.returns, success)
            for call, (success, output) in zip(calls_batch, outputs)
        ]

        return {name: result for output in outputs for name, result in output.items()}

    async def rpc_eth_call(self, session: aiohttp.ClientSession, args):

        async with session.post(
            self.node_uri,
            headers={"Content-Type": "application/json"},
            data=json.dumps(
                {
                    "params": args,
                    "method": "eth_call",
                    "id": 1,
                    "jsonrpc": "2.0",
                }
            ),
        ) as response:

            assert response.status == 200, RuntimeError(f"Network Error: {response}")
            data = await response.json()
            if "error" in data:
                if "out of gas" in data["error"]["message"]:
                    return EthRPCError.OUT_OF_GAS
                elif "execution reverted" in data["error"]["message"]:
                    return EthRPCError.EXECUTION_REVERTED
                else:
                    return EthRPCError.UNKNOWN
            return bytes.fromhex(data["result"][2:])

    async def rpc_aggregator(
        self, args_list: List[List]
    ) -> List[Union[EthRPCError, bytes]]:

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=self.max_conns),
            timeout=aiohttp.ClientTimeout(self.batch_timeout),
        ) as session:
            return await asyncio.gather(
                *[self.rpc_eth_call(session, args) for args in args_list]
            )

    def fetch_outputs(self, p: Optional[multiprocessing.Pool] = None) -> Dict[str, Any]:
        calls = self.calls

        outputs = {}

        for batch_size in itertools.chain(
            map(lambda i: self.batch_size // (1 << i), range(self.retries)), [1]
        ):

            if len(calls) == 0:
                break

            batches = [
                calls[batch : batch + batch_size]
                for batch in range(-(-len(calls) // batch_size))
            ]

            encoded_args: List
            if p and len(batches) > self.parallel_threshold:
                encoded_args = list(
                    p.imap(
                        self.encode_args,
                        batches,
                        chunksize=-(-len(batches) // self.max_workers),
                    )
                )
            else:
                encoded_args = list(map(self.encode_args, batches))

            results = asyncio.run(self.rpc_aggregator(encoded_args))

            if self.require_success and EthRPCError.EXECUTION_REVERTED in results:
                raise RuntimeError("Multicall with require_success=True failed.")

            # find remaining calls
            calls = list(
                itertools.chain(
                    *[
                        batches[i]
                        for i, x in enumerate(results)
                        if x == EthRPCError.OUT_OF_GAS
                    ]
                )
            )

            successes = [
                (batch, result)
                for batch, result in zip(batches, results)
                if not isinstance(result, EthRPCError)
            ]
            batches, results = zip(*successes) if len(successes) else ([], [])

            if p and len(batches) > self.parallel_threshold:
                outputs.update(
                    ChainMap(
                        *p.starmap(
                            self.decode_outputs,
                            zip(batches, results),
                            chunksize=-(-len(batches) // self.max_workers),
                        )
                    )
                )
            else:
                outputs.update(ChainMap(*map(self.decode_outputs, batches, results)))

        return outputs

    @property
    def aggregate(self) -> Call:
        return Call(
            self.multicall_address,
            self.multicall_sig,
            returns=None,
            block_id=self.block_id,
            _w3=Web3(HTTPProvider(self.node_uri)),
            gas_limit=self.gas_limit,
        )
