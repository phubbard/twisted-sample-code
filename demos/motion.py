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
from twisted.internet.protocol import DatagramProtocol
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.python import usage

import logging as log
import sys
import time

# Command line flags and associated default values
class MOptions(usage.Options):
    optParameters = [
    ['port', 'p', 9997, 'Destination TCP port for data stream'],
    ['host', 'h', 'localhost', 'Destination hostname or IP'],
    ['interval', 'i', 100, 'Polling interval, milliseconds'],
    ]

class GraphiteSender(DatagramProtocol):
    def startProtocol(self):
        log.debug('Connecting udp')
        #self.transport.connect('127.0.0.1', 2003)
        log.debug('udp done')

    def datagramReceived(self, datagram, host):
        log.warn('got unexpected packet')

    def connectionRefused(self):
        log.error('connection refused!')

    def sendDatagram(self, msg):
        # Assuming that msg is an 3-array of floats, x-z
        now = int(time.time())
        lines = []
        lines.append('paul.accel.x %s %d' % (msg[0], now))
        lines.append('paul.accel.y %s %d' % (msg[1], now))
        lines.append('paul.accel.z %s %d' % (msg[2], now))
        message = '\n'.join(lines) + '\n' #all lines must end in a newline

        log.debug('sending udp packet "%s"' % message)
        self.transport.write(message, ('127.0.0.1', 2003))

class Sender(protocol.Protocol):
    """
    This handles sending the data to the TCP server.
    """
    def sendRawMessage(self, msg):

        self.transport.write(msg)
        self.transport.write('\n')

    def sendMessage(self, msg):
        if len(msg) != 3:
            return
        outbound_msg = 'x: %f y: %f z: %f\n' % (msg[0], msg[1], msg[2])
        self.transport.write(outbound_msg)

class MotionProcessProtocol(protocol.ProcessProtocol):
    """
    A Python wrapper (twisted protocol) around the monitor program.
    """

    def outReceived(self, data):
        """
        This is called when the motion app prints out data. Format is 3 floats, string
        format, with a space inbetween. easy to parse.
        """
        motion = map(float, data.strip().split())
        if len(motion) != 3:
            log.debug('Only got %d values, skipping' % len(motion))
            return
        self.motionReceived(motion)

    def motionReceived(self, motion):
        """
        Implement this event handler in your application.

        @param motion tupple of force values (x,y,z)
        """
        log.info('got "%s"' % str(motion))

class UDPProducingClient(MotionProcessProtocol):
    """
    Send data to Graphite instead of labview.
    """
    def connectionMade(self):
        self.gs = GraphiteSender()
        self.graphite_connection = reactor.listenUDP(0, self.gs)

    def motionReceived(self, motion):
        log.debug('got "%s"' % str(motion))

        self.gs.sendDatagram(motion)

class TCPProducingClient(MotionProcessProtocol):
    """
    This subclass of MPP adds hooks to repeatedly try and open an outbound (client)
    TCP connection where we'll stream the data. Try

    nc -l 9997

    or, if you have LabVIEW, the 'LV Client.vi' for a live data viewer.
    """

    def __init__(self, hostname, portnum):
        self.hostname = hostname
        self.portnum = portnum

    def connectionMade(self):
        """
        Callback for connecting to the spawned 'motion' process. Starts
        a connection to the TCP server to send the data out.
        """
        self.open_outbound()

    def motionReceived(self, motion):
        # If we have a connection, send the data on
        if hasattr(self, 'p'):
            self.p.sendMessage(motion)
        else:
            self.open_outbound()

        log.debug('got "%s"' % str(motion))


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
        log.debug('Error getting outbound TCP connection: %s' % str(failure))

    def open_outbound(self):
        log.debug('Connected, opening outbound connection')
        factory = protocol.Factory()
        factory.protocol = Sender
        point = TCP4ClientEndpoint(reactor, self.hostname, self.portnum)
        d = point.connect(factory)
        d.addCallback(self.gotProtocol)
        d.addErrback(self.noProtocol)


def spawnProcess(reactor, processProtocol, interval):
    """
    Nifty Twisted trick - spawn a process, and hook its stdout into a Protocol.
    """
    return reactor.spawnProcess(processProtocol,
                                'motion',
                                ['-f', str(interval)]
                                )


if __name__ == '__main__':
    log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s [%(funcName)s] %(message)s')

    o = MOptions()
    try:
        o.parseOptions()
    except usage.UsageError, etaxt:
        log.error('%s %s' % (sys.argv[0], errortext))
        log.info('Try %s --help for usage details' % sys.argv[0])
        raise SystemExit, 1

    #mp = TCPProducingClient(o.opts['host'], o.opts['port'])
    mp = UDPProducingClient()
    spawnProcess(reactor, mp, o.opts['interval'])
    reactor.run()
