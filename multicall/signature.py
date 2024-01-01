from typing import Any, List, Optional, Tuple
import eth_abi
# from eth_abi import decode_single, encode_single
# from eth_abi.exceptions import ValueOutOfBounds
from eth_typing.abi import Decodable
from eth_utils import function_signature_to_4byte_selector

import warnings

# TODO: switch to using from eth_abi.abi import encode, decode


class SignatureFailedToEncodeData(Exception):
    def __init__(self, message):
        super().__init__(message=message)


def parse_signature(signature: str) -> Tuple[str, str, str]:
    """
    Breaks 'func(address)(uint256)' into ['func', '(address)', '(uint256)']
    """
    parts: List[str] = []
    stack: List[str] = []
    start: int = 0
    for end, letter in enumerate(signature):
        if letter == "(":
            stack.append(letter)
            if not parts:
                parts.append(signature[start:end])
                start = end
        if letter == ")":
            stack.pop()
            if not stack:  # we are only interested in outermost groups
                parts.append(signature[start : end + 1])
                start = end + 1
    function = "".join(parts[:2])
    input_types = parts[1]
    output_types = parts[2]

    return function, input_types, output_types


class Signature:
    def __init__(self, signature: str) -> None:
        self.signature = signature
        self.function, self.input_types, self.output_types = parse_signature(signature)
        self.fourbyte = function_signature_to_4byte_selector(self.function)

    def encode_data(self, args: Optional[Any] = None) -> bytes:
        try:
            with warnings.catch_warnings():
                # print(f'{self.input_types=}')
                # print(f'{args=}')
                warnings.filterwarnings("ignore", category=DeprecationWarning, module="eth_abi.codec")

                if args is not None:
                    args_encoded_with_types =  eth_abi.encode_single(self.input_types, args)
                    return self.fourbyte + args_encoded_with_types
                else:
                    return self.fourbyte
        except Exception as e:
            # place holder
            print(type(e), e)
            raise Exception('Signature.encode data failed')
        # except eth_abi.exceptionsValueOutOfBounds as e:
        #     raise SignatureFailedToEncodeData()


    def decode_data(self, output: Decodable) -> Any:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning, module="eth_abi.codec")      
            decoded_output = eth_abi.decode_single(self.output_types, output)
            return decoded_output
    
    def to_cache_id(self):
        pass
