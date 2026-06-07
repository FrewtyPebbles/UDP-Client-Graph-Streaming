import struct

from udp_graph.protocol import HEADER_SIZE, HEADER_STRUCTURE, PROTOCOL_VERSION, Packet, PacketType


class FailPacket(Packet):
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

        request_type, = struct.unpack("!B", remaining_packet[:1])
        self.request_type = PacketType(int(request_type))

    def repack(self) -> bytes:
        return self.pack(self.client_id, self.request_type)

    @classmethod
    def pack(cls, target_client_id:str, request_type:PacketType) -> bytes:

        target_client_id = target_client_id.encode("utf-8")
        target_id_size = len(target_client_id)
        packet_size = 1 + target_id_size

        # add 1 byte for request type
        packet_size += 1

        return struct.pack(f"{HEADER_STRUCTURE}B{target_id_size}s" + "B", PROTOCOL_VERSION,
            PacketType.ROUTING.value,
            packet_size, target_id_size,
            target_client_id,
            request_type.value
        )