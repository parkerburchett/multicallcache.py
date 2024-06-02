from web3 import Web3
import aiohttp
from aiolimiter import AsyncLimiter
import pickle

from multicall.call import Call, GAS_LIMIT, CALL_FAILED_REVERT_MESSAGE
from multicall.signature import Signature
from multicall.rpc_call import sync_rpc_eth_call, async_rpc_eth_call
from multicall.constants import CACHE_PATH

COLUMNS = [
    "callId",
    "target",
    "signature",
    "argumentsAsStr",
    "argumentsAsPickle",
    "block",
    "chainId",
    "success",
    "response",
]


class CallRawData:
    # TODO consider some type validation
    def __init__(self, call: Call, block: int, success: bool = None, response: bytes = None) -> None:
        self.call: Call = call
        self.success: bool = success
        self.response: bytes = response
        self.block: int = block
        self.chainID = 1  # Ethereum only
        self.call_id: bytes = self.call.to_id(self.block)

    def to_label_to_output(self) -> dict[str, any]:
        # not certain this will work with all not a contract, and failed to run contract
        return self.call.decode_output(self.response)

    def convert_to_format_to_save_in_cache_db(self):
        record = self.to_record()
        to_save_format = tuple([record[c] for c in COLUMNS])
        return to_save_format

    def to_record(self) -> dict[str:any]:
        return {
            "callId": self.call_id,
            "target": self.call.target,
            "signature": self.call.signature.signature,
            "argumentsAsStr": str(self.call.arguments),
            "argumentsAsPickle": pickle.dumps(self.call.arguments),
            "block": self.block,
            "chainId": self.chainID,
            "success": self.success,
            "response": self.response,
        }

    def __repr__(self):
        return f"CallRawData(callId={self.call.signature!r}, success={self.success}, block={self.block})"


# TODO refactor for clearness
class Multicall:
    def __init__(
        self,
        calls: list[Call],
    ):
        if len(calls) == 0:
            raise ValueError("Must supply more than 0 calls")
        self.calls = calls
        # function tryAggregate(bool requireSuccess, Call[] memory calls) public returns (Result[] memory returnData)
        self.multicall_sig = Signature("tryAggregate(bool,(address,bytes)[])((bool,bytes)[])")
        self.multicall_address = "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696"  # only support Ethereum mainnet

        multicall_args = []

        self._ensure_no_duplicate_names_in_calls(calls)

        for call in self.calls:
            single_call_calldata = call.signature.encode_data(call.arguments)

            multicall_args.append((call.target, single_call_calldata))

        self.calldata = f"0x{self.multicall_sig.encode_data((False, tuple(multicall_args))).hex()}"

    def _ensure_block_keyword_is_not_in_multicall(self, calls: list[Call]):
        for call in calls:
            for label in call.data_labels:
                if label == "block":
                    raise ValueError("Cannot use `block` as a label because it is prohibited")

    def _ensure_no_duplicate_names_in_calls(self, calls: list[Call]):
        found_data_labels = set()

        for call in calls:
            for label in call.data_labels:
                if label in found_data_labels:
                    # TODO: add to unit test
                    raise ValueError(f"duplicate label found {label} is already present")
                else:
                    found_data_labels.add(label)

    def to_rpc_call_args(self, block: int):
        """Convert this multicall into the format required fo for a rpc node api request"""
        rpc_args = [
            {"to": self.multicall_address, "data": self.calldata, "gas": hex(GAS_LIMIT)},
            hex(int(block)),
        ]
        return rpc_args

    def to_call_ids(self, block: int) -> list[str]:
        """Convert all the calls, block ot their call_ids"""
        call_ids = [c.to_id(block) for c in self.calls]
        return call_ids

    def to_list_of_empty_records(self, block: int):
        return list([CallRawData(call, block, None, None).to_record() for call in self.calls])

    def process_raw_bytes_output(self, raw_bytes_output, block):
        decoded_outputs = self.multicall_sig.decode_data(raw_bytes_output)[0]
        # decoded_outputs list[tuple[success, data]]
        call_raw_data = self._decoded_outputs_to_call_raw_data(decoded_outputs, block)
        label_to_output = self._handle_raw_data(call_raw_data)
        label_to_output["block"] = block
        return label_to_output

    def get_all_call_ids(self, block: int) -> list[CallRawData]:
        ids = [call.to_id(block) for call in self.calls]
        return ids

    def _decoded_outputs_to_call_raw_data(self, decoded_outputs, block):
        call_raw_data = []
        for result, call in zip(decoded_outputs, self.calls):
            success, response = result
            call_raw_data.append(CallRawData(call=call, block=block, success=success, response=response))
        return call_raw_data

    def _handle_raw_data(self, call_raw_data: list[CallRawData]) -> dict[str, any]:
        label_to_output = {}
        for data in call_raw_data:
            if data.success is True:
                single_call_label_to_output = data.call.decode_output(data.response)
                label_to_output.update(single_call_label_to_output)
            else:
                for name in data.call.data_labels:
                    label_to_output[name] = CALL_FAILED_REVERT_MESSAGE

        return label_to_output

    ############################### external calls #####################################################3
    async def async_make_each_call_to_raw_call_data(
        self, w3: Web3, block: int, session: aiohttp.ClientSession, rate_limiter: AsyncLimiter
    ):
        rpc_args = self.to_rpc_call_args(block)
        raw_bytes_output = await async_rpc_eth_call(w3, rpc_args, session, rate_limiter)
        decoded_outputs = self.multicall_sig.decode_data(raw_bytes_output)[0]
        call_raw_data_list = self._decoded_outputs_to_call_raw_data(decoded_outputs, block)
        return call_raw_data_list

    def make_external_calls_to_raw_data(self, w3: Web3, block: int) -> list[CallRawData]:
        rpc_args = self.to_rpc_call_args(block)
        raw_bytes_output = sync_rpc_eth_call(w3, rpc_args)
        decoded_outputs = self.multicall_sig.decode_data(raw_bytes_output)[0]
        records = []
        for call, success_bytes_tuple in zip(self.calls, decoded_outputs):
            success, response = success_bytes_tuple
            data = CallRawData(call, block, success, response)
            records.append(data)
        return records

    def __call__(self, w3: Web3, block_id: int | str = "latest", cache="default") -> dict[str, any]:
        cache_path = CACHE_PATH if cache == "default" else cache

        if isinstance(block_id, int):

            from multicall.cache import get_data_from_disk, df_to_CallRawData

            # we have everything already, happy path
            found_df, not_found_df = get_data_from_disk(self.calls, [block_id], cache_path)
            if len(not_found_df) == 0:
                # most happy path we have everything so we can return it
                all_raw_call_data = df_to_CallRawData(found_df, self.calls, [block_id])
                all_label_to_outputs = [data.to_label_to_output() for data in all_raw_call_data]
                label_to_output = dict()
                for l_to_o in all_label_to_outputs:
                    label_to_output.update(l_to_o)
                label_to_output["block"] = block_id
                return label_to_output

            # we don't have at least one call, get everything

            if block_id < w3.eth.get_block("finalized").number:
                # we should finalize this
                from multicall.fetch_multicall_across_blocks import (
                    simple_sequential_fetch_multicalls_across_blocks_and_save,
                )

                simple_sequential_fetch_multicalls_across_blocks_and_save(
                    calls=self.calls, blocks=[block_id], w3=w3, cache_path=cache_path
                )

                found_df, not_found_df = get_data_from_disk(self.calls, [block_id], cache_path)

                if len(not_found_df) == 0:  # maybe add redundnet check for len(found_df) == len(calls)
                    # most happy path we have everything so we can return it
                    all_raw_call_data = df_to_CallRawData(found_df, self.calls, [block_id])
                    all_label_to_outputs = [data.to_label_to_output() for data in all_raw_call_data]
                    label_to_output = dict()
                    for l_to_o in all_label_to_outputs:
                        label_to_output.update(l_to_o)
                    label_to_output["block"] = block_id
                    return label_to_output
                else:
                    raise ValueError("Expected to save data and did not find it in the db")

        # not finalized and should not be
        rpc_args = self.to_rpc_call_args(block_id)
        raw_bytes_output = sync_rpc_eth_call(w3, rpc_args)
        label_to_output = self.process_raw_bytes_output(raw_bytes_output, block_id)
        return label_to_output
