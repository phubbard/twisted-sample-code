#!/usr/bin/env python

"""
A Twisted service
A simple api to change the color of a light
"""

import string
import logging

from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols import basic


RED = 'zaa'
GREEN = 'aza'
BLUE = 'aaz'
WHITE = 'zzz'
BLACK = 'aaa'


class Device(object):
    """
    the service
    """

    def __init__(self, hostname='ooi-arduino.ucsd.edu', port=80):
        self.hostname = hostname
        self.port = port
        self.temp = None
        self.humidity = None
        self.color = WHITE

    def set_colorRGB(self, r, g, b):
        """
        """
        scale = string.ascii_letters

        rgb = "%s%s%s" % tuple([scale[int(abs(c)) % 52] for c in (r,g,b,)])
        print 'RGB', rgb
        return self.set_color(rgb)

    def set_color(self, rgb):
        """
        """

        self.color = rgb

        def success(client):
            return True

        def fail(reason):
            return False

        d = self._connect()
        d.addCallback(success)
        d.addErrback(fail)
        return d

    def get_data(self):

        def _return_data(client):
            return client.deferred

        d = self._connect()
        d.addCallback(_return_data)
        return d

    def _connect(self):
        client_creator = protocol.ClientCreator(reactor, ArduinoClient, self.color)
        d = client_creator.connectTCP(self.hostname, self.port)
        d.addErrback(self._connect_err)
        return d

    def _connect_err(self, reason):
        logging.debug('Connection Error %s' % (reason,))
        return reason


class ArduinoClient(basic.LineReceiver):

    def __init__(self, color=WHITE):
        """
        color value to set light to
        """
        self._color = color
        self.lastTemp = None
        self.lastRH = None
        self.deferred = defer.Deferred()

    def connectionMade(self):
        #global current_color
        logging.info('Connected! Sending color ' + self._color)
        self.transport.write(self._color + '\n')

    def lineReceived(self, line):
        logging.info('sensor data: "%s"' % line)
        data = line.split()
        self.processData(data)
        self.transport.loseConnection()

    def processData(self, data):
        """Convert raw ADC counts into SI units as per datasheets"""
        # Skip bad reads
        if len(data) != 2:
            return

        tempCts = int(data[0])
        rhCts = int(data[1])

        rhVolts = rhCts * 0.0048828125

        # 10mV/degree, 1024 count/5V
        temp = tempCts * 0.48828125
        # RH temp correction is -0.7% per deg C
        rhcf = (-0.7 * (temp - 25.0)) / 100.0

        # Uncorrected humidity
        humidity = (rhVolts * 45.25) - 42.76

        # Add correction factor
        humidity = humidity + (rhcf * humidity)

        self.lastTemp = temp
        self.lastRH = humidity
        self.deferred.callback((temp, humidity,))

        logging.info('Temp: %f C Relative humidity: %f %%' % (temp, humidity))
        logging.debug('Temp: %f counts: %d RH: %f counts: %d volts: %f' % (temp, tempCts, humidity, rhCts, rhVolts))






