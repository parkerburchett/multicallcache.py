from dataclasses import dataclass

from typing import Dict
from dotenv import load_dotenv
from web3 import Web3
from pathlib import Path

import os

load_dotenv()
W3 = Web3(Web3.HTTPProvider(os.environ.get("ALCHEMY_URL")))  # TODO move this to helpers
CACHE_PATH = Path(__file__).parent / "multicallCache.sqlite"
TEST_CACHE_PATH = Path(__file__).parent / "testing_multicallCache.sqlite"


BASE_MUlTICALL_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"


@dataclass
class NetworkConstants:
    chainId: int
    name: str
    multicallAddress: str
    # only needs to have this function Signature("tryAggregate(bool,(address,bytes)[])((bool,bytes)[])")


# I don't like this pattern
# class Network(IntEnum):
#     Mainnet = 1
#     Kovan = 42
#     Rinkeby = 4
#     Görli = 5
#     Gnosis = 100
#     Polygon = 137
#     Bsc = 56
#     Fantom = 250
#     Heco = 128
#     Harmony = 1666600000
#     Arbitrum = 42161
#     Avax = 43114
#     Moonriver = 1285
#     Aurora = 1313161554
#     Cronos = 25
#     Optimism = 10
#     OptimismKovan = 69
#     Base = 8453


# MULTICALL_ADDRESSES: Dict[int, str] = {
#     Network.Mainnet: "0xeefBa1e63905eF1D7ACbA5a8513c70307C1cE441",
#     Network.Kovan: "0x2cc8688C5f75E365aaEEb4ea8D6a480405A48D2A",
#     Network.Rinkeby: "0x42Ad527de7d4e9d9d011aC45B31D8551f8Fe9821",
#     Network.Görli: "0x77dCa2C955b15e9dE4dbBCf1246B4B85b651e50e",
#     Network.Gnosis: "0xb5b692a88BDFc81ca69dcB1d924f59f0413A602a",
#     Network.Polygon: "0x95028E5B8a734bb7E2071F96De89BABe75be9C8E",
#     Network.Bsc: "0x1Ee38d535d541c55C9dae27B12edf090C608E6Fb",
#     Network.Fantom: "0xb828C456600857abd4ed6C32FAcc607bD0464F4F",
#     Network.Heco: "0xc9a9F768ebD123A00B52e7A0E590df2e9E998707",
#     Network.Harmony: "0xFE4980f62D708c2A84D3929859Ea226340759320",
#     Network.Cronos: "0x5e954f5972EC6BFc7dECd75779F10d848230345F",
#     Network.Optimism: "0x187C0F98FEF80E87880Db50241D40551eDd027Bf",
#     Network.OptimismKovan: "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
# }


# MULTICALL2_ADDRESSES: Dict[int, str] = {
#     Network.Mainnet: "0x5ba1e12693dc8f9c48aad8770482f4739beed696",
#     Network.Kovan: "0x5ba1e12693dc8f9c48aad8770482f4739beed696",
#     Network.Rinkeby: "0x5ba1e12693dc8f9c48aad8770482f4739beed696",
#     Network.Görli: "0x5ba1e12693dc8f9c48aad8770482f4739beed696",
#     Network.Gnosis: "0x9903f30c1469d8A2f415D4E8184C93BD26992573",
#     Network.Polygon: "0xc8E51042792d7405184DfCa245F2d27B94D013b6",
#     Network.Bsc: "0xfF6FD90A470Aaa0c1B8A54681746b07AcdFedc9B",
#     Network.Fantom: "0xBAD2B082e2212DE4B065F636CA4e5e0717623d18",
#     Network.Moonriver: "0xB44a9B6905aF7c801311e8F4E76932ee959c663C",
#     Network.Arbitrum: "0x842eC2c7D803033Edf55E478F461FC547Bc54EB2",
#     Network.Avax: "0xdf2122931FEb939FB8Cf4e67Ea752D1125e18858",
#     Network.Heco: "0xd1F3BE686D64e1EA33fcF64980b65847aA43D79C",
#     Network.Aurora: "0xe0e3887b158F7F9c80c835a61ED809389BC08d1b",
#     Network.Cronos: "0x5e954f5972EC6BFc7dECd75779F10d848230345F",
#     Network.Optimism: "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
#     Network.OptimismKovan: "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
# }
