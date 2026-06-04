from udp_graph.client import Client, ClientConnection

if __name__ == "__main__":
    c1 = Client("c1", "0.0.0.0", 1234)

    c1.connect(ClientConnection("c2", "127.0.0.1", 4321))

    c1.start_listening()

    while c1.is_listening:
        user_input = input("send:")
        if user_input.startswith("/i"):
            info_cmd = user_input.split()
            print(c1.get_client_info(info_cmd[1]).connections["c1"].to_tuple())
        else:
            c1.send_message("c3", user_input.encode())