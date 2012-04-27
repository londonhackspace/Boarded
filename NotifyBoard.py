#!/usr/bin/env python
import serial, re, time

class NotifyBoard(object):
    def __init__(self, serialport):
        try:
            self.port = serial.Serial(serialport, 9600, timeout=2)
        except serial.SerialException:
            # errors went to stderr, which went to Harry Potter land.
            # ideally these would go to irc or something.
            raise RuntimeError('unable to open serial port?')
        self.lastmsg = ''
        # seems that we need a newline for the
        # arduino to work??
        self.eol = '\x0a'

    def display(self, msg, permanent=True):
        assert isinstance(msg, unicode)
        msg = msg[:162] # Max tested size before it corrupts
        msg = msg.replace(u'\xa3', '\x1f') # Fix up for pound

        if not re.match('^[\x1f -~]*$', msg):
            raise ValueError('Standard ASCII only, please')

        self.port.write(str(msg + self.eol))

        if permanent:
            self.lastmsg = msg

    def restore(self):
        self.port.write(str(self.lastmsg) + self.eol)
