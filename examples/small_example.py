
from multicall import Call, Multicall
from web3 import Web3
from dotenv import load_dotenv
from datetime import datetime
import os
load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.environ.get('ALCHEMY_URL')))
def identity(x):
    return x

cbETH = '0xBe9895146f7AF43049ca1c1AE358B0541Ea49704'
cbETH_holder = '0xED1F7bb04D2BA2b6EbE087026F03C96Ea2c357A8'

def toETH(value):
    return value / 1e18

def main():
    import pandas as pd
    weth = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    to_addresses = pd.read_csv('many_weth_transfers.csv').head(5000)['from']
    # 10k adresses fails
    # requests.exceptions.HTTPError: 413 Client Error: Payload Too Large for url: https://eth-mainnet.g.alchemy.com/v2/


    calls = [Call(weth, 'balanceOf(address)(uint256)', (a), f'{a}_weth_bal', toETH, w3)
            for a in to_addresses]
    before_building_multicall = datetime.now()
    multi = Multicall(calls, w3) 
    print(datetime.now() - before_building_multicall, 'time taken to construct multicall object (calldata encoding dominating cost)')
    before_making_request = datetime.now()
    a = multi(18_000_000)


    # add hashing to the call object. 
    print(datetime.now() - before_making_request, 'fetch time', len(calls))
    print(len(a))

    # that

if __name__ == '__main__':
    main()
