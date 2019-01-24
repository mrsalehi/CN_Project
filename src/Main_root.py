from Root import Root
from config import root_port

if __name__ == "__main__":
    #server = Root("insert IP Address", "Insert Port as Int", is_root=True)
    #server.run()

    root = Root(server_ip="192.168.000.001", server_port=root_port, is_root=False)
    #client = Client(server_ip="192.168.000.002", server_port=5232, is_root=False, root_address=("192.168.000.001", 5230))

