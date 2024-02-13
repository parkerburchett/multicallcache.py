from web3 import Web3


from multicall.call import Call, GAS_LIMIT, CALL_FAILED_REVERT_MESSAGE
from multicall.signature import Signature


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
        # todo include checks that each processing function starts with a bool success
        # include check that "block" keyword is reserved
        if len(calls) == 0:
            raise ValueError("Must supply more than 0 calls")
        self.calls = calls
        # what multicall function we are using
        # function tryAggregate(bool requireSuccess, Call[] memory calls) public returns (Result[] memory returnData)
        self.multicall_sig = Signature("tryAggregate(bool,(address,bytes)[])((bool,bytes)[])")
        self.multicall_address = "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696"  # only support Ethereum mainnet

        multicall_args = []

        self._ensure_no_duplicate_names_in_calls(calls)

        for call in self.calls:
            single_call_calldata = call.signature.encode_data(call.arguments)

            multicall_args.append((call.target, single_call_calldata))

        self.calldata = f"0x{self.multicall_sig.encode_data((False, tuple(multicall_args))).hex()}"

    def _ensure_no_duplicate_names_in_calls(self, calls: list[Call]):
        found_data_labels = set()

        for call in calls:
            for label in call.data_labels:
                if label in found_data_labels:
                    # TODO: add to unit test
                    raise ValueError(f"duplicate label found {label} is already present")
                else:
                    found_data_labels.add(label)

    def to_rpc_call_args(self, block_id: int | None):
        """Convert this multicall into the format required fo for a rpc node api request"""
        block_id_for_rpc_call = hex(block_id) if isinstance(block_id, int) else "latest"
        args = [
            {"to": self.multicall_address, "data": self.calldata, "gas": GAS_LIMIT},
            block_id_for_rpc_call,
        ]
        return args

    def __call__(self, w3: Web3, block_id: int | str = "latest") -> dict[str, any]:
        call_raw_data: list[CallRawData] = self._fetch_raw_data(w3, block_id)
        label_to_output: dict[str, any] = self._handle_raw_data(call_raw_data)
        return label_to_output

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

    def _fetch_raw_data(self, w3: Web3, block_id: int) -> list[CallRawData]:
        rpc_args = self.to_rpc_call_args(block_id)
        raw_bytes_output = w3.eth.call(*rpc_args)
        decoded_outputs = self.multicall_sig.decode_data(raw_bytes_output)[0]
        call_raw_data = []
        for result, call in zip(decoded_outputs, self.calls):
            success, single_function_return_data_bytes = result
            # decide on if using latest. If latest then don't save it
            call_raw_data.append(CallRawData(call, success, single_function_return_data_bytes, block_id))
        return call_raw_data
