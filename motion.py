#!/usr/bin/env python

'''
@author Paul Hubbard
@date 1/26/11
@brief Try and wrap the motion/unimotion executable as a Twisted process
@see http://twistedmatrix.com/documents/current/core/howto/process.html
@see http://ifiddling.blogspot.com/2009/01/dummy2.html
@see http://unimotion.sourceforge.net/
@see http://twistedmatrix.com/documents/current/core/howto/clients.html

@note Run 'nc -l 9997' in another window to provide a TCP server and display.
'''

from twisted.internet import reactor, protocol
from twisted.internet.endpoints import TCP4ClientEndpoint

import logging as log

# Where we'll stream the data
DEST_ADDR = 'localhost'
DEST_PORT = 9997

# Update rate, milliseconds. 100 = 10Hz
UPDATE_DELAY_MSEC = 1000

class Sender(protocol.Protocol):
    """
    This handles sending the data to the TCP server.
    """
    def sendRawMessage(self, msg):
        self.transport.write(msg)

    def sendMessage(self, msg):
        if len(msg) != 3:
            return
        outbound_msg = 'x: %f y: %f z: %f\n' % (msg[0], msg[1], msg[2])
        self.transport.write(outbound_msg)

class MotionProcessProtocol(protocol.ProcessProtocol):
    def gotProtocol(self, p):
        """
        Callback from TCP4 endpoint. Saves the protocol instance for later.
        """
        self.p = p
        log.debug('got protocol')

    def noProtocol(self, failure):
        """
        Errback from TCP4 endpoint, called if we get a connection error.
        """
        log.error('Error getting outbound TCP connection: %s' % str(failure))
        del self.p

    def open_outbound(self):
        log.debug('Connected, opening outbound connection')
        factory = protocol.Factory()
        factory.protocol = Sender
        point = TCP4ClientEndpoint(reactor, DEST_ADDR, DEST_PORT)
        d = point.connect(factory)
        d.addCallback(self.gotProtocol)
        d.addErrback(self.noProtocol)

    def connectionMade(self):
        """
        Callback for connecting to the spawned 'motion' process. Starts
        a connection to the TCP server to send the data out.
        """
        self.data = []
        self.open_outbound()

    def outReceived(self, data):
        """
        This is called when the motion app prints out data. Format is 3 floats, string
        format, with a space inbetween. easy to parse.
        """
        log.info('got "%s"' % data.strip())

        data = map(float, data.strip().split())
        if len(data) != 3:
            log.debug('Only got %d values, skipping' % len(data))
            return

        # If we have a connection, send the data on
        if hasattr(self, 'p'):
            self.p.sendMessage(data)
        else:
            self.open_outbound()

if __name__ == '__main__':
    log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s [%(funcName)s] %(message)s')
    mp = MotionProcessProtocol()
    reactor.spawnProcess(mp, 'motion', ['-f', str(UPDATE_DELAY_MSEC)])
    reactor.run()
