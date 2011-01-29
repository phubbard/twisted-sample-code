
from twisted.internet import reactor
from twisted.internet import protocol

class ExampleProtocol(protocol.Protocol):
    """
    There are three methods you can implement for protocol.Protocol
    subclasses:
     * connectionMade
     * connectionLost
     * dataReceived 

    See the official documentation here:
    http://twistedmatrix.com/documents/current/api/twisted.internet.protocol.Protocol.html
    """

    def connectionMade(self):
        print "connection made"

    def connectionLost(self, reason):
        print "connection lost!", reason

    def dataReceived(self, data):
        print "dataReceived:"
        print data


def main():
    """
    The ultimate goal in network programming is communication.
    Protocols are the end points that do the talking.
    The transport is the medium they communicate through.
    
    The Twisted Protocol has everything to do with what is communicated
    (data formats, encodings, etc.) and nothing to do with how connections
    are made (host addresses, ports, etc.). 

    Protocols are only instantiated when a connection is made.
    An instance of a protocol can only be used for the duration of one
    connection -- a protocol is not something to store application
    state in.

    Connections are started using the reactor api.
    The reactor.listenTCP method creates a listening tcp port: a server.
    The reactor.connectTCP method creates a connection to a port: a client.

    The Protocol Factory binds a Protocol class to a transport connection.
    The Protocol Factory's job is to build a Protocol instance the moment a
    connection is opened.
    A Protocol Factory is a good place to hold application state.
    All Protocol instances have a reference to the factory that created
    them.

    (Note: You should *NEVER* create a connection using the socket library
    yourself; Twisted uses the socket library under the covers and it
    handles the socket calls for you).
    """
    # Create a generic factory instance
    f = protocol.Factory() 

    # We want this factory to build instances of our ExampleProtocol class
    # Set the protocol attribute of the factory to be ExampleProtocol (just
    # the class, not an instance)
    f.protocol = ExampleProtocol 

    # Bind the factory to tcp port 8000 and
    reactor.listenTCP(8000, f) 
    # start listening
    # The factory will now create a new instance
    # of ExampleProtocol whenever a connection
    # is made to port 8000

if __name__ == "__main__":
    main()
    reactor.run()

