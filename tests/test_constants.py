import os
from dotenv import load_dotenv
from web3 import Web3
from multicall.call import Call
from pathlib import Path

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.environ.get("ALCHEMY_URL")))
test_data_path = Path(__file__).parent / "test_data"

uniswap_v3_usdc_weth_pool = "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"
weth = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
usdc = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


def identity_function(data: any) -> any:
    return data


weth_bal = Call(
    weth,
    "balanceOf(address)(uint256)",
    (uniswap_v3_usdc_weth_pool),
    "weth_bal",
    identity_function,
)

usdc_bal = Call(
    usdc,
    "balanceOf(address)(uint256)",
    (uniswap_v3_usdc_weth_pool),
    "usdc_bal",
    identity_function,
)

invalid_function = Call(
    usdc,
    "functionDoesNotExist()(uint256)",
    (),
    "functionDoesNotExist",
    identity_function,
)

target_has_no_code = Call(
    "0x0000000000000000000000000000000000000000",
    "functionDoesNotExist()(uint256)",
    (),
    "notAContract",
    identity_function,
)
