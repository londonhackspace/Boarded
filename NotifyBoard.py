#!/usr/bin/env python
import serial, re, time

class NotifyBoard(object):
    def __init__(self, serialport):
        self.port = serial.Serial(serialport, 9600, timeout=1)
        self.lastmsg = ''

    def display(self, msg, permanent=True):
        assert isinstance(msg, unicode)
        msg = msg[:162] # Max tested size before it corrupts
        msg = msg.replace(u'\xa3', '\x1f') # Fix up for pound

        if not re.match('^[\x1f -~]*$', msg):
            raise ValueError('Standard ASCII only, please')

        self.port.write(str(msg + '\n'))

        if permanent:
            self.lastmsg = msg

    def restore(self):
        self.port.write(str(self.lastmsg) + '\n')
