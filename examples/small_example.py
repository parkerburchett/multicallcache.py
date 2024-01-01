
from decimal import Decimal

from multicall import Call, Multicall
MCD_VAT = '0x35d1b3f3d7966a1dfe207aa4514c12a259a0492b'
from web3 import Web3


def identity(x):
    return x

cbETH = '0xBe9895146f7AF43049ca1c1AE358B0541Ea49704'
cbETH_holder = '0xED1F7bb04D2BA2b6EbE087026F03C96Ea2c357A8'

def identify_function(value):
    return value

call = Call(cbETH, 'balanceOf(address)(uint256)', (cbETH_holder),
            'balanceOf', identify_function, w3)

# print(call(18_000_000))

multi = Multicall([call], w3) # multicall.encode data fails here
    
a = multi(18_000_000)

print(a)