print('hello test_multicall.py')

import json
import gzip
from multicall import Call, Multicall
import os

import pytest
from web3 import Web3
from web3.providers import HTTPProvider

from .settings import CONFIG


MULTICALLS_DIR = os.path.join(os.path.dirname(__file__), "data")

# "multicall2.json.gz", is testing chain id=250 aka Fantom Opera. Skipping since I don't care about it

MULTICALL_FILES = ["multicall1.json.gz", "multicall3.json.gz"]


@pytest.mark.parametrize("fname", MULTICALL_FILES)
def test_multicall(fname):
    with gzip.open(os.path.join(MULTICALLS_DIR, fname), "r") as fl:
        data = json.load(fl)

        calls, network, require_success, parallel_threshold = (
            data["calls"],
            data["network"],
            data.get("require_success", False),
            data.get("parallel_threshold", 1),
        )

        network_uri = CONFIG["networks"][str(network)]

        multi = Multicall(
            list(map(lambda c: Call(*c["call"]), calls)),
            _w3=Web3(HTTPProvider(network_uri)),
            require_success=require_success,
            parallel_threshold=parallel_threshold,
        )

        results = multi()

        assert len(results) == len(calls), "Not all calls were executed"

        for call in calls:

            _, _, ((name, _),) = call["call"]

            assert (
                results[name] == call["expected"]
            ), f"Result {results[name]} is not equal to expected {call['expected']}"
