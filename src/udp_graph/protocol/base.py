from abc import ABC, abstractmethod
import struct
from enum import Enum
from typing import Self
from udp_graph.client_connection import ClientConnection

PROTOCOL_VERSION = 0 # 16 bit
HEADER_STRUCTURE = "!HBH"
HEADER_SIZE = struct.calcsize("!HBH")
IP_STRUCTURE = "BBBBH"
IP_SIZE = struct.calcsize(f"!{IP_STRUCTURE}")

class PacketType(Enum): # 8 bit
    INFO = 0
    MESSAGE = 1
    ROUTING = 2
    BACKTRACE = 3
    REGISTER = 4
    CONNECT = 5
    FAIL = 6

class Packet(ABC):
    @classmethod
    def unpack_headers(cls, packet:bytes):
        raw_protocol_version, raw_packet_type, raw_packet_size = struct.unpack(HEADER_STRUCTURE, packet[:5])
        return int(raw_protocol_version), PacketType(int(raw_packet_type)), int(raw_packet_size)
    @classmethod
    def unpack(cls, packet:bytes):
        from udp_graph.protocol import BacktracePacket, InfoPacket, MessagePacket, RoutingPacket

        _, raw_packet_type, _ = struct.unpack(HEADER_STRUCTURE, packet[:5])
        packet_type = PacketType(int(raw_packet_type))

        match packet_type:
            case PacketType.INFO:
                return InfoPacket(packet)
            case PacketType.MESSAGE:
                return MessagePacket(packet)
            case PacketType.ROUTING:
                return RoutingPacket(packet)
            case PacketType.BACKTRACE:
                return BacktracePacket(packet)

    @abstractmethod
    def repack(self) -> bytes:
        pass

    @classmethod
    @abstractmethod
    def pack(self, *args, **kwargs) -> bytes:
        pass

