import socket
from udp_graph.protocol import RegisterPacket, FailPacket, PacketType
from udp_graph.client_connection import ClientConnection

class Registrar:
    # This class acts as a registrar and ip relay for creating p2p UDP connections
    def __init__(self, connected_clients:dict[str, ClientConnection]|None = None):
        self.connected_clients:dict[str, ClientConnection] = connected_clients or {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def add_client(self, client_id:str, address:str, port:int):
        # try to perform STUN in accordance with RFC 5389
        cc = ClientConnection(address, port)
        self.socket.sendto(RegisterPacket.pack(cc), cc.to_tuple()) # STUN
        self.connected_clients[client_id] = cc

    def connect_clients(self, requesting_client:str, target_client:str):
        """ Forward each client's client connection to eachother """
        if target_client in self.connected_clients and requesting_client in self.connected_clients:
            requesting_connection = self.connected_clients[requesting_client]
            target_connection = self.connected_clients[target_client]
            self.socket.sendto(RegisterPacket.pack(target_connection), requesting_connection.to_tuple())
            self.socket.sendto(RegisterPacket.pack(requesting_connection), target_connection.to_tuple())
        elif target_client not in self.connected_clients and requesting_client in self.connected_clients:
            # ON FAIL, SEND FAILURE PACKET.
            requesting_connection = self.connected_clients[requesting_client]
            self.socket.sendto(FailPacket.pack(target_client, PacketType.CONNECT), requesting_connection.to_tuple())
        else:
            raise ConnectionError(f"Failed to connect client {requesting_client!r} to client {target_client!r}")