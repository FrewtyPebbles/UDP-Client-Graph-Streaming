import struct
from udp_graph.client_connection import ClientConnection
from udp_graph.protocol import HEADER_SIZE, HEADER_STRUCTURE, IP_SIZE, IP_STRUCTURE, PROTOCOL_VERSION, Packet, PacketType

class InfoPacket(Packet):
    packet_type = PacketType.INFO
    
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

        self.connections:dict[str, ClientConnection] = {}
        while remaining_packet:
            
            id_len, = struct.unpack("!B", remaining_packet[:1])
            remaining_packet = remaining_packet[1:]
            
            raw_id, = struct.unpack(f"!{id_len}s", remaining_packet[:id_len])
            client_id:str = raw_id.decode()
            remaining_packet = remaining_packet[id_len:]
            
            ip1, ip2, ip3, ip4, port = struct.unpack(f"!{IP_STRUCTURE}", remaining_packet[:IP_SIZE])
            remaining_packet = remaining_packet[IP_SIZE:]
            self.connections[client_id] = ClientConnection(client_id, f"{ip1}.{ip2}.{ip3}.{ip4}", port)
        

    def repack(self) -> bytes:
        return self.pack(self.client_id, self.connections, self.forward_list)

    @classmethod
    def pack(cls, target_client_id:str, connections:dict[str, ClientConnection], forwarded_client_ids:list[str]) -> bytes:
        connection_schemas = []
        connection_values = []

        packet_size = 0

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

        for connection in connections.values():
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


        return struct.pack(f"{HEADER_STRUCTURE}B{target_id_size}s" + forwarded_structure + "".join(connection_schemas),
            PROTOCOL_VERSION, PacketType.INFO.value, packet_size,
            target_id_size,
            target_client_id,
            *forwarded_list,
            *connection_values
        )