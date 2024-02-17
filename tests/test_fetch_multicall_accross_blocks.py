import asyncio
import os


from dotenv import load_dotenv
from web3 import Web3
from multicall.call import Call
from multicall.fetch_multicall_across_blocks import (
    simple_sequential_fetch_multicalls_across_blocks,
    simple_async_fetch_multicalls_across_blocks,
)

from pathlib import Path
import pandas as pd

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

calls = [weth_bal, usdc_bal, invalid_function, target_has_no_code]
blocks = [18_000_000, 18_001_000]


def simple_sequential_tests():
    found_df = simple_sequential_fetch_multicalls_across_blocks(calls, blocks, w3)
    # TODO: don't have a cast to string issue

    found_df["weth_bal"] = found_df["weth_bal"].apply(str)
    found_df["usdc_bal"] = found_df["usdc_bal"].apply(str)

    found_df.to_csv(test_data_path / "simple_sequential_test_data.csv", index=False)
    expected_df = pd.read_csv(test_data_path / "simple_sequential_test_data.csv")

    expected_df["weth_bal"] = expected_df["weth_bal"].apply(str)
    expected_df["usdc_bal"] = expected_df["usdc_bal"].apply(str)

    assert expected_df.equals(found_df), "expected_df for sequential call does not match found_df"


def simple_async_test():
    found_df = asyncio.run(simple_async_fetch_multicalls_across_blocks(calls, blocks, w3))

    pass


if __name__ == "__main__":
    simple_async_test()
