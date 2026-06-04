import socket as soct
import threading
from udp_graph.client_connection import ClientConnection
from udp_graph.protocol import InfoPacketRequest, Packet, PacketType, InfoPacketResponse
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
        self.packet_queue = queue.Queue(queue_size)

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
    
    def send_bytes(self, client_id:str, packet:bytes):
        connection = self.connections[client_id]
        self.udp_socket.sendto(packet, connection.to_tuple())

    def get_client_info(self, client_id:str, timeout:int = 3) -> InfoPacketResponse:
        self.send_bytes(client_id, InfoPacketRequest.pack())
        return self.packet_queue.get(timeout=timeout)
    
    def packet_handler(self, raw_address:tuple[str, int], data:bytes):
        packet = Packet.unpack(data)

        match packet.packet_type:
            case PacketType.INFO_REQUEST:
                self.send_bytes(self.raw_to_id[raw_address], InfoPacketResponse.pack(list(self.connections.values())))
            case PacketType.INFO_RESPONSE:
                self.packet_queue.put(packet)
                    

    def start_listening(self):
        """Starts the background listening loop."""
        self.is_listening = True
        self.listen_loop_thread.start()
        print("Client receiver loop started...")

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
                    print(f"Unknown sender {ip}:{port}")
            except OSError:
                break
        self.disconnect_all()
        self.udp_socket.close()
        