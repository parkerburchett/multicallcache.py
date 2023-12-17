import eth_retry
from eth_typing import Address, ChecksumAddress, HexAddress
from eth_typing.abi import Decodable
from eth_utils import to_checksum_address
from web3 import Web3
from typing import Any, Callable, Iterable, List, Optional, Tuple, Union
from eth_typing import Address, ChecksumAddress, HexAddress
from multicall import Signature
from enum import Enum
import inspect

GAS_LIMIT = 55_000_000
# alchemy default gas limit, tx will revert if they exceed this theshsold, 
# non issue this won't happen. It ought to timeout faster


class HandlingFunctionFailed(Exception):
    def __init__(self, handling_function: Callable, decoded_value: Any, exception: Exception):
        function_sournce_code = inspect.getsource(handling_function)
        super().__init__(f"""Inside of multicall.Call then handling function raised an uncaught exception
        {function_sournce_code=}
        {decoded_value=} {type(decoded_value)=}
        Raised this error
        {exception=}"""
        )


class FunctionCallResponseType(Enum):
    SUCCEEDED: 1
    REVERTED: 2


# only supports aggregate not try and aggregate
class Call:
    def __init__(
        self,
        target: ChecksumAddress, # only support checksum addresses
        signature: str,
        arguments: Tuple[str],
        return_data_labels: Tuple[str],
        return_handling_functions: Tuple[Callable],
        w3: Web3
    ) -> None:
        """
        target: the address that you want to make a funciton call on. 
        signature: the method to call on target, eg `totalSupply()(uint256)`
        arguments: the tuple of arguments to pass to the funciton  
        return_data_label: what to label the returning data as
        return_handling_function: what function to pass in the pythonic output of return_data_label into


        Unit tests to include

        All of these combinations needs to work

        unction args that need to work
        1. Method with no data
        2. Method with 1 arg of each valid type
        3. Method with 2 + args of each valid type

        return Data that must be handled with (success = True) and not

        # just handle intenrally the success flag, 

        if try_block_and_aggregate:
            success, *pythonic_response_data = output?

            if success: 
                return self.return_handling_function(*pythonic_response_data)
            else:
                return None ? FunctionCallResponseType.REVERTED

        1. contract not deployed
        2. None

        """
        self.target = to_checksum_address(target)
        self.signature = Signature(signature)
        self.arguments = arguments
        self.return_data_labels = return_data_labels
        self.return_handling_functions = return_handling_functions
        self.calldata = self.signature.encode_data(self.arguments)
        self.w3 = w3

    # alias prep_args
    def to_rpc_call_args(self, block_id: int | None):
        """Convert this call into the format required for the args for a rpc node api request"""
        block_id_for_rpc_call = hex(block_id) if isinstance(block_id, int) else 'latest'
        args = [{"to": self.target, "data": self.calldata, 'gas': GAS_LIMIT}, block_id_for_rpc_call]          
        return args
    
    def decode_output(self, raw_bytes_output: bytes) -> dict[str, Any]:

        decoded_output = self.signature.decode_data(raw_bytes_output)

        label_to_output = {}

        for label, handling_function, decoded_value in zip(
            self.return_data_labels,
            self.return_handling_functions,
            decoded_output
            ):
                try:
                    processed_output = handling_function(decoded_value)
                except Exception as exception:
                    raise HandlingFunctionFailed(handling_function, decoded_value, exception)
                
                label_to_output[label] = processed_output
        
        return label_to_output
            

    def __call__(self, block_id: int | None) -> dict[str, Any]:
        rpc_args = self.to_rpc_call_args(block_id)
        raw_bytes_output = self.w3.eth.call(*rpc_args)
        label_to_output = self.decode_output(raw_bytes_output)
        return label_to_output
