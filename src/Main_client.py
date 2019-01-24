from Root import Root
from Client import Client
from config import root_port, client_port

if __name__ == "__main__":
    #server = Root("insert IP Address", "Insert Port as Int", is_root=True)
    #server.run()

    #root = Root(server_ip="192.168.000.001", server_port=5230, is_root=False)
    client = Client(server_ip="192.168.000.002", server_port=client_port, is_root=False,
                    root_address=("192.168.000.001", root_port))

