from typing import Any, Dict, List

from web3 import Web3


from multicall import Call
from multicall import Signature

GAS_LIMIT = 55_000_000


class Multicall:

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
        self.multicall_sig = Signature("tryAggregate(bool,(address,bytes)[])((bool,bytes)[])")
        self.multicall_address = "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696" # only support ETH

        multicall_args = []
        for call in self.calls:
            single_call_calldata = call.signature.encode_data(call.arguments)
            multicall_args.append((call.target, single_call_calldata))
        self.calldata = f"0x{self.multicall_sig.encode_data((False, tuple(multicall_args))).hex()}"
    
    def to_rpc_call_args(self, block_id: int | None):
        """Convert this multicall into the format required fo for a rpc node api request"""
        block_id_for_rpc_call = hex(block_id) if isinstance(block_id, int) else 'latest'
        args = [{"to": self.multicall_address, "data": self.calldata, 'gas': GAS_LIMIT}, block_id_for_rpc_call]          
        return args
    
    def decode_outputs(self, hex_bytes_output: bytes) -> dict:
        decoded_outputs: tuple[tuple(bool, bytes)] = self.multicall_sig.decode_data(hex_bytes_output)[0]
    
        # is decoded into a tuple of Result.
        # struct Result {
        #     bool success;
        #     bytes returnData; 
        # }

        label_to_output = {}
        
        for result, call in zip(decoded_outputs, self.calls):
            success, single_function_call_bytes = result # from struct Multicall.Result
            if success is True:
                single_call_label_to_output = call.decode_output(single_function_call_bytes)
                label_to_output.update(single_call_label_to_output)

        return label_to_output

    def __call__(self, block_id: int | None) -> Dict[str, Any]:
        rpc_args = self.to_rpc_call_args(block_id)
        raw_bytes_output = self.w3.eth.call(*rpc_args)
        label_to_output = self.decode_outputs(raw_bytes_output) 
        return label_to_output
