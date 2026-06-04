import socket as soct
import threading
from udp_graph.client_connection import ClientConnection
from udp_graph.protocol import InfoPacketRequest, Packet, PacketType, InfoPacketResponse, MessagePacket, RoutingPacket, BacktracePacket
import queue
# TODO Implement connection reset request for if the queue misses alot of packets

class Client:
    def __init__(self, client_id:str, ip:str, port:int, queue_size:int = 10):
        self.client_id = client_id
        self.connections:dict[str, ClientConnection] = {}
        self.raw_to_connections:dict[tuple[str, int], ClientConnection] = {}
        self.raw_to_id:dict[tuple[str, int], str] = {}
        self.is_listening = False
        self.buffer_size = 1024
        self.udp_socket = soct.socket(soct.AF_INET, soct.SOCK_DGRAM)
        self.ip = ip
        self.port = port
        self.listen_loop_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.client_info_queue:queue.Queue[InfoPacketResponse] = queue.Queue(queue_size)
        self.client_message_queue:queue.Queue[MessagePacket] = queue.Queue(queue_size)
        self.backtrace_packet_queue:queue.Queue[BacktracePacket] = queue.Queue(queue_size)

    def connect(self, connection:ClientConnection):
        self.connections[connection.client_id] = connection
        self.raw_to_connections[connection.to_tuple()] = connection
        self.raw_to_id[connection.to_tuple()] = connection.client_id

    def disconnect(self, connection:ClientConnection):
        del self.connections[connection.client_id]
        del self.raw_to_connections[connection.to_tuple()]
        del self.raw_to_id[connection.to_tuple()]

    def disconnect_all(self):
        self.connections = {}
        self.raw_to_connections = {}
        self.raw_to_id = {}
    
    def raw_send_bytes(self, client_connection:ClientConnection, packet:bytes):
        self.udp_socket.sendto(packet, client_connection.to_tuple())

    def get_client_info(self, client_connection:ClientConnection | str, timeout:int|None = None) -> InfoPacketResponse:
        client_connection = self.connections[client_connection] if isinstance(client_connection, str) else client_connection
        self.raw_send_bytes(client_connection, InfoPacketRequest.pack())
        return self.client_info_queue.get(timeout=timeout)
    
    def listen_for_backtrace(self, block:bool = True, timeout:int|None = None) -> BacktracePacket|None:
        try:
            return self.backtrace_packet_queue.get(block, timeout)
        except queue.Empty:
            return None
    
    def send_message(self, target_client_id:str, message:bytes, timeout:int = 1):
        """Sends a message to the supplied client_id by using a breadth first search"""
        if target_client_id in self.connections:
            self.raw_send_bytes(self.connections[target_client_id], MessagePacket.pack(target_client_id, message, [self.client_id]))
        else:
            connections = self.connections.values()
            for connection in connections:
                self.raw_send_bytes(connection, RoutingPacket.pack(target_client_id, [self.client_id], {con.client_id for con in connections}))

            backtraces:list[BacktracePacket] = []
            while backtrace := self.listen_for_backtrace(timeout=1):
                backtraces.append(backtrace)
            
            if not backtraces:
                raise ConnectionError(f"Failed to get backtrace to client {target_client_id!r}")
            
            shortest_bt = min(backtraces, key=lambda bt: len(bt.forward_list))
            self.raw_send_bytes(self.connections[shortest_bt.forward_list[1]], MessagePacket.pack(target_client_id, message, shortest_bt.forward_list))
            
            
    def send_backtrace(self, forward_list:list[str]):
        i = forward_list.index(self.client_id)
        self.raw_send_bytes(self.connections[forward_list[i-1]], BacktracePacket.pack(forward_list))


    def listen_for_message(self, block:bool = True, timeout:int|None = None) -> MessagePacket | None:
        try:
            return self.client_message_queue.get(block, timeout)
        except queue.Empty:
            return None
    
    def packet_handler(self, raw_address:tuple[str, int], data:bytes):
        packet = Packet.unpack(data)

        match packet.packet_type:
            case PacketType.INFO_REQUEST:
                self.send_client_info(raw_address, packet)
            case PacketType.INFO_RESPONSE:
                self.client_info_queue.put(packet)
            case PacketType.MESSAGE:
                self.handle_message_packet(raw_address, packet)
            case PacketType.ROUTING:
                self.handle_routing_packet(raw_address, packet)
            case PacketType.BACKTRACE:
                self.handle_backtrace_packet(raw_address, packet)


    def send_client_info(self, raw_address:tuple[str, int], packet:MessagePacket):
        self.raw_send_bytes(self.raw_to_connections[raw_address], InfoPacketResponse.pack(list(self.connections.values())))

    def handle_backtrace_packet(self, raw_address:tuple[str, int], packet:BacktracePacket):
        if packet.forward_list[0] == self.client_id:
            self.backtrace_packet_queue.put(packet)
            return
        self.send_backtrace(packet.forward_list)

    def handle_routing_packet(self, raw_address:tuple[str, int], packet:RoutingPacket):
        packet.forward_list.append(self.client_id)
        if packet.client_id == self.client_id:
            self.send_backtrace(packet.forward_list)
            return
        
        to_forwards:list[ClientConnection] = []
        for client_id, con in self.connections.items():
            if client_id not in packet.visited_set:
                packet.visited_set.add(client_id)
                to_forwards.append(con)
        
        for forward in to_forwards:
            self.forward_packet(forward, packet)

    def handle_message_packet(self, raw_address:tuple[str, int], packet:MessagePacket):
        if packet.client_id == self.client_id:
            self.client_message_queue.put(packet)
            return
        # Figure out where the client is in the forward list and go to the next one.
        i = packet.forward_list.index(self.client_id)
        self.forward_packet(self.connections[packet.forward_list[i+1]], packet)
            
    def forward_packet(self, connection:ClientConnection, packet:MessagePacket|RoutingPacket|BacktracePacket):
        self.raw_send_bytes(connection, packet.repack())

    def start_listening(self):
        """Starts the background listening loop."""
        self.is_listening = True
        self.listen_loop_thread.start()

    def stop_listening(self):
        self.is_listening = False
    
    def _listen_loop(self):
        self.udp_socket.bind((self.ip, self.port))
        while self.is_listening:
            try:
                data, raw_sender_address = self.udp_socket.recvfrom(self.buffer_size)
                if raw_sender_address in self.raw_to_connections:
                    self.packet_handler(raw_sender_address, data)
                else:
                    ip, port = raw_sender_address
            except OSError:
                break
        self.disconnect_all()
        self.udp_socket.close()
        