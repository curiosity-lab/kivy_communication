#install_twisted_rector must be called before importing the reactor
from kivy.support import install_twisted_reactor
install_twisted_reactor()
#A simple Client that send messages to the echo server
from twisted.internet import reactor, protocol


class EchoClient(protocol.Protocol):

    def __init__(self):
        pass

    def connectionMade(self):
        self.factory.client.on_connection(self.transport)

    def dataReceived(self, data):
        self.factory.client.print_message(data)


class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

    def __init__(self, client):
        self.client = client

    def clientConnectionLost(self, conn, reason):
        self.client.print_message("connection lost")

    def clientConnectionFailed(self, conn, reason):
        self.client.print_message("connection failed")


class TwistedClient:
    connection = None
    parent = None
    ip = None

    def __init__(self, the_parent=None, the_ip=None):
        self.parent = the_parent
        self.ip = the_ip

    def connect_to_server(self, the_ip=None):
        if the_ip:
            self.ip = the_ip
        if self.ip:
            self.print_message('connecting...')
            reactor.connectTCP(the_ip.text, 8000, EchoFactory(self))
        else:
            self.print_message('missing ip!')

    def on_connection(self, connection):
        self.print_message("connected successfully!")
        self.connection = connection

    def send_message(self, *args):
        try:
            msg = args[0]
            if msg and self.connection:
                self.connection.write(msg)
        except:
            self.print_message('incorrect message')

    def print_message(self, msg):
        if self.parent:
            try:
                self.parent.print_message(msg)
                return
            except:
                pass
        print("message: ", msg)