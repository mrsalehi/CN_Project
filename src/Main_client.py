from Root import Root
from Client import Client
from config import root_port, client_port, has_GUI
from UserInterface import *

if __name__ == "__main__":
    if not has_GUI:
        print("port: ", client_port)
    root_ip = "192.168.000.001"
    client_ip = "192.168.000.002"
    user_interface = UserInterface((client_ip, client_port))
    main_thread = threading.Thread(target=Client, args=(client_ip, client_port, user_interface, False, (root_ip, root_port)))
    main_thread.start()
    if has_GUI:
        user_interface.run()
    # client = Client(server_ip=client_ip, server_port=client_port,
    #                 user_interface=user_interface,
    #                 is_root=False,
    #                 root_address=(root_ip, root_port))
