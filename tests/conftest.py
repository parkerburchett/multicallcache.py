import pytest
from multicall.cache import create_db, delete_db
import os
from multicall.constants import TEST_CACHE_PATH, CACHE_PATH


def setup_session():
    create_db(TEST_CACHE_PATH)
    print(f"Created {TEST_CACHE_PATH=}")
    yield

    delete_db(TEST_CACHE_PATH)
    print(f"removed {TEST_CACHE_PATH=}") # TODO not printing during tests
