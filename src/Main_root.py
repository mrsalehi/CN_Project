from Root import Root
from config import root_port

if __name__ == "__main__":
    root = Root(server_ip="192.168.000.001", server_port=root_port, is_root=False)
