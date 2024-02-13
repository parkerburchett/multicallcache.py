from typing import Any, Callable, Tuple
import inspect

from eth_utils import to_checksum_address
from web3 import Web3
from multicall.signature import Signature


# single tx gas limit. Using Alchemy's max value, not relevent for view only calls where gas is free.
GAS_LIMIT = 55_000_000
CALL_FAILED_REVERT_MESSAGE = "reverted_call_failed"
NOT_A_CONTRACT_REVERT_MESSAGE = "reverted_not_a_contract"


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
        arguments: tuple[str],
        data_labels: tuple[str] | str,
        handling_functions: Tuple[Callable] | Callable,
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
        self.calldata = self.signature.encode_data(self.arguments)
        self.chain_id = "1"

    def to_rpc_call_args(self, block_id: int | str):
        """Convert this call into the format to send to a rpc node api request"""
        block_id_for_rpc_call = hex(block_id) if isinstance(block_id, int) else "latest"
        args = [
            {"to": self.target, "data": self.calldata, "gas": GAS_LIMIT},
            block_id_for_rpc_call,
        ]
        return args

    def decode_output(self, raw_bytes_output: bytes) -> dict[str, Any]:

        if len(raw_bytes_output) == 0:
            label_to_output = {}
            # calls to addresses that don't have any code at that block return HexBytes('0x')
            for label in self.data_labels:
                label_to_output[label] = NOT_A_CONTRACT_REVERT_MESSAGE
            return label_to_output

        decoded_output = self.signature.decode_data(raw_bytes_output)

        if len(self.data_labels) != len(decoded_output):
            raise ReturnDataAndHandlingFunctionLengthMismatch(f"{len(self.data_labels)=} != {len(decoded_output)=}=")

        label_to_output = {}

        for label, handling_function, decoded_value in zip(self.data_labels, self.handling_functions, decoded_output):
            label_to_output[label] = handling_function(decoded_value)
        return label_to_output

    def __call__(self, w3: Web3, block_id: int | str = "latest") -> dict[str, Any]:
        # not optimized for speed, only use for testing that your calls work
        rpc_args = self.to_rpc_call_args(block_id)
        raw_bytes_output = w3.eth.call(*rpc_args)
        label_to_output = self.decode_output(raw_bytes_output)
        return label_to_output

    def to_id(self) -> str:
        # good enough until we run into a problem
        call_id = self.chain_id + " " + self.target + " " + self.signature.signature + " " + str(self.arguments)
        return call_id
