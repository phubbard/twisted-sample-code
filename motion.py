#!/usr/bin/env python

'''
@author Paul Hubbard
@date 1/26/11
@brief Try and wrap the motion/unimotion executable as a Twisted process
@see http://twistedmatrix.com/documents/current/core/howto/process.html
@see http://ifiddling.blogspot.com/2009/01/dummy2.html
@see http://unimotion.sourceforge.net/
@see http://twistedmatrix.com/documents/current/core/howto/clients.html
'''

from twisted.internet import reactor, protocol
from twisted.internet.endpoints import TCP4ClientEndpoint

import logging as log

DEST_ADDR = 'localhost'
DEST_PORT = 9997

class Sender(protocol.Protocol):
    def sendMessage(self, msg):
        if len(msg) != 3:
            return
        outbound_msg = 'x: %f y: %f z: %f\n' % (msg[0], msg[1], msg[2])
        self.transport.write(outbound_msg)

class MotionProcessProtocol(protocol.ProcessProtocol):
    def gotProtocol(self, p):
        self.p = p
        log.debug('got protocol')
        p.sendMessage(self.data)

    def noProtocol(self, failure):
        log.critical('Error getting outbound TCP connection: %s' % str(failure))

    def connectionMade(self):
        self.data = []
        log.debug('Connected, opening outbound connection')
        factory = protocol.Factory()
        factory.protocol = Sender
        point = TCP4ClientEndpoint(reactor, DEST_ADDR, DEST_PORT)
        d = point.connect(factory)
        d.addCallback(self.gotProtocol)
        d.addErrback(self.noProtocol)

    def outReceived(self, data):
        log.info('got "%s"' % data.strip())

        data = map(float, data.strip().split())
        if len(data) != 3:
            log.debug('Only got %d values, skipping' % len(data))
            return

        if hasattr(self, 'p'):
            self.p.sendMessage(data)

if __name__ == '__main__':
    log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s [%(funcName)s] %(message)s')
    mp = MotionProcessProtocol()
    reactor.spawnProcess(mp, 'motion', ['-f', '100'])
    reactor.run()
