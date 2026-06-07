  
import struct

from udp_graph.protocol import HEADER_SIZE, HEADER_STRUCTURE, PROTOCOL_VERSION, Packet, PacketType


class BacktracePacket(Packet):
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
    

            