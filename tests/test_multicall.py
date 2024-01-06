import os

from dotenv import load_dotenv
import pytest
from web3 import Web3
import web3
from multicall.multicall import Multicall
from multicall.call import Call

load_dotenv()

cbETH = "0xBe9895146f7AF43049ca1c1AE358B0541Ea49704"
cbETH_holder = "0xED1F7bb04D2BA2b6EbE087026F03C96Ea2c357A8"

BLOCK_TO_CHECK = 18_000_000
w3 = Web3(Web3.HTTPProvider(os.environ.get("ALCHEMY_URL")))


def identify_function(value):
    return value


def test_multicall():
    balance_of_call = Call(
        cbETH,
        "balanceOf(address)(uint256)",
        (cbETH_holder),
        "balanceOf",
        identify_function,
        w3,
    )
    name_call = Call(cbETH, "name()(string)", (), "name", identify_function, w3)
    total_supply_call = Call(cbETH, "totalSupply()(uint256)", (), "totalSupply", identify_function, w3)
    multicall = Multicall([balance_of_call, name_call, total_supply_call], w3)

    expected_data = {
        "balanceOf": 32431674561658258136000,
        "name": "Coinbase Wrapped Staked ETH",
        "totalSupply": 1224558113282286488129522,
    }

    assert multicall(BLOCK_TO_CHECK) == expected_data, "Multicall, multiple calls, each returning a single value failed"

    print("success!")

    # assert balance_of_call(BLOCK_TO_CHECK) == {'balanceOf': 32431674561658258136000}, "balance_of_call failed"


test_multicall_single_call()
