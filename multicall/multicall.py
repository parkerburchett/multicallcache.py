import asyncio
from collections import ChainMap
import itertools
import json
import multiprocessing
from time import time
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import hexbytes

import aiohttp
import numpy as np
from web3 import Web3
from web3.providers import HTTPProvider


from multicall import Call
from multicall import Signature
from multicall.constants import MULTICALL2_ADDRESSES, MULTICALL_ADDRESSES
from multicall.errors import EthRPCError
from multicall.loggers import setup_logger
from multicall.utils import chain_id

GAS_LIMIT = 55_000_000


# only support try and aggragate
class Multicall:
    """
    Just make only external calls don't touch the local sqlite database
    """

    def __init__(
        self,
        calls: List[Call],
        w3: Web3,
        max_concurrent_requests: int = 1,
        n_calls_per_batch:int = 50,
        batch_timeout: int = 300,
        ):
        if len(calls) == 0:
            raise ValueError('Must supply more than 0 calls')
        self.calls = calls
        self.w3 = w3
        self.max_concurrent_requests = max_concurrent_requests
        self.n_calls_per_batch= n_calls_per_batch
        self.batch_timeout = batch_timeout

        # function tryAggregate(bool requireSuccess, Call[] memory calls) public returns (Result[] memory returnData)
        # struct Result {
        #     bool success;
        #     bytes returnData; 
        # }
            
        self.multicall_sig = Signature("tryAggregate(bool,(address,bytes)[])((bool,bytes)[])")
        self.multicall_address = "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696" # only support ETH

        multicall_args = []
        for call in self.calls:
            single_call_calldata = call.signature.encode_data(call.arguments)
            multicall_args.append((call.target, single_call_calldata))

        args = (False, tuple(multicall_args))
        self.calldata = f"0x{self.multicall_sig.encode_data(args).hex()}"

        # why do I need multicall_as_call? 
        # -> because I need what was call.signature and call.returns for OldCall.decode output
        # self.multicall_as_call = Call(self.multicall_address, self.multicall_sig,)
    
    def to_rpc_call_args(self, block_id: int | None):
        """Convert this multicall into the format required fo for a rpc node api request"""
        block_id_for_rpc_call = hex(block_id) if isinstance(block_id, int) else 'latest'
        args = [{"to": self.multicall_address, "data": self.calldata, 'gas': GAS_LIMIT}, block_id_for_rpc_call]          
        return args
    
    def decode_outputs(self, hex_bytes_output: bytes) -> dict:
        # is decoded inside of a len 0 tuple , need to remove that layer of nesting
        decoded_outputs: tuple[tuple(bool, bytes)] = self.multicall_sig.decode_data(hex_bytes_output)[0] 
        label_to_output = {}

        for result, call in zip(decoded_outputs, self.calls):
            success, single_function_call_bytes = result # from struct Multicall.Result
            if success is True:
                single_call_label_to_output = call.decode_output(single_function_call_bytes)
                label_to_output.update(single_call_label_to_output)
            else:
                pass
                print(call, 'failed')
 
        return label_to_output

    def __call__(self, block_id: int | None) -> Dict[str, Any]:
        rpc_args = self.to_rpc_call_args(block_id)
        raw_bytes_output= self.w3.eth.call(*rpc_args)
        label_to_output = self.decode_outputs(raw_bytes_output) 
        return label_to_output




@dataclass
class CallResponseData:
    call: Call
    pythonic_output: Any # the data after it is passed throuhg the return type
    bytes_output: bytes # redundent
    function_success: Optional[bool]    

logger = setup_logger(__name__)

CallResponse = Tuple[Union[None, bool], bytes] # TODO remove this


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

# gas_limit
#  NOTE: this parameter has a cap of 550 million gas per request.
# Reach out to us at support@alchemy.com if you want to increase this limit!
# https://docs.alchemy.com/reference/eth-call

# class MulticallV2:

#     def __init__(
#         self,
#         calls: List[Call],
#         block_id: int,
#         w3: Web3,
#         db_path:str = 'cache_db.sqlite', # make follow best practices
#         require_success: bool = False, # default to handlers are f(success, data) -> some operation(data)
#         max_concurrent_requests: int = 1,
#         n_calls_per_batch:int = 50,
#         batch_timeout: int = 300,
#         ):
#             self.calls = calls
#             self.block_id = block_id
#             self.w3 = w3
#             self.db_path = db_path
#             self.require_success = require_success
#             self.max_concurrent_requests = max_concurrent_requests
#             self.n_calls_per_batch= n_calls_per_batch
#             self.batch_timeout = batch_timeout

#             # Consider making these constants in the file
#             self.chainid = chain_id(w3)
#             self.node_uri = w3.provider.endpoint_uri # string? # what the heck is this?
#             self.gas_limit = 50_000_000

#             # kind of hazy about this. I'm only using this for Ethereum
#             if require_success is True:
#                 multicall_map = (
#                     MULTICALL_ADDRESSES
#                     if self.chainid in MULTICALL_ADDRESSES
#                     else MULTICALL2_ADDRESSES
#                 )
#                 self.multicall_sig = "aggregate((address,bytes)[])(uint256,bytes[])"
#             else:
#                 multicall_map = MULTICALL2_ADDRESSES

#                 self.multicall_sig = "tryBlockAndAggregate(bool,(address,bytes)[])(uint256,uint256,(bool,bytes)[])"

#             self.multicall_address = multicall_map[self.chainid]

#     def __repr__(self) -> str:
#         return f'Multicall {", ".join(set(map(lambda call: call.function, self.calls)))}, {len(self.calls)} calls'   

#     def __call__(self) -> Dict[str, Any]:
#         if len(self.calls) == 0:
#             return {}
#         else:
#             return self.fetch_outputs_refactored()

#     def encode_args(self, call_batch: List[Call]):
#         args = get_args(call_batch, self.require_success)
#         calldata = f"0x{self.aggregate.signature.encode_data(args).hex()}"

#         args = [
#             {"to": self.aggregate.target, "data": calldata},
#             hex(self.block_id) if self.block_id is not None else "latest",
#         ]
#         # why incode the args at the start?

#         if self.gas_limit:
#             args[0]["gas"] = f"0x{self.gas_limit:x}"

#         return args

#     def decode_outputs(self, calls_batch: List[Call], result: bytes) -> List[CallResponseData]:
#         if self.require_success is True:
#             _, outputs = Call.decode_output(
#                 result, self.aggregate.signature, self.aggregate.returns
#             )
#             outputs = unpack_aggregate_outputs(outputs)
#         else:
#             _, _, outputs = Call.decode_output(
#                 result, self.aggregate.signature, self.aggregate.returns
#             )

#         response_data = []

#         for call, response in zip(calls_batch, outputs):
#             success, bytes_output = response
#             pythonic_output = Call.decode_output(bytes_output, call.signature, None, success)
#             response_data.append(CallResponseData(call, pythonic_output, bytes_output, success))

#         return response_data

#     # move this up a level, all multicalls (regardless of being on the same or differnt block
#     # should use the same client Session
#     async def rpc_aggregator(
#         self, call_batches: List[List[Call]]
#     ) -> Tuple[Exception | None, List[CallResponseData]]:
#         async with aiohttp.ClientSession(
#             connector=aiohttp.TCPConnector(limit=self.max_concurrent_requests),
#             timeout=aiohttp.ClientTimeout(self.batch_timeout),
#         ) as session:
#             return await asyncio.gather(
#                 *[self.rpc_eth_call(session, calls) for calls in call_batches]
#             ) 

#     def _determine_error(self, data): # I'm not using theses
#         if "error" in data:
#             if "out of gas" in data["error"]["message"]:
#                 return EthRPCError.OUT_OF_GAS
#             # this is never happening.
#             # Maybe this was an issue when this library was written
#             # but I don't think so now
#             elif "execution reverted" in data["error"]["message"]:
#                 return EthRPCError.EXECUTION_REVERTED
#             else:
#                 return EthRPCError.UNKNOWN
#         return None

#     async def rpc_eth_call(self, session: aiohttp.ClientSession, calls_batch:list[Call]
#         )-> Tuple[EthRPCError | None, List[CallResponseData]]:
#         """Make the multicall with many calls in it"""
#         args = self.encode_args(calls_batch) # might run into malformed calls here. # maybe don't worry about it
#         async with session.post(
#             self.node_uri,
#             headers={"Content-Type": "application/json"},
#             data=json.dumps(
#                 {
#                     "params": args,
#                     "method": "eth_call",
#                     "id": 1,
#                     "jsonrpc": "2.0",
#                 }
#             ),
#         ) as response:

#             assert response.status == 200, RuntimeError(f"Network Error: {response}")
#             data = await response.json()
#             error = self._determine_error(data)
#             if error is None:
#                 bytes_result = bytes.fromhex(data["result"][2:])
#                 cleaned_results = self.decode_outputs(calls_batch, bytes_result)
#                 return error, cleaned_results
#             else:
#                 return error, []

#     def _fetch_data(self, calls_remaining: list[Call], n_calls_per_batch: int) -> List[CallResponseData]:
#         num_batches = len(calls_remaining) // n_calls_per_batch ## make sure to scale this down when it fails, 
#         call_batches = np.array_split(calls_remaining, num_batches)
#         call_result_tuples = asyncio.run(self.rpc_aggregator(call_batches))
#         externally_fetched_data = [data for error, data in call_result_tuples if error is None]
#         return externally_fetched_data

#     def _fetch_locally(self) -> Tuple[List[Call], List[CallResponseData]]:
#         return self.calls, []

#     def _save_locally(self, externally_fetched_data: List[CallResponseData]) -> None:
#         pass


#     def fetch_outputs_refactored(self) -> Dict[str, Any]:
#         calls_remaining, locally_fetched_data = self._fetch_locally()

#         externally_fetched_data = self._fetch_data(calls_remaining, self.n_calls_per_batch)
#         self._save_locally(externally_fetched_data)
#         all_fetched_data = [*locally_fetched_data, * externally_fetched_data]
#         cleaned_outputs = self._post_process_call_response_data(all_fetched_data)
#         return cleaned_outputs


#     def _post_process_call_response_data(self, call_response_data: List[CallResponseData]) -> list[dict]:
#         cleaned_data = []
#         for data in call_response_data:
#             call = data.call
#             post_function_output_data = Call.decode_output(data.bytes_output, call.signature, call.returns, data.function_success)
#             cleaned_data.append(post_function_output_data)
#         return cleaned_data # to a single dict? 
        
#     @property
#     def aggregate(self) -> Call:
#         return Call(
#             self.multicall_address,
#             self.multicall_sig,
#             returns=None,
#             block_id=self.block_id,
#             _w3=Web3(HTTPProvider(self.node_uri)),
#             gas_limit=self.gas_limit,
#         )

