class ClientConnection:
    def __init__(self, client_id:str, ip:str, port:int):
        self.client_id = client_id
        self.ip = ip
        self.port = port
    
    def to_tuple(self):
        return self.ip, self.port