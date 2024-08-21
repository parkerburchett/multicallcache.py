from dotenv import load_dotenv
import os
from web3 import Web3
from helpers import refresh_testing_db, identity_function, TEST_CACHE_PATH
from multicallcache.call import Call


load_dotenv()
base_client = Web3(Web3.HTTPProvider(os.environ.get("BASE_ALCHEMY_URL")))
BASE_TEST_BLOCK = 16_000_000
BASE_WETH = "0x4200000000000000000000000000000000000006"
WETH_HOLDER = "0x628ff693426583D9a7FB391E54366292F509D457"


@refresh_testing_db
def test_base():
    assert base_client.eth.get_block(BASE_TEST_BLOCK).timestamp == 1718789347

    balance_of_call = Call(
        BASE_WETH, "balanceOf(address)(uint256)", (WETH_HOLDER), "balanceOf", identity_function, base_client
    )

    a = balance_of_call(BASE_TEST_BLOCK, TEST_CACHE_PATH)

    assert a == {"balanceOf": 13893954689682401099771}, "balance_of_call failed"
