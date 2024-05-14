from typing import Any, Dict, Iterable, List

import eth_retry
from web3 import Web3

from multicall.constants import Network
import time

chainids: Dict[Web3, int] = {}


def flatten(nested_list: list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten(item))
        else:
            flat_list.append(item)
    return flat_list


def chunks(lst: List, n: int):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


@eth_retry.auto_retry
#TODO, this should be hardcoded and updated with PRs
def chain_id(w3: Web3) -> int:
    """
    Returns chain id for an instance of Web3. Helps save repeat calls to node.
    """
    try:
        return chainids[w3]
    except KeyError:
        chainids[w3] = w3.eth.chain_id
        return chainids[w3]


def get_endpoint(w3: Web3) -> str:
    provider = w3.provider
    if isinstance(provider, str):
        return provider
    if hasattr(provider, "_active_provider"):
        provider = provider._get_active_provider(False)
    return provider.endpoint_uri


def raise_if_exception(obj: Any) -> None:
    if isinstance(obj, Exception):
        raise obj


def raise_if_exception_in(iterable: Iterable[Any]) -> None:
    for obj in iterable:
        raise_if_exception(obj)


def state_override_supported(w3: Web3) -> bool:
    if chain_id(w3) in [Network.Gnosis]:
        return False
    return True


def time_function(func):
    """
    Decorator that measures and prints the execution time of a non-async function.
    """

    def wrapper(*args, **kwargs):
        start_time = time.time()  # Record the start time of the function
        result = func(*args, **kwargs)  # Call the function with the provided arguments
        end_time = time.time()  # Record the end time of the function
        print(f"{func.__name__} executed in {end_time - start_time:.6f} seconds.")
        return result  # Return the result of the function

    return wrapper
