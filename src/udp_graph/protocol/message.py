import struct
from udp_graph.protocol import HEADER_SIZE, HEADER_STRUCTURE, PROTOCOL_VERSION, Packet, PacketType


class MessagePacket(Packet):
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

        return struct.pack(f"{HEADER_STRUCTURE}B{target_id_size}s" + forwarded_structure + f"B{message_size}s",
            PROTOCOL_VERSION, PacketType.MESSAGE.value, packet_size,
            target_id_size,
            target_client_id,
            *forwarded_list,
            message_size,
            message
        )