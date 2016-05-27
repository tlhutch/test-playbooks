import re
import sys
import time
import random
import logging

import fauxfactory

log = logging.getLogger(__name__)


class NoReloadError(Exception):
    pass


class Struct(object):
    """Simple data structure that does kwargs->attr binding on initialization
    """
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

def wait_until(obj, att, desired, callback=None, interval=5, attempts=0, timeout=0, start_time=None, verbose=False, verbose_atts=None):
    '''
    When changing the state of an object, it will commonly be in a transitional
    state until the change is complete. This will reload the object every
    `interval` seconds, and check its `att` attribute until the `desired` value
    is reached, or until the maximum number of attempts is reached. The updated
    object is returned. It is up to the calling program to check the returned
    object to make sure that it successfully reached the desired state.

    Once the desired value of the attribute is reached, the method returns. If
    not, it will re-try until the attribute's value matches one of the
    `desired` values. By default (attempts=0) it will loop infinitely until the
    attribute reaches the desired value. You can optionally limit the number of
    times that the object is reloaded by passing a positive value to
    `attempts`. If the attribute has not reached the desired value by then, the
    method will exit.

    Alternatively, a maximum `timeout` (in seconds) can be provided.  If the
    desired outcome is not realized within the provided `timeout`, the method
    returns.  The `timeout` begins when the method is called.  An alternative
    `start_time` can be provided.

    If `verbose` is True, each attempt will print out the current value of the
    watched attribute and the time that has elapsed since the original request.
    Also, if `verbose_atts` is specified, the values of those attributes will
    also be output. If `verbose` is False, then `verbose_atts` has no effect.

    Note that `desired` can be a list of values; if the attribute becomes equal
    to any of those values, this will succeed. For example, when creating a new
    cloud server, it will initially have a status of 'BUILD', and you can't
    work with it until its status is 'ACTIVE'. However, there might be a
    problem with the build process, and the server will change to a status of
    'ERROR'. So for this case you need to set the `desired` parameter to
    `['ACTIVE', 'ERROR']`. If you simply pass 'ACTIVE' as the desired state,
    this will loop indefinitely if a build fails, as the server will never
    reach a status of 'ACTIVE'.

    Since this process of waiting can take a potentially long time, and will
    block your program's execution until the desired state of the object is
    reached, you may specify a callback function. The callback can be any
    callable that accepts a single parameter; the parameter it receives will be
    either the updated object (success), or None (failure). If a callback is
    specified, the program will return immediately after spawning the wait
    process in a separate thread.
    '''
    if callback:
        raise NotImplementedError("Coming soon!")
        # waiter = _WaitThread(obj=obj, att=att, desired=desired, callback=callback,
        #          interval=interval, attempts=attempts, verbose=verbose,
        #          verbose_atts=verbose_atts)
        # waiter.start()
        # return waiter
    else:
        return _wait_until(obj=obj, att=att, desired=desired, callback=None,
                           interval=interval, attempts=attempts, timeout=timeout,
                           start_time=start_time, verbose=verbose, verbose_atts=verbose_atts)


def _wait_until(obj, att, desired, callback, interval, attempts, timeout, start_time, verbose, verbose_atts):
    '''
    Loops until either the desired value of the attribute is reached, or the
    number of attempts is exceeded.
    '''
    assert hasattr(obj, 'get'), "The provided object (%s) does not support a 'get' method" % obj.__class__

    if not isinstance(desired, (list, tuple)):
        desired = [desired]
    if verbose_atts is None:
        verbose_atts = []
    if not isinstance(verbose_atts, (list, tuple)):
        verbose_atts = [verbose_atts]
    infinite = (attempts == 0)
    attempt = 0

    # Initialize start_time (if provided)
    if start_time is None:
        start_time = time.time()
    elif isinstance(start_time, time.struct_time):
        start_time = time.mktime(start_time)
        # Adjust for timezone/daylight savings offset
        if time.localtime().tm_isdst and time.daylight:
            start_time -= time.altzone
        else:
            start_time -= time.timezone
        log.debug("start_time: %s (%s)" % (time.ctime(start_time), start_time))

    while infinite or (attempt < attempts):
        obj.get()
        attval = getattr(obj, att)
        elapsed = time.time() - start_time
        if verbose:
            _print_state(obj, att, attval, elapsed, verbose_atts)

        if attval in desired:
            return obj

        if timeout and elapsed > timeout:
            _print_state(obj, att, attval, elapsed, verbose_atts)
            break

        time.sleep(interval)
        attempt += 1
    return obj


def _print_state(obj, att, attval, elapsed, verbose_atts):
    msgs = ["Current value of %s: %s (elapsed: %4.1f seconds)" % (
            att, attval, elapsed)]
    for vatt in verbose_atts:
        vattval = getattr(obj, vatt, None)
        msgs.append("%s=%s" % (vatt, vattval))
    log.debug(" ".join(msgs))


def random_int(maxint=sys.maxint):
    max = int(maxint)
    return random.randint(0, max)


def random_ipv4():
    """
    Generates a random ipv4 address;; useful for testing.
    """
    return ".".join(str(random.randint(1, 255)) for i in range(4))


def random_ipv6():
    """
    Generates a random ipv6 address;; useful for testing.
    """
    return ':'.join('{0:x}'.format(random.randint(0, 2 ** 16 - 1)) for i in range(8))


def random_loopback_ip():
    """
    Generates a random loopback ipv4 address;; useful for testing.
    """
    return "127.{}.{}.{}".format(random_int(255), random_int(255), random_int(255))


def random_utf8(*args, **kwargs):
    """This function exists due to a bug in ChromeDriver that throws an
    exception when a character outside of the BMP is sent to `send_keys`.
    Code pulled from http://stackoverflow.com/a/3220210.
    """
    pattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
    scrubbed = pattern.sub(u'\uFFFD', fauxfactory.gen_utf8(*args, **kwargs))

    return scrubbed
