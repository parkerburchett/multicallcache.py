"""
test cases
- the rpc node fail because too many calls to fast (rate limiter should mostly prevent this)
- too many calls in a block (100k), timeout, or gas fails

"""


from helpers import w3, weth_bal

from multicall.fetch_multicall_across_blocks import async_fetch_multicalls_across_blocks_and_save


async def make_a_bunch_of_the_same_call_at_many_blocks():
    blocks = [19948055 - i for i in range(100)]
    await async_fetch_multicalls_across_blocks_and_save([weth_bal], blocks, w3, 1, save=False)

