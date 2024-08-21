import pytest
import web3
from multicallcache.call import Call, NOT_A_CONTRACT_REVERT_MESSAGE
from multicallcache.constants import TEST_CACHE_PATH, W3
from helpers import refresh_testing_db, TEST_BLOCK


cbETH = "0xBe9895146f7AF43049ca1c1AE358B0541Ea49704"
cbETH_holder = "0xED1F7bb04D2BA2b6EbE087026F03C96Ea2c357A8"


def identity_function(value):
    return value


@refresh_testing_db
def test_single_return_value():
    balance_of_call = Call(cbETH, "balanceOf(address)(uint256)", (cbETH_holder), "balanceOf", identity_function, W3)
    assert balance_of_call(TEST_BLOCK, TEST_CACHE_PATH) == {
        "balanceOf": 32431674561658258136000
    }, "balance_of_call failed"

    name_call = Call(cbETH, "name()(string)", (), "name", identity_function, W3)
    assert name_call(TEST_BLOCK, TEST_CACHE_PATH) == {"name": "Coinbase Wrapped Staked ETH"}, "name_call failed"

    total_supply_call = Call(cbETH, "totalSupply()(uint256)", (), "totalSupply", identity_function, W3)
    assert total_supply_call(TEST_BLOCK, TEST_CACHE_PATH) == {
        "totalSupply": 1224558113282286488129522
    }, "total_supply_call failed"


@refresh_testing_db
def test_multiple_return_values():
    BALANCER_VAULT = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"

    vault_get_paused_state = Call(
        BALANCER_VAULT,
        "getPausedState()(bool,uint256,uint256)",
        (),
        ("paused", "pauseWindowEndTime", "bufferPeriodEndTime"),
        (identity_function, identity_function, identity_function),
        W3,
    )
    expected = {
        "paused": False,
        "pauseWindowEndTime": 1626633407,
        "bufferPeriodEndTime": 1629225407,
    }
    assert vault_get_paused_state(TEST_BLOCK, TEST_CACHE_PATH) == expected, "vault_get_paused_state failed"

    pool_id = bytes.fromhex("1e19cf2d73a72ef1332c882f20534b6519be0276000200000000000000000112")
    vault_get_pool_tokens = Call(
        BALANCER_VAULT,
        "getPoolTokens(bytes32)(address[],uint256[],uint256)",
        pool_id,
        ("tokens", "balances", "lastChangeBlock"),
        (identity_function, identity_function, identity_function),
        W3,
    )

    expected = {
        "tokens": (
            "0xae78736cd615f374d3085123a210448e74fc6393",
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        ),
        "balances": (10218807022150565266010, 12892757262517014259928),
        "lastChangeBlock": 17999794,
    }
    assert vault_get_pool_tokens(TEST_BLOCK, TEST_CACHE_PATH) == expected, "vault_get_pool_tokens failed"


@refresh_testing_db
def test_non_existent_function_call():
    bad_function_signature_call = Call(
        cbETH, "thisFunctionDoesNotExist()(uint256)", (), "thisFunctionDoesNotExist", identity_function, W3
    )

    with pytest.raises(web3.exceptions.ContractLogicError):
        # we only know that thisFunctionDoesNotExist() doesn't exist when we try to call it.
        # so it is constructed properly, but reverts when called
        bad_function_signature_call(TEST_BLOCK, TEST_CACHE_PATH)


@refresh_testing_db
def test_call_to_an_address_without_code():
    address_without_code = "0x0000000000000000000000000000000000000000"

    call_to_address_without_code = Call(
        address_without_code,
        "thisFunctionDoesNotExist()(uint256)",
        (),
        "thisFunctionDoesNotExist",
        identity_function,
        W3,
    )
    assert call_to_address_without_code(TEST_BLOCK, TEST_CACHE_PATH) == {
        "thisFunctionDoesNotExist": NOT_A_CONTRACT_REVERT_MESSAGE
    }, "failed Call to address without code"


def test_malformed_calls():
    # I am stuck here. I can't figure out the import errors and catching the custom error
    # TODO: make sure this catches the correct exception
    with pytest.raises(Exception):
        Call(cbETH, "totalSupply()(uint256)", (cbETH), "totalSupply", identity_function, W3)

    with pytest.raises(Exception):
        Call(cbETH, "balanceOf(address)(uint256)", (), "balanceOf", identity_function, W3)

    with pytest.raises(Exception):
        Call(cbETH, "balanceOf(address)(uint256)", (int(100)), "balanceOf", identity_function, W3)
