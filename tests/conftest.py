import pytest
from pathlib import Path
from multicall.cache import create_db, delete_db


TEST_CACHE_PATH = Path(__file__).parent / "test_cache_db.sqlite"


@pytest.fixture(scope="session", autouse=True)
def setup_session():
    create_db(TEST_CACHE_PATH)
    CACHE_PATH = TEST_CACHE_PATH # idk if this works
    yield
    delete_db(TEST_CACHE_PATH)
