from typing import Any, Callable, Tuple
import hashlib
from pathlib import Path

import inspect

from eth_utils import to_checksum_address
from web3 import Web3, exceptions

# from multicall.cache import get_one_value # circular import issues
from multicall.signature import Signature
from multicall.constants import CACHE_PATH

# what does a failed call look like?

# single tx gas limit. Using Alchemy's max value, not relevent for view only calls where gas is free.
GAS_LIMIT = 55_000_000
CALL_FAILED_REVERT_MESSAGE = "reverted_call_failed"
NOT_A_CONTRACT_REVERT_MESSAGE = "reverted_not_a_contract"
REVERTED_UNKNOWN_MESSAGE = "REVERTED"


class HandlingFunctionFailed(Exception):
    def __init__(self, handling_function: Callable, decoded_value: Any, exception: Exception):
        function_source_code = inspect.getsource(handling_function)  #
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
        target: the address that you want to make a function call on.
        signature: the method to call on target, eg `totalSupply()(uint256)`
        arguments: the tuple of arguments to pass to the function
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
        self.chain_id = "1"  # hardcode for Ethereum

    def to_rpc_call_args(self, block_id: int | str):
        """Convert this call into the format to send to a rpc node api request"""
        block_id_for_rpc_call = hex(block_id) if isinstance(block_id, int) else "latest"
        args = [
            {
                "to": self.target,
                "data": self.calldata,
                "gas": hex(GAS_LIMIT),
            },  # if using w3.eth.call(*rpc_args) , don't need ot hex(gas limit)
            block_id_for_rpc_call,
        ]
        return args

    def decode_output(self, raw_bytes_output: bytes) -> dict[str, Any]:
        """applies the handling function and converts raw_bytes_output to a dict of pythonic objects"""

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

    def to_id(self, block: int) -> bytes:
        if not isinstance(block, int):
            raise ValueError("Must define a block to make a call ID")

        call_id = (
            self.chain_id
            + " "
            + self.target
            + " "
            + self.signature.signature
            + " "
            + str(self.arguments)
            + " "
            + str(block)
        )

        hash_object = hashlib.sha256()
        hash_object.update(call_id.encode("utf-8"))
        return hash_object.digest()

    def __call__(self, w3: Web3, block_id: int | str = "latest", cache="default") -> dict[str, Any]:
        """Primary entry point, for fast naive use"""
        # happy path
        cache_path = CACHE_PATH if cache == "default" else cache

        if isinstance(block_id, int):
            # TODO this is for circular import issues, (call.py <-> cache.py)
            # refactor these to not have circular imports or need to import here
            from multicall.cache import get_one_value, isCached

            already_cached = isCached(self, block_id, cache_path)
            # RPC call, TODO remove when not needed, make some assumptions
            finalized_block = w3.eth.get_block("finalized").number
            block_is_finalized = block_id < finalized_block

            if block_is_finalized and not already_cached:
                _save_data(w3, self, block_id, cache_path)

            success, raw_bytes_output = get_one_value(self, block_id, cache_path)
            if not success:
                raise exceptions.ContractLogicError()
            else:
                return self.decode_output(raw_bytes_output)

        else:
            # TODO if if block id = finalized then it should be cached, but this code does not cache it
            # not cached and it shouldn't be cached because block_id is not finalized
            rpc_args = self.to_rpc_call_args(block_id)
            raw_bytes_output = w3.eth.call(*rpc_args)  # might raise exceptions.ContractLogicError()
            return self.decode_output(raw_bytes_output)


# TODO, goal: fully abstract away the finalized block issue.


def _save_data(w3: Web3, call: Call, block: int, cache_path: Path):
    """Default speedy behavior assumes block is finalized on ETH,

    1. if we already have the data
    2. if not local: fetch, save to disk

    """
    from multicall.fetch_multicall_across_blocks import simple_sequential_fetch_multicalls_across_blocks_and_save

    simple_sequential_fetch_multicalls_across_blocks_and_save([call], [block], w3, cache_path)
