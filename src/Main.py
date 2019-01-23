from Root import Root
from Client import Client

if __name__ == "__main__":
    server = Root("insert IP Address", "Insert Port as Int", is_root=True)
    server.run()

    client = Client("Insert IP Address", "Insert Port as Int", is_root=False,
                  root_address=("Insert IP Address", "Insert Port as Int"))
    