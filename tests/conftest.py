import pytest
from pathlib import Path
from multicall.cache import create_db, delete_db


TEST_CACHE_PATH = Path(__file__).parent / "test_cache_db.sqlite"


@pytest.fixture(scope="session", autouse=True)
def setup_session():
    create_db(TEST_CACHE_PATH)
    # I want to overwrite the CACHE_PATH variable for the whole package  while in testing,
    # how do I do that?
    yield
    delete_db(TEST_CACHE_PATH)
