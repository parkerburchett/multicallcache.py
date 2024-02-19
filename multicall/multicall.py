from web3 import Web3
import aiohttp
from aiolimiter import AsyncLimiter


from multicall.call import Call, GAS_LIMIT, CALL_FAILED_REVERT_MESSAGE
from multicall.signature import Signature
from multicall.rpc_call import sync_rpc_eth_call, async_rpc_eth_call


class CallRawData:
    def __init__(self, call: Call, success: bool, response_bytes: bytes, block: int) -> None:
        self.call = call
        self.success = success
        self.response_bytes = response_bytes
        self.block = block


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

        if not isinstance(block, int):
            raise ValueError("block must be an int", type(block), block)
        rpc_args = [
            {"to": self.multicall_address, "data": self.calldata, "gas": hex(GAS_LIMIT)},
            hex(block),
        ]
        return rpc_args
    

    def call_using_web3_py(self, w3: Web3, block: int) -> list[CallRawData]:
        rpc_args = self.to_rpc_call_args(block)
        raw_bytes_output = w3.eth.call(*rpc_args)
        label_to_output = self.process_raw_bytes_output(raw_bytes_output, block)
        return label_to_output


    def __call__(self, w3: Web3, block: int) -> list[CallRawData]:
        rpc_args = self.to_rpc_call_args(block)
        raw_bytes_output = sync_rpc_eth_call(w3, rpc_args)
        label_to_output = self.process_raw_bytes_output(raw_bytes_output, block)
        return label_to_output

    async def async_call(self, w3: Web3, block: int, session: aiohttp.ClientSession, rate_limiter: AsyncLimiter):
        rpc_args = self.to_rpc_call_args(block)
        raw_bytes_output = await async_rpc_eth_call(w3, rpc_args, session, rate_limiter)
        label_to_output = self.process_raw_bytes_output(raw_bytes_output, block)
        return label_to_output

    def process_raw_bytes_output(self, raw_bytes_output, block):
        decoded_outputs = self.multicall_sig.decode_data(raw_bytes_output)[0]
        call_raw_data = self._decoded_outputs_to_call_raw_data(decoded_outputs, block)
        label_to_output = self._handle_raw_data(call_raw_data)
        label_to_output["block"] = block
        return label_to_output

    def _decoded_outputs_to_call_raw_data(self, decoded_outputs, block):
        call_raw_data = []
        for result, call in zip(decoded_outputs, self.calls):
            success, single_function_return_data_bytes = result
            call_raw_data.append(CallRawData(call, success, single_function_return_data_bytes, block))
        return call_raw_data

    def _handle_raw_data(self, call_raw_data: list[CallRawData]) -> dict[str, any]:
        label_to_output = {}
        for data in call_raw_data:
            if data.success is True:
                single_call_label_to_output = data.call.decode_output(data.response_bytes)
                label_to_output.update(single_call_label_to_output)
            else:
                for name in data.call.data_labels:
                    label_to_output[name] = CALL_FAILED_REVERT_MESSAGE

        return label_to_output
