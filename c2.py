from udp_graph.client import Client, ClientConnection

if __name__ == "__main__":
    c2 = Client("c2", "0.0.0.0", 4321)

    c2.connect(ClientConnection("c1", "127.0.0.1", 1234))

    c2.start_listening()

    while c2.is_listening:
        user_input = input("send:")
        if user_input.startswith("/i"):
            info_cmd = user_input.split()
            print(c2.get_client_info(info_cmd[1]).connections["c2"].to_tuple())
        else:
            c2.send_bytes("c1", user_input.encode())