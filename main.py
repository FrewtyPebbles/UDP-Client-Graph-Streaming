import re

from udp_graph.client import Client, ClientConnection
import argparse

def validate_ip(ip_address: str) -> bool:
    ip_pattern = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    return bool(ip_pattern.match(ip_address))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A demo client that can send messages to other clients using a BFS.")
    parser.add_argument("client_name", type=str, help="The name of the client on the mesh network.")
    parser.add_argument("-a","--address", type=str, help="The address of the client.", default="0.0.0.0")
    parser.add_argument("-p","--port", type=int, help="The name of the client on the mesh network.", default=21435)
    args = parser.parse_args()
    client = Client(args.client_name, args.address, args.port)

    

    client.start_listening()

    recipient = None

    while client.is_listening:
        user_input = input("send:")
        if user_input.startswith("/info"):
            info_cmd = user_input.split()
            if len(info_cmd) == 2:
                client_info = client.get_client_info(info_cmd[1])
                if client_info:
                    print(f"{info_cmd[1]!r}'s connections:")
                    for connection in client_info.connections.values():
                        print(f"\n - {connection.client_id!r}:\n\taddress: {connection.ip}:{connection.port}")
                else:
                    print(f"Client {info_cmd[1]!r} could not be found ;(")
            else:
                print("usage: /info <client_id>\n - Shows clients connected to this client")
        elif user_input.startswith("/connect"):
            con_cmd = user_input.split()
            if len(con_cmd) == 4 and validate_ip(con_cmd[2]):
                try:
                    port = int(con_cmd[3])
                    client.connect(ClientConnection(con_cmd[1], con_cmd[2], port))
                except:
                    print("usage: /connect <client_id> <ip address> <port>\n - Connects this client to another client.")
            else:
                print("usage: /connect <client_id> <ip address> <port>\n - Connects this client to another client.")
        elif user_input.startswith("/recipient"):
            con_cmd = user_input.split()
            if len(con_cmd) == 2 and con_cmd[1] in client.connections:
                recipient = con_cmd[1]
            else:
                print("usage: /recipient <client_id>\n - Sets the recipient for messages.")
        else:
            if recipient:
                client.send_message(recipient, user_input.encode())
            else:
                print("No recipient selected. Select the recipient of your messages with \"/recipient\".")
        
        msg = client.listen_for_message(timeout=1)
        if msg:
            print(msg.message)