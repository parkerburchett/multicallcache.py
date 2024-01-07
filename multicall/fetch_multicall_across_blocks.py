import pandas as pd
from web3 import Web3

from multicall.call import Call
from multicall.multicall import Multicall


def identify_function(x):
    return x


def simple_single_threaded_fetch_multicalls_accross_blocks(
    calls: list[Call], blocks: list[int], w3: Web3
) -> pd.DataFrame:

    df = pd.DataFrame.from_records([Multicall(calls)(w3, block) for block in blocks])
    return df
