from dotenv import load_dotenv
from web3 import Web3
from pathlib import Path
import os
from enum import IntEnum
from typing import Dict


load_dotenv()
# default ETH client
W3 = Web3(Web3.HTTPProvider(os.environ.get("ALCHEMY_URL")))  # TODO move this to helpers
CACHE_PATH = Path(__file__).parent / "multicallCache.sqlite"
TEST_CACHE_PATH = Path(__file__).parent / "testing_multicallCache.sqlite"


# ordered by chain id for easy extension
class Network(IntEnum):
    Mainnet = 1
    Ropsten = 3
    Rinkeby = 4
    Gorli = 5
    Optimism = 10
    CostonTestnet = 16
    ThundercoreTestnet = 18
    SongbirdCanaryNetwork = 19
    Cronos = 25
    RSK = 30
    RSKTestnet = 31
    Kovan = 42
    Bsc = 56
    OKC = 66
    OptimismKovan = 69
    BscTestnet = 97
    Gnosis = 100
    Velas = 106
    Thundercore = 108
    Coston2Testnet = 114
    Fuse = 122
    Heco = 128
    Polygon = 137
    Fantom = 250
    Boba = 288
    KCC = 321
    ZkSync = 324
    OptimismGorli = 420
    Astar = 592
    Metis = 1088
    Moonbeam = 1284
    Moonriver = 1285
    MoonbaseAlphaTestnet = 1287
    Milkomeda = 2001
    Kava = 2222
    FantomTestnet = 4002
    Canto = 7700
    Klaytn = 8217
    Base = 8453
    EvmosTestnet = 9000
    Evmos = 9001
    Holesky = 17000
    Arbitrum = 42161
    Celo = 42220
    Oasis = 42262
    AvalancheFuji = 43113
    Avax = 43114
    GodwokenTestnet = 71401
    Godwoken = 71402
    Mumbai = 80001
    ArbitrumRinkeby = 421611
    ArbitrumGorli = 421613
    Sepolia = 11155111
    Aurora = 1313161554
    Harmony = 1666600000
    PulseChain = 369
    PulseChainTestnet = 943


MULTICALL_ADDRESSES: Dict[int, str] = {
    Network.Mainnet: "0xeefBa1e63905eF1D7ACbA5a8513c70307C1cE441",
    Network.Kovan: "0x2cc8688C5f75E365aaEEb4ea8D6a480405A48D2A",
    Network.Rinkeby: "0x42Ad527de7d4e9d9d011aC45B31D8551f8Fe9821",
    Network.Gorli: "0x77dCa2C955b15e9dE4dbBCf1246B4B85b651e50e",
    Network.Gnosis: "0xb5b692a88BDFc81ca69dcB1d924f59f0413A602a",
    Network.Polygon: "0x95028E5B8a734bb7E2071F96De89BABe75be9C8E",
    Network.Bsc: "0x1Ee38d535d541c55C9dae27B12edf090C608E6Fb",
    Network.Fantom: "0xb828C456600857abd4ed6C32FAcc607bD0464F4F",
    Network.Heco: "0xc9a9F768ebD123A00B52e7A0E590df2e9E998707",
    Network.Harmony: "0xFE4980f62D708c2A84D3929859Ea226340759320",
    Network.Cronos: "0x5e954f5972EC6BFc7dECd75779F10d848230345F",
    Network.Optimism: "0x187C0F98FEF80E87880Db50241D40551eDd027Bf",
    Network.OptimismKovan: "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
    Network.Kava: "0x7ED7bBd8C454a1B0D9EdD939c45a81A03c20131C",
}

MULTICALL2_ADDRESSES: Dict[int, str] = {
    Network.Mainnet: "0x5ba1e12693dc8f9c48aad8770482f4739beed696",
    Network.Kovan: "0x5ba1e12693dc8f9c48aad8770482f4739beed696",
    Network.Rinkeby: "0x5ba1e12693dc8f9c48aad8770482f4739beed696",
    Network.Gorli: "0x5ba1e12693dc8f9c48aad8770482f4739beed696",
    Network.Gnosis: "0x9903f30c1469d8A2f415D4E8184C93BD26992573",
    Network.Polygon: "0xc8E51042792d7405184DfCa245F2d27B94D013b6",
    Network.Bsc: "0xfF6FD90A470Aaa0c1B8A54681746b07AcdFedc9B",
    Network.Fantom: "0xBAD2B082e2212DE4B065F636CA4e5e0717623d18",
    Network.Moonriver: "0xB44a9B6905aF7c801311e8F4E76932ee959c663C",
    Network.Arbitrum: "0x842eC2c7D803033Edf55E478F461FC547Bc54EB2",
    Network.Avax: "0xdf2122931FEb939FB8Cf4e67Ea752D1125e18858",
    Network.Heco: "0xd1F3BE686D64e1EA33fcF64980b65847aA43D79C",
    Network.Aurora: "0xe0e3887b158F7F9c80c835a61ED809389BC08d1b",
    Network.Cronos: "0x5e954f5972EC6BFc7dECd75779F10d848230345F",
    Network.Optimism: "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
    Network.OptimismKovan: "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
    Network.Kava: "0x45be772faE4a9F31401dfF4738E5DC7DD439aC0b",
}

# based on https://github.com/mds1/multicall#readme
MULTICALL3_ADDRESSES: Dict[int, str] = {
    Network.Mainnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Ropsten: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Rinkeby: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Gorli: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Optimism: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.CostonTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.ThundercoreTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.SongbirdCanaryNetwork: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Cronos: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.RSK: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.RSKTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Kovan: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Bsc: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.OKC: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.OptimismKovan: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.BscTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Gnosis: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Velas: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Thundercore: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Coston2Testnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Fuse: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Heco: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Polygon: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Fantom: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Boba: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.KCC: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.ZkSync: "0x47898B2C52C957663aE9AB46922dCec150a2272c",
    Network.OptimismGorli: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Astar: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Metis: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Moonbeam: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Moonriver: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.MoonbaseAlphaTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Milkomeda: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.FantomTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Canto: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Klaytn: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.EvmosTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Evmos: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Arbitrum: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Celo: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Oasis: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.AvalancheFuji: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Avax: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.GodwokenTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Godwoken: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Mumbai: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.ArbitrumRinkeby: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.ArbitrumGorli: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Sepolia: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Aurora: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Harmony: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.PulseChain: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.PulseChainTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Base: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Holesky: "0xcA11bde05977b3631167028862bE2a173976CA11",
}
