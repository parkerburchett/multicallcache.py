import os

from dotenv import load_dotenv
import pytest
from web3 import Web3
import web3
import multicall
from multicall.call import Call
from multicall.signature import SignatureFailedToEncodeData

# TODO: get black to work
# $ poetry run pytest tests/mine/

load_dotenv()

BLOCK_TO_CHECK = 18_000_000
w3 = Web3(Web3.HTTPProvider(os.environ.get('ALCHEMY_URL')))

cbETH = '0xBe9895146f7AF43049ca1c1AE358B0541Ea49704'
cbETH_holder = '0xED1F7bb04D2BA2b6EbE087026F03C96Ea2c357A8'

def identify_function(value):
    return value


def test_single_return_value():
    balance_of_call =  Call(cbETH, 'balanceOf(address)(uint256)', (cbETH_holder), 'balanceOf', identify_function, w3)
    assert balance_of_call(BLOCK_TO_CHECK) == {'balanceOf': 32431674561658258136000}, "balance_of_call failed"

    name_call = Call(cbETH, 'name()(string)', (), 'name', identify_function, w3)
    assert name_call() == {'name': 'Coinbase Wrapped Staked ETH'}, "name_call failed"

    total_supply_call = Call(cbETH, 'totalSupply()(uint256)', (), 'totalSupply', identify_function, w3)
    assert total_supply_call(BLOCK_TO_CHECK) == {'totalSupply': 1224558113282286488129522}, "total_supply_call failed"


def test_multiple_return_values():
    BALANCER_VAULT = '0xBA12222222228d8Ba445958a75a0704d566BF2C8'

    vault_get_paused_state = Call(BALANCER_VAULT, 'getPausedState()(bool,uint256,uint256)', (),
                                  ('paused', 'pauseWindowEndTime', 'bufferPeriodEndTime'),
                                  (identify_function, identify_function, identify_function), w3)
    expected = {'paused': False, 'pauseWindowEndTime': 1626633407, 'bufferPeriodEndTime': 1629225407}
    assert vault_get_paused_state(BLOCK_TO_CHECK) == expected, "vault_get_paused_state failed"

    pool_id = bytes.fromhex("1e19cf2d73a72ef1332c882f20534b6519be0276000200000000000000000112")
    vault_get_pool_tokens = Call(BALANCER_VAULT, 'getPoolTokens(bytes32)(address[],uint256[],uint256)',
                                     pool_id,
                                     ('tokens', 'balances', 'lastChangeBlock'),
                                      (identify_function, identify_function, identify_function), w3)

    expected = {'tokens': ('0xae78736cd615f374d3085123a210448e74fc6393', '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'),
                'balances': (10218807022150565266010, 12892757262517014259928), 'lastChangeBlock': 17999794}
    assert vault_get_pool_tokens(BLOCK_TO_CHECK) == expected, "vault_get_pool_tokens failed"


def test_malformed_calls():
    bad_function_signature_call = Call(cbETH, 'thisFunctionDoesNotExist()(uint256)', (), '', identify_function, w3)
    with pytest.raises(web3.exceptions.ContractLogicError):
        bad_function_signature_call()
    
    # I am stuck here. I can't figure out the import errors and catching the custom error
    # TODO: make sure this catches the correct exception
    with pytest.raises(Exception) as e:
        too_many_args_call = Call(cbETH, 'totalSupply()(uint256)', (cbETH), 'totalSupply', identify_function, w3)
        too_many_args_call()

    with pytest.raises(Exception) as e:
        too_few_args_call = Call(cbETH, 'balanceOf(address)(uint256)', (), 'balanceOf', identify_function, w3)
        too_few_args_call()

test_malformed_calls()