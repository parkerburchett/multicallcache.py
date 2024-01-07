import pandas as pd
from web3 import Web3

from multicall.call import Call
from multicall.multicall import Multicall, CallRawData


def identify_function(x):
    return x


def simple_single_threaded_fetch_multicalls_accross_blocks(
    calls: list[Call], blocks: list[int], w3: Web3
) -> pd.DataFrame:
    
    multicall = Multicall(calls)
    raw_data_by_block: list[CallRawData] = []
    
    for block_id in blocks:
        raw_data = multicall.fetch_raw_data(w3, block_id)
        raw_data_by_block.append(raw_data_by_block)



