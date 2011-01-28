
from twisted.internet import reactor
from twisted.internet import protocol

class NotHTTP(protocol.Protocol):

    def connectionMade(self):
        """
        """
        print "connection made"

    def connectionLost(self, reason):
        """
        """
        print "connection lost!"
        print reason

    def dataReceived(self, data):
        """
        """
        print "dataReceived:"
        print data
        #self.transport.write('Hello, do you speak newb?\r\n')
        #self.transport.loseConnection()

class FrankenFactory(protocol.Factory):

    def buildProtocol(self, addr):
        p = protocol.Factory.buildProtocol(self, addr)
        self.lastp = p
        return p

def main():
    #f = protocol.Factory()
    f = FrankenFactory()
    f.protocol = NotHTTP

    reactor.listenTCP(8000, f)
    return f

if __name__ == "__main__":
    main()
    reactor.run()

