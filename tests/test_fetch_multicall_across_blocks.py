from multicall.fetch_multicall_across_blocks import fetch_save_and_return
from multicall.constants import W3
from helpers import weth_bal, usdc_bal, invalid_function, target_has_no_code, weth_bal2


def test_fetch_save_and_return():

    calls = [weth_bal, usdc_bal, invalid_function, target_has_no_code]
    blocks = [i for i in range(18_000_000 + 2, 19_000_000, 5_000)]

    print("first go")
    df = fetch_save_and_return([*calls, weth_bal2], blocks, W3, 10)
    print(df.head())

    print("second go")
    df = fetch_save_and_return([*calls, weth_bal2], blocks, W3, 10)

    print(df.head())
