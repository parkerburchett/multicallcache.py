from multicall.signature import Signature, SignatureFailedToEncodeData
from multicall.call import Call, HandlingFunctionFailed
from multicall_theirs.multicall import Multicall, MulticallV2, _initialize_multiprocessing

# try to use forkserver/spawn
_initialize_multiprocessing()
#TODO remove this
