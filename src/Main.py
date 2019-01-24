from Root import Root
from Client import Client

if __name__ == "__main__":
    #server = Root("insert IP Address", "Insert Port as Int", is_root=True)
    #server.run()

    client = Client(server_ip="192.168.000.001", server_port=5231, is_root=False,
                  root_address=("192.168.000.000", 5230))


    client1 = Client(server_ip="192.168.000.001", server_port=5232, is_root=False,
                    root_address=("192.168.000.000", 5230))

    