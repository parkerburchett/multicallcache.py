import pandas as pd
from web3 import Web3

from multicall.call import Call
from multicall.multicall import Multicall



def simple_sequential_fetch_multicalls_across_blocks(
    calls: list[Call], blocks: list[int], w3: Web3
) -> pd.DataFrame:
    
    multicall = Multicall(calls)
    responses = []
    for block_id in blocks:
        mulitcall_response: dict[str, any] = multicall(w3, block_id)
        mulitcall_response['block'] = block_id
        responses.append(mulitcall_response)

    df = pd.DataFrame.from_records(responses)
    return df


