import struct
from enum import Enum
from typing import Self
from udp_graph.client_connection import ClientConnection

PROTOCOL_VERSION = 0 # 16 bit
HEADER_STRUCTURE = "!HBH"
HEADER_SIZE = struct.calcsize("!HBH")
IP_SIZE = struct.calcsize("!BBBBH")

class PacketType(Enum): # 8 bit
    INFO_REQUEST = 0
    INFO_RESPONSE = 1
    MESSAGE = 2
    

class InfoPacketRequest:
    packet_type = PacketType.INFO_REQUEST

    def __init__(self, packet:bytes):
        pass

    @classmethod
    def pack(cls) -> bytes:
        return struct.pack(HEADER_STRUCTURE, PROTOCOL_VERSION, PacketType.INFO_REQUEST.value, 0)

class InfoPacketResponse:
    packet_type = PacketType.INFO_RESPONSE
    
    def __init__(self, packet:bytes):
        _, raw_packet_type, raw_packet_size = struct.unpack(HEADER_STRUCTURE, packet[:HEADER_SIZE])
        packet_type = PacketType(int(raw_packet_type))
        packet_size = int(raw_packet_size)
        remaining_packet = packet[HEADER_SIZE:]
        if len(remaining_packet) != packet_size:
            raise ValueError("Invalid packet size")
        connections:list[ClientConnection] = []
        while remaining_packet:
            
            id_len, = struct.unpack("!B", remaining_packet[:1])
            remaining_packet = remaining_packet[1:]
            
            raw_id, = struct.unpack(f"!{id_len}s", remaining_packet[:id_len])
            client_id:str = raw_id.decode()
            remaining_packet = remaining_packet[id_len:]
            
            ip1, ip2, ip3, ip4, port = struct.unpack(f"!BBBBH", remaining_packet[:IP_SIZE])
            remaining_packet = remaining_packet[IP_SIZE:]
            connections.append(ClientConnection(client_id, f"{ip1}.{ip2}.{ip3}.{ip4}", port))
        
        self.connections = {con.client_id:con for con in connections}

    @classmethod
    def pack(cls, connections:list[ClientConnection]) -> bytes:
        connection_schemas = []
        connection_values = []

        packet_size = 0

        ip_schema = "BBBBH"

        for connection in connections:
            c_id = connection.client_id.encode("utf-8")
            id_size = len(c_id)
            connection_schemas.append("B" + f"{id_size}s" + ip_schema)
            packet_size += 1 + id_size + IP_SIZE
            connection_values.extend([
                id_size,
                c_id,
                *map(int, connection.ip.split(".")),
                connection.port
            ])


        return struct.pack(HEADER_STRUCTURE + "".join(connection_schemas), PROTOCOL_VERSION, PacketType.INFO_RESPONSE.value, packet_size, *connection_values)
    
class MessagePacket:
    packet_type = PacketType.MESSAGE
    
    def __init__(self, packet:bytes):
        _, raw_packet_type, raw_packet_size = struct.unpack(HEADER_STRUCTURE, packet[:HEADER_SIZE])
        packet_type = PacketType(int(raw_packet_type))
        packet_size = int(raw_packet_size)
        remaining_packet = packet[HEADER_SIZE:]
        if len(remaining_packet) != packet_size:
            raise ValueError("Invalid packet size")
        connections:list[ClientConnection] = []
        while remaining_packet:

            id_len, = struct.unpack("!B", remaining_packet[:1])
            remaining_packet = remaining_packet[1:]
            
            raw_id, = struct.unpack(f"!{id_len}s", remaining_packet[:id_len])
            client_id:str = raw_id.decode()
            remaining_packet = remaining_packet[id_len:]
            
            ip1, ip2, ip3, ip4, port = struct.unpack(f"!BBBBH", remaining_packet[:IP_SIZE])
            remaining_packet = remaining_packet[IP_SIZE:]
            
            connections.append(ClientConnection(client_id, f"{ip1}.{ip2}.{ip3}.{ip4}", port))
        
        self.connections = {con.client_id:con for con in connections}

    @classmethod
    def pack(cls, connections:list[ClientConnection]) -> bytes:
        connection_schemas = []
        connection_values = []

        packet_size = 0

        ip_schema = "BBBBH"

        for connection in connections:
            c_id = connection.client_id.encode("utf-8")
            id_size = len(c_id)
            connection_schemas.append("B" + f"{id_size}s" + ip_schema)
            packet_size += 1 + id_size + IP_SIZE
            connection_values.extend([
                id_size,
                c_id,
                *map(int, connection.ip.split(".")),
                connection.port
            ])


        return struct.pack(HEADER_STRUCTURE + "".join(connection_schemas), PROTOCOL_VERSION, PacketType.INFO_RESPONSE.value, packet_size, *connection_values)
    
class Packet:
    @classmethod
    def unpack_headers(cls, packet:bytes):
        raw_protocol_version, raw_packet_type, raw_packet_size = struct.unpack(HEADER_STRUCTURE, packet[:5])
        return int(raw_protocol_version), PacketType(int(raw_packet_type)), int(raw_packet_size)
    @classmethod
    def unpack(cls, packet:bytes):
        _, raw_packet_type, _ = struct.unpack(HEADER_STRUCTURE, packet[:5])
        packet_type = PacketType(int(raw_packet_type))

        match packet_type:
            case PacketType.INFO_REQUEST:
                return InfoPacketRequest(packet)
            case PacketType.INFO_RESPONSE:
                return InfoPacketResponse(packet)