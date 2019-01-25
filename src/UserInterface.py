import threading
import time
from tkinter import *
from config import has_GUI


class UserInterface():

    def __init__(self, server_address):
        self.server_ip = server_address[0]
        self.server_port = server_address[1]
        self.buffer = []
        self.printer = []

    def GUI(self, buffer):
        def register():
            buffer.append("Register")

        def advertise():
            buffer.append("Advertise")

        def send(event=None):
            msg = text.get()
            text.set("")
            buffer.append("send %s" % msg)
            # print(msg)
            # msg_list.insert(END, msg)

        def handle_printer():
            while True:
                time.sleep(0.5)
                for msg in self.printer:
                    msg_list.insert(END, msg)
                self.printer.clear()

        screen = Tk()
        screen.title("P2P UI")
        screen.geometry("500x400")

        label = Label(screen, text="address: (%s, %d)" % (self.server_ip, self.server_port))
        label.pack()

        register_b = Button(screen, text="Register", command=register)
        register_b.pack()

        advertise_b = Button(screen, text="Advertise", command=advertise)
        advertise_b.pack()

        messages_frame = Frame(screen)
        text = StringVar()  # For the messages to be sent.
        text.set("")
        scrollbar = Scrollbar(messages_frame)

        msg_list = Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        msg_list.pack(side=LEFT)
        msg_list.pack()
        messages_frame.pack()
        entry_field = Entry(screen, textvariable=text)
        entry_field.bind("<Return>", send)
        entry_field.pack()
        send_button = Button(screen, text="Send", command=send)
        send_button.pack()

        printer_t = threading.Thread(target=handle_printer)
        printer_t.start()

        screen.mainloop()

    def run(self):
        """
        Which the user or client sees and works with.
        This method runs every time to see whether there are new messages or not.
        """
        if has_GUI:
            self.GUI(self.buffer)
        else:
            while True:
                message = input("Write your command:\n")
                # print(message)
                self.buffer.append(message)
