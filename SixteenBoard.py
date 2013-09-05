#!/usr/bin/env python
import serial, re, time
from sixteensegfont import font

#
# the bit order is different on the hardware due to the order of the
# bits in the shift registers
#  
def mangle(c):
    mangled = "{0:04x}".format(c)
    #        last nibble -> first
    #        first -> last
    #        middle 2 swap
    #        3210    3210
    #        c387 -> 783c
    return "%c%c%c%c" % (mangled[3], mangled[2], mangled[1], mangled[0])


class SixteenBoard(object):
    def __init__(self, serialport):
        try:
            self.port = serial.Serial(serialport, 9600, timeout=2)
        except serial.SerialException:
            # errors went to stderr, which went to Harry Potter land.
            # ideally these would go to irc or something.
            raise RuntimeError('unable to open serial port?')
        self.lastmsg = ''
        self.clear()
        
    def message(self,str):
        for c in str:
            self.port.write("w" + mangle(font[c]))
            time.sleep(0.5)

    def clear(self):
        for i in range(0,8):
            self.port.write("w0000")
            time.sleep(0.2)

    def display(self, msg, permanent=True):
        assert isinstance(msg, unicode)
        if len(msg) == 0:
            self.clear()
            return
        msg = msg[:32] # guess
#        msg = msg.replace(u'\xa3', '\x1f') # Fix up for pound

        if not re.match('^[ -~]*$', msg):
            raise ValueError('Standard ASCII only, please')

        self.message(msg)

        if permanent:
            self.lastmsg = msg

    def restore(self):
        self.message(str(self.lastmsg))
