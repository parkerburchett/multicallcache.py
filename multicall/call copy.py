from typing import Any, Callable, Iterable, List, Optional, Tuple, Union

import eth_retry
from eth_typing import Address, ChecksumAddress, HexAddress
from eth_typing.abi import Decodable
from eth_utils import to_checksum_address
from web3 import Web3

from multicall import Signature
from multicall.loggers import setup_logger


logger = setup_logger(__name__)

AnyAddress = Union[str, Address, ChecksumAddress, HexAddress]


class Call:
    def __init__(
        self,
        target: AnyAddress,
        function: Union[
            str, Iterable[Union[str, Any]]
        ],  # 'funcName(dtype)(dtype)' or ['funcName(dtype)(dtype)', input0, input1, ...]
        returns: Optional[Iterable[Tuple[str, Callable]]] = None,
        block_id: Optional[int] = None,
        gas_limit: Optional[int] = None,
        _w3: Optional[Web3] = None,
    ) -> None:
        self.target = to_checksum_address(target)
        self.returns = returns
        self.block_id = block_id
        self.gas_limit = gas_limit
        self.w3 = _w3

        self.args: Optional[List[Any]]
        if isinstance(function, list):
            self.function, *self.args = function
        else:
            self.function = function
            self.args = None

        self.signature = Signature(self.function)

    def __repr__(self) -> str:
        return f"Call {self.target}.{self.function}"

    @property
    def data(self) -> bytes:
        return self.signature.encode_data(self.args)

    @staticmethod
    def decode_output(
        output: Decodable,
        signature: Signature,
        returns: Optional[Iterable[Tuple[str, Callable]]] = None,
        success: Optional[bool] = None,
    ) -> Any:

        if success is None:

            def apply_handler(handler, value):
                return handler(value)

        else:

            def apply_handler(handler, value):
                return handler(success, value)

        if success is None or success:
            try:
                decoded = signature.decode_data(output)
            except:
                success, decoded = False, [None] * (1 if not returns else len(returns))  # type: ignore
        else:
            decoded = [None] * (1 if not returns else len(returns))  # type: ignore

        logger.debug(f"returns: {returns}")
        logger.debug(f"decoded: {decoded}")

        if returns:
            return {
                name: apply_handler(handler, value) if handler else value
                for (name, handler), value in zip(returns, decoded)
            }
        else:
            return decoded if len(decoded) > 1 else decoded[0]

    @eth_retry.auto_retry
    def __call__(self, args: Optional[Any] = None) -> Any:
        if self.w3 is None:
            raise RuntimeError
        args = Call.prep_args(
            self.target,
            self.signature,
            args or self.args,
            self.block_id,
            self.gas_limit,
        )
        return Call.decode_output(
            self.w3.eth.call(*args),
            self.signature,
            self.returns,
        )

    @staticmethod
    def prep_args(
        target: str,
        signature: Signature,
        args: Optional[Any],
        block_id: Optional[int],
        gas_limit: int,
    ) -> List:

        calldata = signature.encode_data(args)
        args = [{"to": target, "data": calldata}, hex(block_id)]

        if gas_limit:
            args[0]["gas"] = gas_limit

        return args
