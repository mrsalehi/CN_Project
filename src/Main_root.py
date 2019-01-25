from Root import Root
from config import root_port
import threading
from UserInterface import *
from config import has_GUI

if __name__ == "__main__":
    root_ip = "192.168.000.001"
    user_interface = UserInterface((root_ip, root_port))
    main_thread = threading.Thread(target=Root, args=(root_ip, root_port, user_interface))
    main_thread.start()
    if has_GUI:
        user_interface.run()


