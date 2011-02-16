"""
Getting to know deferreds.

Rules of thumb:
    - minimize inlineCallbacks usage
    - never except the plain Exception class
    - always set up proper error handling
    - understand how errbacks relate to exceptions with inlineCallbacks

"""
import sys

from twisted.internet import defer
from twisted.internet import reactor
from twisted.python import failure
from twisted.web import client


########################################
# Basic example without errback handling 

def demo1(url):
    """Get a web page (e.g. http://ooici.net).
    """
    d = client.getPage(url)
    d.addCallback(print_page)
    return d

def print_page(page):
    """I am a callback that the deferred will call as soon as it gets the
    page.
    """
    print page

# ---------------------------------------

@defer.inlineCallbacks
def demo2(url):
    """The same as demo1, but using inlineCallbacks
    """
    page = yield client.getPage(url)
    print page


####################################

@defer.inlineCallbacks
def bad_example(url):
    """This is an unnecessary use of inlineCallbacks
    """
    page = yield client.getPage(url)
    defer.returnValue(page)

##################################
# Exceptions and Errbacks


# ...... callbacks ........

def success_handler(result):
    print 'Success!'

def failure_handler(reason):
    print reason.value

# .........................

def return_failure():
    """I return a deferred that always fails.
    """
    d = defer.Deferred()
    d.errback(failure.Failure("I'm a failure :-(", TypeError))
    return d


def fail_example():
    """I demonstrate a properly handled error
    """
    d = return_failure()
    d.addCallback(success_handler)
    d.addErrback(failure_handler)
    return d

@defer.inlineCallbacks
def inline_fail_example():
    """inlineCallbacks version of fail_example.
    Error is handled.
    """
    try:
        ans = yield return_failure()
    except TypeError, e:
        print 'I failed. fml'
    defer.returnValue(None)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def call_inline_fail_example():
    """Because the TypeError is handled in the inline_fail_example, the
    result of inline_fail_example is actually a success.
    """
    d = inline_fail_example()
    d.addCallback(success_handler)
    d.addErrback(failure_handler)
    return d
# ------------------------------------------------------

@defer.inlineCallbacks
def inline_fail_example_return_fail():
    """inlineCallbacks version of fail_example that does NOT handle the
    error (a TypeError is raised by return_failure; but here, a KeyError is
    excepted on).
    """
    try:
        ans = yield return_failure()
    except KeyError, e:
        print 'I failed. fml'

def call_inline_fail_example_return_fail():
    """Because TypeError is NOT handled in the inline_fail_example_return_fail,
    the result is a failure!
    """
    d = inline_fail_example_return_fail()
    d.addErrback(failure_handler)
    return d


###############################################
# Trigger deferred, and watch how it works!
# 
# Observe that a function decorated with defer.inlineCallbacks ALWAYS
# returns a deferred object, even if there is no deferred yielded, as is
# in the none() function.

@defer.inlineCallbacks
def give_me_a_deferred(d):
    result = yield d
    defer.returnValue(result)

# Do this in the ayps shell:
# d = defer.Deferred()
# ans = give_me_a_deferred(d)
# type(ans) # the function returns a deferred
# d.callback('ftw!')
# ans.result

@defer.inlineCallbacks
def none():
    """This doesn't yield on a deferred, but it works.
    """
    yield (None)
    defer.returnValue(42)

#####################################

if __name__ == '__main__':
    url = sys.argv[1]
    d = demo1(url)
    d.addCallback(lambda _: reactor.stop())
    reactor.run()
