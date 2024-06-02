# import pytest
# from multicall.cache import create_db, delete_db
# import os
# from multicall.constants import TEST_CACHE_PATH, CACHE_PATH

# # @pytest.fixture(scope="session", autouse=True)
# # def setup_session():
# #     create_db(TEST_CACHE_PATH)
# #     yield
# #     delete_db(TEST_CACHE_PATH)

# def preTest():
#     create_db(TEST_CACHE_PATH)

# def postTest():
#     delete_db(TEST_CACHE_PATH)

# def with_pre_and_post_tests(func):
#     # TODO, makes a fresh db between tests
#     def wrapper(*args, **kwargs):
#         # Run pre-test
#         preTest()
#         try:
#             # Execute the function
#             result = func(*args, **kwargs)
#             return result
#         finally:
#             # Run post-test
#             postTest()
#     return wrapper
