#!/usr/bin/env python

from junitparser import JUnitXml


import sys

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

#following from Python cookbook, #475186
def has_colours(stream):
    if not hasattr(stream, "isatty"):
        return False
    if not stream.isatty():
        return False # auto color only on TTYs
    try:
        import curses
        curses.setupterm()
        return curses.tigetnum("colors") > 2
    except:
        # guess false in case of error
        return False
has_colours = has_colours(sys.stdout)


def printout(text, colour=WHITE):
        if has_colours:
                seq = "\x1b[1;%dm" % (30+colour) + text + "\x1b[0m"
                sys.stdout.write(seq)
        else:
                sys.stdout.write(text)

failed = []
success = []

xml = JUnitXml.fromfile('./reports/junit/results.xml')
for test in xml:
    if test.result and test.result._tag == 'failure':
        failed.append(test)
    else:
        success.append(test)


for test in success:
    printout("[success] ", GREEN)
    print(u"{}::{}".format(test.classname, test.name))


for test in failed:
    printout("[failed] ", RED)
    print(u"{}::{}\n{}\n".format(test.classname, test.name, test.result.message))

