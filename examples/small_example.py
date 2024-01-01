
from decimal import Decimal

from multicall import Call, Multicall
MCD_VAT = '0x35d1b3f3d7966a1dfe207aa4514c12a259a0492b'
from web3 import Web3
from dotenv import load_dotenv

import os

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.environ.get('ALCHEMY_URL')))
def identity(x):
    return x

cbETH = '0xBe9895146f7AF43049ca1c1AE358B0541Ea49704'
cbETH_holder = '0xED1F7bb04D2BA2b6EbE087026F03C96Ea2c357A8'

def identify_function(value):
    return value

call1 = Call(cbETH, 'balanceOf(address)(uint256)', (cbETH_holder), 'balanceOf1', identify_function, w3)
call2 = Call(cbETH, 'balanceOf(address)(uint256)', (cbETH_holder), 'balanceOf2', identify_function, w3)
           

multi = Multicall([call1, call2], w3)
    
a = multi(18_000_000)

print(a)