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
    INFO_REQUEST = 0
    INFO_RESPONSE = 1
    MESSAGE = 2
    ROUTING = 3
    BACKTRACE = 4
    

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
        _, _, raw_packet_size = struct.unpack(HEADER_STRUCTURE, packet[:HEADER_SIZE])
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
            
            print(remaining_packet[:IP_SIZE])
            ip1, ip2, ip3, ip4, port = struct.unpack(f"!{IP_STRUCTURE}", remaining_packet[:IP_SIZE])
            remaining_packet = remaining_packet[IP_SIZE:]
            connections.append(ClientConnection(client_id, f"{ip1}.{ip2}.{ip3}.{ip4}", port))
        
        self.connections = {con.client_id:con for con in connections}

    @classmethod
    def pack(cls, connections:list[ClientConnection]) -> bytes:
        connection_schemas = []
        connection_values = []

        packet_size = 0

        for connection in connections:
            c_id = connection.client_id.encode("utf-8")
            id_size = len(c_id)
            connection_schemas.append("B" + f"{id_size}s" + IP_STRUCTURE)
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
        _, _, raw_packet_size = struct.unpack(HEADER_STRUCTURE, packet[:HEADER_SIZE])
        packet_size = int(raw_packet_size)
        remaining_packet = packet[HEADER_SIZE:]
        if len(remaining_packet) != packet_size:
            raise ValueError("Invalid packet size")

        id_len, = struct.unpack("!B", remaining_packet[:1])
        remaining_packet = remaining_packet[1:]
        
        raw_id, = struct.unpack(f"!{id_len}s", remaining_packet[:id_len])
        self.client_id:str = raw_id.decode()
        remaining_packet = remaining_packet[id_len:]

        # FORWARD LIST
        num_forwarded, = struct.unpack("!B", remaining_packet[:1])
        remaining_packet = remaining_packet[1:]
        self.forward_list:list[str] = []
        for _ in range(num_forwarded):
            c_id_len, = struct.unpack("!B", remaining_packet[:1])
            remaining_packet = remaining_packet[1:]
            forwarded, = struct.unpack(f"!{c_id_len}s", remaining_packet[:c_id_len])
            remaining_packet = remaining_packet[c_id_len:]
            self.forward_list.append(forwarded.decode())

        # END FORWARD LIST

        message_len, = struct.unpack("!B", remaining_packet[:1])
        remaining_packet = remaining_packet[1:]

        if len(remaining_packet) < message_len:
            raise ValueError("Message too large.")
        
        self.message = remaining_packet

    def repack(self) -> bytes:
        return self.pack(self.client_id, self.message, self.forward_list)

    @classmethod
    def pack(cls, target_client_id:str, message:bytes, forwarded_client_ids:list[str]) -> bytes:

        target_client_id = target_client_id.encode("utf-8")
        target_id_size = len(target_client_id)
        packet_size = 1 + target_id_size

        # BEGIN FORWARDED
        forwarded_structure = "B"
        forwarded_list = [len(forwarded_client_ids)] # number of visited client IDs
        for c_id in forwarded_client_ids:
            c_id = c_id.encode()
            c_id_len = len(c_id)
            forwarded_list.extend([c_id_len, c_id])
            forwarded_structure += f"B{c_id_len}s"
            
        packet_size += struct.calcsize(forwarded_structure)
        # END FORWARDED

        message_size = len(message)
        packet_size += 1 + message_size

        return struct.pack(f"{HEADER_STRUCTURE}B{target_id_size}s" + forwarded_structure + f"B{message_size}s", PROTOCOL_VERSION,
            PacketType.MESSAGE.value,
            packet_size, target_id_size,
            target_client_id, *forwarded_list,
            message_size, message
        )
    
class RoutingPacket:
    packet_type = PacketType.ROUTING
    
    def __init__(self, packet:bytes):
        _, _, raw_packet_size = struct.unpack(HEADER_STRUCTURE, packet[:HEADER_SIZE])
        packet_size = int(raw_packet_size)
        remaining_packet = packet[HEADER_SIZE:]
        if len(remaining_packet) != packet_size:
            raise ValueError("Invalid packet size")

        id_len, = struct.unpack("!B", remaining_packet[:1])
        remaining_packet = remaining_packet[1:]
        
        raw_id, = struct.unpack(f"!{id_len}s", remaining_packet[:id_len])
        self.client_id:str = raw_id.decode()
        remaining_packet = remaining_packet[id_len:]

        # FORWARD LIST
        num_forwarded, = struct.unpack("!B", remaining_packet[:1])
        remaining_packet = remaining_packet[1:]
        self.forward_list:list[str] = []
        for _ in range(num_forwarded):
            c_id_len, = struct.unpack("!B", remaining_packet[:1])
            remaining_packet = remaining_packet[1:]
            forwarded, = struct.unpack(f"!{c_id_len}s", remaining_packet[:c_id_len])
            remaining_packet = remaining_packet[c_id_len:]
            self.forward_list.append(forwarded.decode())

        # END FORWARD LIST

        # VISITED SET
        num_visited, = struct.unpack("!B", remaining_packet[:1])
        remaining_packet = remaining_packet[1:]
        self.visited_set:set[str] = set()
        for _ in range(num_visited):
            c_id_len, = struct.unpack("!B", remaining_packet[:1])
            remaining_packet = remaining_packet[1:]
            visited, = struct.unpack(f"!{c_id_len}s", remaining_packet[:c_id_len])
            remaining_packet = remaining_packet[c_id_len:]
            self.visited_set.add(visited.decode())
        # END VISITED SET

    def repack(self) -> bytes:
        return self.pack(self.client_id, self.forward_list, self.visited_set)

    @classmethod
    def pack(cls, target_client_id:str, forwarded_client_ids:list[str], visited_client_ids:set[str]) -> bytes:

        target_client_id = target_client_id.encode("utf-8")
        target_id_size = len(target_client_id)
        packet_size = 1 + target_id_size

        # BEGIN FORWARDED
        forwarded_structure = "B"
        forwarded_list = [len(forwarded_client_ids)] # number of visited client IDs
        for c_id in forwarded_client_ids:
            c_id = c_id.encode()
            c_id_len = len(c_id)
            forwarded_list.extend([c_id_len, c_id])
            forwarded_structure += f"B{c_id_len}s"
            
        packet_size += struct.calcsize(forwarded_structure)
        # END FORWARDED

        # BEGIN VISITED
        visited_structure = "B"
        visited_set = [len(visited_client_ids)] # number of visited client IDs
        for c_id in visited_client_ids:
            c_id = c_id.encode()
            c_id_len = len(c_id)
            visited_set.extend([c_id_len, c_id])
            visited_structure += f"B{c_id_len}s"
            
        packet_size += struct.calcsize(visited_structure)
        # END VISITED

        return struct.pack(f"{HEADER_STRUCTURE}B{target_id_size}s" + forwarded_structure + visited_structure, PROTOCOL_VERSION,
            PacketType.ROUTING.value,
            packet_size, target_id_size,
            target_client_id,
            *forwarded_list,
            *visited_set
        )
        
class BacktracePacket:
    packet_type = PacketType.BACKTRACE
    
    def __init__(self, packet:bytes):
        _, _, raw_packet_size = struct.unpack(HEADER_STRUCTURE, packet[:HEADER_SIZE])
        packet_size = int(raw_packet_size)
        remaining_packet = packet[HEADER_SIZE:]
        if len(remaining_packet) != packet_size:
            raise ValueError("Invalid packet size")

        # FORWARD LIST
        num_forwarded, = struct.unpack("!B", remaining_packet[:1])
        remaining_packet = remaining_packet[1:]
        self.forward_list:list[str] = []
        for _ in range(num_forwarded):
            c_id_len, = struct.unpack("!B", remaining_packet[:1])
            remaining_packet = remaining_packet[1:]
            forwarded, = struct.unpack(f"!{c_id_len}s", remaining_packet[:c_id_len])
            remaining_packet = remaining_packet[c_id_len:]
            self.forward_list.append(forwarded.decode())

        # END FORWARD LIST

    def repack(self) -> bytes:
        return self.pack(self.client_id, self.forward_list, self.visited_set)

    @classmethod
    def pack(cls, forwarded_client_ids:list[str]) -> bytes:
        packet_size = 0

        # BEGIN FORWARDED
        forwarded_structure = "B"
        forwarded_list = [len(forwarded_client_ids)] # number of visited client IDs
        for c_id in forwarded_client_ids:
            c_id = c_id.encode()
            c_id_len = len(c_id)
            forwarded_list.extend([c_id_len, c_id])
            forwarded_structure += f"B{c_id_len}s"
            
        packet_size += struct.calcsize(forwarded_structure)
        # END FORWARDED

        return struct.pack(HEADER_STRUCTURE + forwarded_structure, PROTOCOL_VERSION,
            PacketType.BACKTRACE.value,
            packet_size, 
            *forwarded_list,
        )
    
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
            case PacketType.MESSAGE:
                return MessagePacket(packet)
            case PacketType.ROUTING:
                return RoutingPacket(packet)
            case PacketType.BACKTRACE:
                return BacktracePacket(packet)
            