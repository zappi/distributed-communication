import json
from threading import Thread, Lock
import socket
import sys
import time


class Client():
    """
    Client is initialized with client_port as a parameter
    """
    def __init__(self, client_port):
        self.identifier = client_port
        self.server_tcp = ('127.0.0.1', 8889)
        self.lock = Lock()
        self.server_listener = SocketThread(
            self, client_port, self.server_tcp, self.lock)
        self.server_listener.start()
        self.server_message = []

    """
    Used to send messages to the server.
    """
    def send_msg(self, action, play=None, msg=None):
        message = json.dumps({
            "action": action,
            "payload": play,
            "message": msg,
            "player_id": self.identifier
        })

        self.sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_tcp.connect(self.server_tcp)
        """
        If the action is test then the client sends a message 50000 amounts to the server
        to measure how long it takes for the messages to arrive. The sleep is so that the
        server can prepare to accept messages.
        """
        if action == 'test':
            self.sock_tcp.send(message.encode())
            time.sleep(1)
            for i in range(50000):
                self.sock_tcp.send(message.encode())
            self.sock_tcp.close()
        else:
            self.sock_tcp.send(message.encode())
            data = self.sock_tcp.recv(1024)
            self.sock_tcp.close()
            message = self.parse_data(data)

        print(message)

    """
    Parses messages from the server if the succes code is True. If not raises an Exception
    """

    def parse_data(self, data):
        try:
            data = json.loads(data)
            if data['success'] == "True":
                return data['message']
            else:
                raise Exception(data['message'])
        except ValueError:
            print(data)
    """
    Gets servers messages to print
    """
    def get_messages(self):

        message = self.server_message
        self.server_message = []
        return set(message)


class SocketThread(Thread):

    """
    Initializes SocketThread which is used to listen to the servers messages.
    Initialized with servers address.
    """
    def __init__(self, client, client_port, server_tcp, lock):

        Thread.__init__(self)
        self.client = client
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", int(client_port)))
        self.lock = lock
        self.time_reference = time.time()

    """
    Recieves messages from the server and then prints them
    """

    def run(self):

        while True:
            data, addr = self.sock.recvfrom(1024)
            self.lock.acquire()
            try:
                self.client.server_message.append(data)
                self.print_messages()
            finally:
                self.lock.release()

    def print_messages(self):

        messages = client.get_messages()
        if len(messages) != 0:
            for message in messages:
                message = json.loads(message)
                sender, value = message.popitem()
                print(sender, " : ", value)

"""
Initializes the client and log-array. If a port isn't supplied as an arg it defaults to port 9999.
Waits for messages that are used for the application from the user.
"""

if __name__ == '__main__':

    log = []

    if sys.argv[1]:
        client = Client(sys.argv[1])
    else:
        client = Client(9999)

    print("Join a game with 'join' \n"
          "Send a play with 'play <num>' \n"
          "1 = rock, 2 = paper, 3 = scissors \n"
          "Send a message with 'msg <message>'\n"
          "Send a play and message with 'pmsg <num> <message> \n"
          "Print the log of this session with 'log' \n"
          "Test the network with 50000 messages with 'test'")

    while True:
        cmd = input('> ')

        if cmd.startswith('join'):
            client.send_msg('join')
            log.append(('join'))
        elif cmd.startswith('play'):
            client.send_msg('play', cmd[5:].strip())
            log.append(('play', cmd[5:].strip()))
        elif cmd.startswith('msg'):
            client.send_msg('msg', None, cmd[4:])
            log.append(('message', cmd[4:]))
        elif cmd.startswith('pmsg'):
            client.send_msg('pmsg', cmd[5:6], cmd[6:])
            log.append(('play and message', cmd[5:6], cmd[6:]))
        elif cmd.startswith('log'):
            for entry in log:
                print(entry)
        elif cmd.startswith('test'):
            client.send_msg('test')
        else:
            print('Invalid command')
