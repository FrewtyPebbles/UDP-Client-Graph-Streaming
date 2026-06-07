import struct

from udp_graph.protocol import HEADER_SIZE, HEADER_STRUCTURE, PROTOCOL_VERSION, Packet, PacketType


class RoutingPacket(Packet):
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

        request_type, = struct.unpack("!B", remaining_packet[:1])
        self.request_type = PacketType(int(request_type))

    def repack(self) -> bytes:
        return self.pack(self.client_id, self.forward_list, self.visited_set, self.request_type)

    @classmethod
    def pack(cls, target_client_id:str, forwarded_client_ids:list[str], visited_client_ids:set[str], request_type:PacketType) -> bytes:

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

        # add 1 byte for request type
        packet_size += 1

        return struct.pack(f"{HEADER_STRUCTURE}B{target_id_size}s" + forwarded_structure + visited_structure + "B", PROTOCOL_VERSION,
            PacketType.ROUTING.value,
            packet_size, target_id_size,
            target_client_id,
            *forwarded_list,
            *visited_set,
            request_type.value
        )