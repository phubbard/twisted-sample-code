#!/usr/bin/env python

"""
Collection of demonstrations using the arduino and motion modules.

Note: I'm still not sure on the final form of the example functions, but
the content is progressing.
The goal is to make the tests easy to run, and maybe interact with while
minimizing fanciness and hackyness.
"""
from twisted.internet import reactor
from twisted.web import resource
from twisted.web import server

import motion
import arduino

WEB_PORT = 8000

#################################################################
## Extra Demonstration Code
## These supplement motion and arduino
## Each module implements simple core functionality
## This demonstration code shows different ways to present the core
## functionality over different network protocols, and or combines different
## functionalities.

class DeviceControlPage(resource.Resource):

    def __init__(self, device):
        resource.Resource.__init__(self)
        self.device = device
        self.putChild('demo', self)

    def render_GET(self, request):
        """
        """
        d = self.device.get_data()
        d.addCallback(self._finish_response, request)
        d.addErrback(self._err_get)
        return server.NOT_DONE_YET

    def _finish_response(self, (temp, humidity,), request):
        request.write("""
<html>
  <head>
    <title>Arduino Device Control Demonstration</title>
  </head>
  <body>
    <h1>Weather Station</h1>
    <h2>Light Control</h2>
      <form method='post'>
        <input type='text' name='color' value='%s'>
        <input type='submit' value='Set Color'>
      </form>
    <h2>Current Observations</h2>
      <ul>
        <li>Temperature: %f C</li>
        <li>Humidity: %f </li>
      </ul>
  </body>
</html>
        """ % (self.device.color, temp, humidity,))
        request.finish()

    def _err_get(self, reason):
        print 'ERR'
        print reason


    def render_POST(self, request):
        color = request.args.get('color', ['rgb'])[0]
        d = self.device.set_color(color)
        request.redirect('/demo')
        return ''


def test_web():
    device = Device()
    site = server.Site(LightControl(device))
    port = reactor.listenTCP(8888, site)


class MotionToLight(motion.MotionProcessProtocol):

    def __init__(self, device):
        self.device = device

    def motionReceived(self, motion):
        self.device.set_colorRGB(*map(int, motion))


#######################################################
## Demonstration scripts

def demo1():
    """
    Arduino Device (driver? or adapter?)
    This demonstrates how a arduino.Device instance is simply an object
    that represents a physical device.
    The arduino device has a temperature sensor, a humidity sensor, and a
    controllable multi-color LED

    The arduino.Device has these api methods:
     * set_color - this controls the LED light
     * get_data - this fetches a sample from the sensors

    Both methods of the api return Deferred instances.
    The Deferred returned by set_color will callback with a bool indicating
    success or failure of setting the color.

    The Deferred returned by get_data will callback with a two-tuple of
    sensor data (temperature, humidity,)
    
    Instances of arduino.Device actually communicate to the physical
    device, so can only run in an environment where connectivity to the
    device is available.
    """
    device = arduino.Device()

    def print_cb(result, fun_name):
        """Add this as a callback handler to Deferred objects returned by
        the device.
        """
        print "Callback for %s: " % (fun_name,)
        print result

    def print_eb(reason):
        """Add this as an errback handler to Deferred objects returned by
        the device.
        """
        print "Errback for %s: " % (fun_name,)
        print reason

    # api call example 1
    d1 = device.get_data()
    d1.addCallback(print_cb, 'get_data')
    d1.addErrback(print_eb, 'get_data')

    # api call example 2
    d2 = device.set_color('aaa') # white
    d2.addCallback(print_cb, 'set_color')
    d2.addErrback(print_eb, 'set_color')

    # api call example 3
    d3 = device.set_color('aaZ') # blue
    d3.addCallback(print_cb, 'set_color')
    d3.addErrback(print_eb, 'set_color')



def demo2():
    """
    Present device object as web resource

    Run this demo and use a web browser to view:
    http://localhost:8000/demo

    """
    device = arduino.Device()
    site = server.Site(DeviceControlPage(device))
    port = reactor.listenTCP(WEB_PORT, site)

def demo3():
    """
    Laptop Motion Sensor

    Demonstrates how an external program can be invoked and monitored by
    Twisted. Motion is a program that writes samples of the accelerometer 
    inside the MacBook to stdout. 
    Twisted treats the stdin/out of a process just like any other
    transport.
    The twisted Process Protocol receives the write events on the outReceived 
    method

    The MotionProcessProtocol will log the data samples when they occur.
    """
    motionProcess = motion.MotionProcessProtocol()
    motion.spawnProcess(reactor, motionProcess)

def demo4():
    """
    Integrate the motion sensor and the Arduino device light!

    This demo uses both an arduino.Device object and a motion process.
    The x, y, and z components of the accelerometer data are mapped to the
    r, g, and b components of the LED on the arduino device. The result is
    the ability to change the LED color by moving your laptop around.

    The MotionToLight extends the MotionProcessProtocol. The motionReceived
    event handler calls the set_color method of the arduino device every
    time it gets a new accelerometer sample.

    """
    device = arduino.Device()
    motionProcess = MotionToLight(device)
    motion.spawnProcess(reactor, motionProcess, 250)
