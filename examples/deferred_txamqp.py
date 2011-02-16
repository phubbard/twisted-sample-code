"""
A simple example showing the utility of a deferred.

A client waiting for a response? (pretty straight forward, good for example)

A client waiting for a connection? (maybe to complicated to explain)
"""
import os
import time
from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet import task
from twisted.application import service

from txamqp import spec
from txamqp.content import Content
from txamqp.client import TwistedDelegate
from txamqp.protocol import AMQClient
from txamqp.queue import TimeoutDeferredQueue

SPEC_PATH = os.path.abspath('amqp0-8.xml') # assume the demo is run in place


# Example of sending a batch of messages.
#
# In general, the batch can be thought of as an iterable, or a generator.
# Twisted provides a mechanism to iterate over these batches in a safe
# way in the twisted.task module. The operation to be repeated doesn't have
# to return a deferred. In fact, it is more likely the case that the
# operation isn't deferred, and that's why you need the task Cooperator in
# the first place.

def send_messages(chan, msg_size, ex_type):
    def message_iterator():
        global count
        global start_time
        count = 0
        start_time = time.time()
        loop = task.LoopingCall(msg_rate)
        loop.start(1)
        while True:
            count += 1
            #content = 'Message %d' % (count,)
            content = 'x' * msg_size
            msg = Content(content)
            chan.basic_publish(exchange=ex_type, content=msg, routing_key='foo')
            yield None
    return task.cooperate(message_iterator())


def msg_rate():
    elapsed_time = time.time() - start_time
    rate = count /elapsed_time 
    print '%s msg/sec' %(str(rate),)


####################################################
# txamqp boiler plate

def createClient(host='localhost', port=5672):
    """
    Typical setup procedure for txamqp
    """

    spec_path = os.path.abspath('amqp0-8.xml') # assume the demo is run in place
    spec_file = spec.load(spec_path)

    username = 'guest'
    password = 'guest'
    vhost = '/'

    delegate = TwistedDelegate()

    def authenticate(conn, username, password):
        """this is a callback handler that returns a deferred
        """
        d = conn.authenticate(username, password)
        d.addCallback(lambda _: conn)
        d.addErrback(handle_error)
        return d

    def handle_error(reason):
        """
        do something useful with the error
        """
        reason.printTraceback()
        return reason

    client_creator = protocol.ClientCreator(reactor, 
                                            AMQClient, 
                                            delegate=delegate, 
                                            vhost=vhost,
                                            spec=spec_file)
    d = client_creator.connectTCP(host, port)
    d.addCallback(authenticate, username, password)
    d.addErrback(handle_error)
    return d


def main(msg_size, ex_type):
    global count
    global start_time
    @defer.inlineCallbacks
    def gotClient(client):
        chan = yield client.channel(1)
        yield chan.channel_open()
        defer.returnValue(chan)
    d = createClient('amoeba.ucsd.edu')
    d.addCallback(gotClient)
    d.addCallback(send_messages, msg_size, ex_type)


if __name__ == '__main__':
    main(10000, 'amq.direct')
    reactor.run()
