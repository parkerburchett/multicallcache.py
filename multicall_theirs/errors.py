import enum


class EthRPCError(enum.Enum):
    OUT_OF_GAS = enum.auto
    EXECUTION_REVERTED = enum.auto
    UNKNOWN = enum.auto
