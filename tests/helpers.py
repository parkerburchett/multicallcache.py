from multicall.call import Call
from pathlib import Path

test_data_path = Path(__file__).parent / "test_data"

uniswap_v3_usdc_weth_pool = "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"
weth = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
usdc = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


def to_str(data: any) -> str:
    return str(data)


weth_bal = Call(
    weth,
    "balanceOf(address)(uint256)",
    (uniswap_v3_usdc_weth_pool),
    "weth_bal",
    to_str,
)

weth_bal2 = Call(
    weth,
    "balanceOf(address)(uint256)",
    ("0x95222290DD7278Aa3Ddd389Cc1E1d165CC4BAfe5"),
    "weth_bal2",
    to_str,
)


usdc_bal = Call(
    usdc,
    "balanceOf(address)(uint256)",
    (uniswap_v3_usdc_weth_pool),
    "usdc_bal",
    to_str,
)

invalid_function = Call(
    usdc,
    "functionDoesNotExist()(uint256)",
    (),
    "functionDoesNotExist",
    to_str,
)

target_has_no_code = Call(
    "0x0000000000000000000000000000000000000000",
    "functionDoesNotExist()(uint256)",
    (),
    "notAContract",
    to_str,
)
