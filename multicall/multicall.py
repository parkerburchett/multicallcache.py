import asyncio
from concurrent.futures import Future, ThreadPoolExecutor
import itertools
import multiprocessing
from time import time
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import requests
from web3 import Web3

from multicall import Call
from multicall.constants import MULTICALL2_ADDRESSES, MULTICALL2_BYTECODE, MULTICALL_ADDRESSES
from multicall.loggers import setup_logger
from multicall.utils import chunks, chain_id, state_override_supported


logger = setup_logger(__name__)

CallResponse = Tuple[Union[None,bool],bytes]

def get_args(calls: List[Call], require_success: bool = True) -> List[Union[bool,List[List[Any]]]]:
    if require_success is True:
        return [[[call.target, call.data] for call in calls]]
    return [require_success, [[call.target, call.data] for call in calls]]

def unpack_aggregate_outputs(outputs: Any) -> Tuple[CallResponse,...]:
    return tuple((None, output) for output in outputs)

def unpack_batch_results(batch_results: List[List[CallResponse]]) -> List[CallResponse]:
    return [result for batch in batch_results for result in batch]


class Multicall:
    def __init__(
        self,
        calls: List[Call],
        batch_size: int = 100,
        block_id: Optional[int] = None,
        retries: int = 3,
        require_success: bool = True,
        _w3: Optional[Web3] = None,
        workers: int = min(10, multiprocessing.cpu_count()),
    ) -> None:
        self.calls = calls
        self.batch_size = batch_size
        self.block_id = block_id
        self.retries = retries
        self.require_success = require_success
        self.w3 = _w3
        self.chainid = chain_id(self.w3)
        if require_success is True:
            multicall_map = MULTICALL_ADDRESSES if self.chainid in MULTICALL_ADDRESSES else MULTICALL2_ADDRESSES
            self.multicall_sig = 'aggregate((address,bytes)[])(uint256,bytes[])'
        else:
            multicall_map = MULTICALL2_ADDRESSES
            self.multicall_sig = 'tryBlockAndAggregate(bool,(address,bytes)[])(uint256,uint256,(bool,bytes)[])'
        self.multicall_address = multicall_map[self.chainid]
        self.workers = ThreadPoolExecutor(workers)

    def __repr__(self) -> str:
        return f'Multicall {", ".join(set(map(lambda call: call.function, self.calls)))}, {len(self.calls)} calls'

    def __call__(self) -> Dict[str,Any]:
        if self.w3 is None:
            raise RuntimeError
        if len(self.calls) == 0:
            return {}
        start = time()
        response = self.execute()
        logger.debug(f"Multicall took {time() - start}s")
        return response

    def execute(self) -> Dict[str,Any]:
        futures = []
        for batch in chunks(self.calls, self.batch_size):
            futures.append(self.workers.submit(self.fetch_outputs, batch, self.retries))
        outputs = itertools.chain(*map(Future.result, futures))
        return {
            name: result
            for output in outputs
            for name, result in output.items()
        }

    def fetch_outputs(self, calls: List[Call], retries: int) -> List[CallResponse]:
        for _ in range(retries):
            try:
                args = get_args(calls, self.require_success)
                if self.require_success is True:
                    _, outputs = self.aggregate(args)
                    outputs = unpack_aggregate_outputs(outputs)
                else:
                    _, _, outputs = self.aggregate(args)
                outputs = [
                    Call.decode_output(output, call.signature, call.returns, success)
                    for call, (success, output) in zip(calls, outputs)
                ]
                return outputs
            except Exception as e:
                logger.warning(e)

        return []


    @property
    def aggregate(self) -> Call:
        if state_override_supported(self.w3):
            return Call(
                self.multicall_address,
                self.multicall_sig,
                returns=None,
                block_id=self.block_id,
                state_override_code=MULTICALL2_BYTECODE,
                _w3=self.w3,
                gas_limit=1<<31,
            )
        
        # If state override is not supported, we simply skip it.
        # This will mean you're unable to access full historical data on chains without state override support.
        return Call(
            self.multicall_address,
            self.multicall_sig,
            returns=None,
            block_id=self.block_id,
            _w3=self.w3,
            gas_limit=1<<31,
        )
