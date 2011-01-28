"""
Shows what happens if 'False' is returned by dataReceived.

Note: Don't return a Deferred! It will be ignored by the framework!
"""

from twisted.internet import reactor
from twisted.internet import protocol

class ExampleProtocol(protocol.Protocol):

    def connectionMade(self):
        """
        Send a prompt as soon as the connection is opened.
        """
        print "connection made"
        self.transport.write("\nType something, will you? We're paying for this stuff:\n")

    def connectionLost(self, reason):
        """
        """
        print "connection lost!"
        print reason

    def dataReceived(self, data):
        """
        Returning 'True' results in the disconnection of the connection.

        This is never treated as a Deferred function, so you should not
        return a deferred here, nor should you decorate with
        inlineCallbacks.
        """
        print "dataReceived:"
        print data
        # The following 'write' never actually occur because returning True
        # disconnects the file descriptor instantly!
        self.transport.write('Received your data: %s\n' % data)
        return True # This tells the reactor to disconnect!

def main():
    """
    Run this demo and interact with it via telnet:

    $ telnet localhost 8000

    Type something and hit enter.
    """
    f = protocol.Factory()
    f.protocol = ExampleProtocol

    reactor.listenTCP(8000, f)
    return f

if __name__ == "__main__":
    main()
    reactor.run()

