import pandas as pd
import pytest

from multicall.fetch_multicall_across_blocks import fetch_save_and_return

from helpers import w3, weth_bal, usdc_bal, invalid_function, target_has_no_code, test_data_path, weth_bal2


def test_fetch_save_and_return():

    calls = [weth_bal, usdc_bal, invalid_function, target_has_no_code]
    blocks = [i for i in range(18_000_000 + 2, 19_000_000, 5_000)]

    print("first go")
    df = fetch_save_and_return([*calls, weth_bal2], blocks, w3, 10)

    print("second go")
    df = fetch_save_and_return([*calls, weth_bal2], blocks, w3, 10)

    pass
