import pandas as pd
from web3 import Web3

from multicall.call import Call
from multicall.multicall import Multicall, CallRawData


def attempt_identify_function(success: bool, data: any):
    if success is True:
        return data
    else:
        return None


def simple_single_threaded_fetch_multicalls_accross_blocks(
    calls: list[Call], blocks: list[int], w3: Web3
) -> pd.DataFrame:

    # include checks that blocks is a list of ints, all less than eth.latest finalized

    multicall = Multicall(calls)
    raw_data_by_block: list[CallRawData] = []

    for block_id in blocks:
        mulitcall_response = multicall(w3, block_id)
        raw_data_by_block.append(mulitcall_response)
