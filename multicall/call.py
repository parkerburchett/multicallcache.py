from typing import Any, Callable, Tuple
import hashlib
from pathlib import Path

import inspect

from eth_utils import to_checksum_address
from web3 import Web3, exceptions


# from multicall.cache import get_one_value # circular import issues
from multicall.signature import Signature
from multicall.constants import CACHE_PATH


# single tx gas limit. Using Alchemy's max value, not relevent for view only calls where gas is free.
GAS_LIMIT = 55_000_000
CALL_FAILED_REVERT_MESSAGE = "REVERTED"
NOT_A_CONTRACT_REVERT_MESSAGE = "REVERTED"  # TODO add the capacity to tell these apart
REVERTED_UNKNOWN_MESSAGE = "REVERTED"


# TODO add these to unit tests
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
        self.message = message  # this doesn't seem like the right syntax
        super().__init__(self.message)


class FailedToBuildCalldata(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class Call:
    # todo, if handling functions is empty, default to the identity funciton 
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
        self.chain_id = "1"  # hardcode for Ethereum TODO add check for base
    

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
        """A unique identifer of the immutable charactaristics of this call"""
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
            from multicall.cache import get_isCached_success_raw_bytes_output_for_a_single_call

            # step 1 if we already have it return it, most happy path, only 1 call
            isCached, success, raw_bytes_output = get_isCached_success_raw_bytes_output_for_a_single_call(
                self, block_id, cache_path
            )
            if isCached:
                if success:
                    return self.decode_output(raw_bytes_output)
                else:
                    raise exceptions.ContractLogicError()

            if block_id < w3.eth.get_block("finalized").number:
                _save_data(w3, self, block_id, cache_path)
                # TODO gets external data, saves it, then reads it from disk
                # one read is redundent, can remove
                isCached, success, raw_bytes_output = get_isCached_success_raw_bytes_output_for_a_single_call(
                    self, block_id, cache_path
                )
                if isCached:
                    if success:
                        return self.decode_output(raw_bytes_output)
                    else:
                        raise exceptions.ContractLogicError()

            else:
                # make a call and don't save the result
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
