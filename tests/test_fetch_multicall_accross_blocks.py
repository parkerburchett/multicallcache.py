import os

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

BLOCK_TO_CHECK = 18_000_000
w3 = Web3(Web3.HTTPProvider(os.environ.get("ALCHEMY_URL")))

cbETH = "0xBe9895146f7AF43049ca1c1AE358B0541Ea49704"
