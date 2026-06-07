import struct
from udp_graph.client_connection import ClientConnection
from udp_graph.protocol import HEADER_SIZE, HEADER_STRUCTURE, IP_SIZE, IP_STRUCTURE, PROTOCOL_VERSION, Packet, PacketType

class ConnectPacket(Packet):
    packet_type = PacketType.CONNECT
    
    def __init__(self, packet:bytes):
        _, _, raw_packet_size = struct.unpack(HEADER_STRUCTURE, packet[:HEADER_SIZE])
        packet_size = int(raw_packet_size)
        remaining_packet = packet[HEADER_SIZE:]
        if len(remaining_packet) != packet_size:
            raise ValueError("Invalid packet size")
        
        id_len, = struct.unpack("!B", remaining_packet[:1])
        remaining_packet = remaining_packet[1:]
        
        raw_id, = struct.unpack(f"!{id_len}s", remaining_packet[:id_len])
        client_id:str = raw_id.decode()
        remaining_packet = remaining_packet[id_len:]

        ip1, ip2, ip3, ip4, port = struct.unpack(f"!{IP_STRUCTURE}", remaining_packet[:IP_SIZE])
        remaining_packet = remaining_packet[IP_SIZE:]
        self.client_connection = ClientConnection(client_id, f"{ip1}.{ip2}.{ip3}.{ip4}", port)
        

    def repack(self) -> bytes:
        return self.pack(self.client_connection)

    @classmethod
    def pack(cls, client_connection:ClientConnection) -> bytes:
        packet_size = 0

        target_client_id = client_connection.client_id.encode("utf-8")
        target_id_size = len(target_client_id)
        packet_size = 1 + target_id_size

        connection_values = [
            *map(int, client_connection.ip.split(".")),
            client_connection.port
        ]

        packet_size += IP_SIZE


        return struct.pack(f"{HEADER_STRUCTURE}B{target_id_size}s" + IP_STRUCTURE,
            PROTOCOL_VERSION, PacketType.CONNECT.value, packet_size,
            target_id_size,
            target_client_id,
            *connection_values
        )