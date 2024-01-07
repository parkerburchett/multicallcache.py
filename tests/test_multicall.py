import os

from dotenv import load_dotenv
from web3 import Web3
from multicall.multicall import Multicall
from multicall.call import Call, CALL_FAILED_REVERT_MESSAGE, NOT_A_CONTRACT_REVERT_MESSAGE

# TODO: not sure how many methods to split the tests into

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
    )
    name_call = Call(
        cbETH,
        "name()(string)",
        (),
        "name",
        identify_function,
    )
    total_supply_call = Call(
        cbETH,
        "totalSupply()(uint256)",
        (),
        "totalSupply",
        identify_function,
    )
    multicall_single_return_values = Multicall(
        [balance_of_call, name_call, total_supply_call],
    )

    single_return_values_expected_data = {
        "balanceOf": 32431674561658258136000,
        "name": "Coinbase Wrapped Staked ETH",
        "totalSupply": 1224558113282286488129522,
    }

    assert (
        multicall_single_return_values(w3, BLOCK_TO_CHECK) == single_return_values_expected_data
    ), "Multicall, multiple calls, each returning a single value failed"

    ################################# Functions that return multiple values #################################

    BALANCER_VAULT = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
    pool_id = bytes.fromhex("1e19cf2d73a72ef1332c882f20534b6519be0276000200000000000000000112")

    vault_get_paused_state_call = Call(
        BALANCER_VAULT,
        "getPausedState()(bool,uint256,uint256)",
        (),
        ("paused", "pauseWindowEndTime", "bufferPeriodEndTime"),
        (identify_function, identify_function, identify_function),
    )

    vault_get_pool_tokens_call = Call(
        BALANCER_VAULT,
        "getPoolTokens(bytes32)(address[],uint256[],uint256)",
        pool_id,
        ("tokens", "balances", "lastChangeBlock"),
        (identify_function, identify_function, identify_function),
    )

    many_return_values_expected_data = {
        "paused": False,
        "pauseWindowEndTime": 1626633407,
        "bufferPeriodEndTime": 1629225407,
        "tokens": (
            "0xae78736cd615f374d3085123a210448e74fc6393",
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        ),
        "balances": (10218807022150565266010, 12892757262517014259928),
        "lastChangeBlock": 17999794,
    }

    multicall_with_many_return_values = Multicall([vault_get_paused_state_call, vault_get_pool_tokens_call])

    assert (
        multicall_with_many_return_values(w3, BLOCK_TO_CHECK) == many_return_values_expected_data
    ), "multicall_many_return_values failed"

    multicall_with_single_and_multiple = Multicall(
        [vault_get_paused_state_call, vault_get_pool_tokens_call, balance_of_call, name_call, total_supply_call]
    )

    expected_values_combination = {**many_return_values_expected_data, **single_return_values_expected_data}

    assert (
        multicall_with_single_and_multiple(w3, BLOCK_TO_CHECK) == expected_values_combination
    ), "multicall_with_single_and_multiple failed"

    ################################# Functions that don't exist #################################
    bad_function_signature_call = Call(
        cbETH,
        "thisFunctionDoesNotExist()(uint256)",
        (),
        "thisFunctionDoesNotExist",
        identify_function,
    )

    multicall_with_bad_function_signature_call = Multicall(
        [
            vault_get_paused_state_call,
            vault_get_pool_tokens_call,
            balance_of_call,
            name_call,
            total_supply_call,
            bad_function_signature_call,
        ],
    )

    expected_values_combination["thisFunctionDoesNotExist"] = CALL_FAILED_REVERT_MESSAGE

    assert (
        multicall_with_bad_function_signature_call(w3, BLOCK_TO_CHECK) == expected_values_combination
    ), "multicall_single_and_multiple failed"

    address_without_code = "0x0000000000000000000000000000000000000000"

    call_to_address_without_code = Call(
        address_without_code,
        "thisFunctionDoesNotExist()(uint256)",
        (),
        "AddressWithoutCode",
        identify_function,
    )

    multicall_with_call_to_address_without_code = Multicall(
        [
            vault_get_paused_state_call,
            vault_get_pool_tokens_call,
            balance_of_call,
            name_call,
            total_supply_call,
            bad_function_signature_call,
            call_to_address_without_code,
        ]
    )

    expected_values_combination["AddressWithoutCode"] = NOT_A_CONTRACT_REVERT_MESSAGE

    assert (
        multicall_with_call_to_address_without_code(w3, BLOCK_TO_CHECK) == expected_values_combination
    ), "multicall_with_call_to_address_without_code failed"


test_multicall()
