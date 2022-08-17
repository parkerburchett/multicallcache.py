import asyncio
from concurrent.futures import Future, ProcessPoolExecutor
import itertools
import multiprocessing
import requests
from time import time
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import requests
from web3 import Web3
from web3.providers import HTTPProvider

from multicall import Call
from multicall.constants import (
    MULTICALL2_ADDRESSES,
    MULTICALL2_BYTECODE,
    MULTICALL_ADDRESSES,
)
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


class Multicall:
    class MulticallBatch:
        def __init__(
            self,
            provider: HTTPProvider,
            block_id: Optional[int],
            gas_limit: Optional[int],
            require_success: bool,
        ):
            self.block_id = block_id
            self.gas_limit = gas_limit
            self.require_success = require_success
            self.w3 = Web3(provider)
            self.chainid = chain_id(self.w3)
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

        def fetch_outputs(self, calls: List[Call], retries: int) -> List[CallResponse]:
            for attempt in range(retries):
                try:
                    args = get_args(calls, self.require_success)
                    if self.require_success is True:
                        _, outputs = self.aggregate(args)
                        outputs = unpack_aggregate_outputs(outputs)
                    else:
                        _, _, outputs = self.aggregate(args)
                    outputs = [
                        Call.decode_output(
                            output, call.signature, call.returns, success
                        )
                        for call, (success, output) in zip(calls, outputs)
                    ]
                    return outputs
                except Exception as e:
                    logger.warning(e)
                    if "out of gas" in str(e) or attempt == retries - 1:
                        # revert to eth_call
                        outputs = []
                        for call in calls:
                            call.w3 = self.w3
                            try:
                                outputs.append(call())
                            except Exception as e:
                                if self.require_success:
                                    raise e
                                outputs.append(
                                    Call.decode_output(
                                        None, call.signature, call.returns, False
                                    )
                                )
                        return outputs

            return []

        @property
        def aggregate(self) -> Call:
            return Call(
                self.multicall_address,
                self.multicall_sig,
                returns=None,
                block_id=self.block_id,
                _w3=self.w3,
                gas_limit=self.gas_limit,
            )

    def __init__(
        self,
        w3_uri: str,
        calls: List[Call],
        batch_size: int = 100,
        block_id: Optional[int] = None,
        gas_limit: Optional[int] = 1 << 31,
        retries: int = 3,
        require_success: bool = True,
        workers: int = min(10, multiprocessing.cpu_count()),
    ) -> None:
        self.calls = calls
        self.batch_size = batch_size
        self.block_id = block_id
        self.gas_limit = gas_limit
        self.retries = retries
        self.require_success = require_success
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=workers, pool_maxsize=workers
        )
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        self.provider = HTTPProvider(w3_uri, session=session)
        self.workers = ProcessPoolExecutor(max_workers=workers)

    def __repr__(self) -> str:
        return f'Multicall {", ".join(set(map(lambda call: call.function, self.calls)))}, {len(self.calls)} calls'

    def __call__(self) -> Dict[str, Any]:
        if len(self.calls) == 0:
            return {}
        start = time()
        response = self.execute()
        logger.debug(f"Multicall took {time() - start}s")
        return response

    def execute(self) -> Dict[str, Any]:
        futures = []
        for batch in chunks(self.calls, self.batch_size):
            futures.append(
                self.workers.submit(
                    _dispatch_multicall_batch,
                    self.provider,
                    self.block_id,
                    self.gas_limit,
                    self.retries,
                    self.require_success,
                    batch,
                )
            )
        outputs = itertools.chain(*map(Future.result, futures))
        return {name: result for output in outputs for name, result in output.items()}


def _dispatch_multicall_batch(
    provider: HTTPProvider,
    block_id: int,
    gas_limit: int,
    retries: int,
    require_success: bool,
    batch: List[Call],
):
    return Multicall.MulticallBatch(
        provider,
        block_id,
        gas_limit,
        require_success,
    ).fetch_outputs(batch, retries)
