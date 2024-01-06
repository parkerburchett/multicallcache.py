from eth_utils import to_checksum_address
from web3 import Web3
from typing import Any, Callable, Tuple
from multicall.signature import Signature
import inspect

# single tx gas limit. Using Alchemy's max value, not relevent for view only calls where gas is free.
GAS_LIMIT = 55_000_000


class HandlingFunctionFailed(Exception):
    def __init__(self, handling_function: Callable, decoded_value: Any, exception: Exception):
        function_source_code = inspect.getsource(handling_function)
        super().__init__(
            f"""handling_function raised an exception
        
        {function_source_code=}

        {decoded_value=} {type(decoded_value)=}
        Raised this error
        {exception=}"""
        )


class ReturnDataAndHandlingFunctionLengthMismatch(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class FailedToBuildCalldata(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class Call:
    def __init__(
        self,
        target: str,
        signature: str,
        arguments: Tuple[str],  # not certain if need
        data_labels: tuple[str] | str,
        handling_functions: Tuple[Callable] | Callable,
        w3: Web3,
    ) -> None:
        """
        target: the address that you want to make a funciton call on.
        signature: the method to call on target, eg `totalSupply()(uint256)`
        arguments: the tuple of arguments to pass to the funciton
        return_data_labels: what to label the returning data as
        handling_functions: what function to pass in the pythonic output of return_data_label into
        """
        arguments = arguments if isinstance(arguments, tuple) else (arguments,)
        data_labels = data_labels if isinstance(data_labels, tuple) else (data_labels,)
        handling_functions = handling_functions if isinstance(handling_functions, tuple) else (handling_functions,)
        if len(data_labels) != len(handling_functions):
            raise ReturnDataAndHandlingFunctionLengthMismatch(f"{len(self.data_labels)=} != {len(handling_functions)}=")

        self.data_labels = data_labels
        self.handling_functions = handling_functions
        self.target = to_checksum_address(target)
        self.signature = Signature(signature)
        self.arguments = arguments
        self.w3 = w3
        self.calldata = self.signature.encode_data(self.arguments)

    def to_rpc_call_args(self, block_id: int | str):
        """Convert this call into the format to send to a rpc node api request"""
        block_id_for_rpc_call = hex(block_id) if isinstance(block_id, int) else "latest"
        args = [
            {"to": self.target, "data": self.calldata, "gas": GAS_LIMIT},
            block_id_for_rpc_call,
        ]
        return args

    def decode_output(self, raw_bytes_output: bytes) -> dict[str, Any]:
        decoded_output = self.signature.decode_data(raw_bytes_output)

        if len(self.data_labels) != len(decoded_output):
            raise ReturnDataAndHandlingFunctionLengthMismatch(f"{len(self.data_labels)=} != {len(decoded_output)=}=")

        label_to_output = {}

        for label, handling_function, decoded_value in zip(self.data_labels, self.handling_functions, decoded_output):
            label_to_output[label] = handling_function(decoded_value)
        return label_to_output

    def __call__(self, block_id: int | str = "latest") -> dict[str, Any]:
        # TODO:, fail if attempting before the multicallV2 block was deployed
        # TODO: Maybe mock deploy it with the alchemy modify state before call)
        # TODO: wrap in error catching for rate limiting and or archive node failures
        # TODO: this has the same pattern as multicall can we unifiy them with inheritance
        rpc_args = self.to_rpc_call_args(block_id)
        raw_bytes_output = self.w3.eth.call(*rpc_args)
        label_to_output = self.decode_output(raw_bytes_output)
        return label_to_output
