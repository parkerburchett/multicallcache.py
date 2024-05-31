import pytest
from multicall.cache import create_db, delete_db
import os
from multicall.constants import TEST_CACHE_PATH, CACHE_PATH

# create the db if it does not exist, run on import, ugly move to a place that makes more sense
if not os.path.exists(CACHE_PATH):
    create_db(CACHE_PATH)


@pytest.fixture(scope="session", autouse=True)
def setup_session():
    create_db(TEST_CACHE_PATH)
    yield
    delete_db(TEST_CACHE_PATH)
