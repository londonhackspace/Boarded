#!/usr/bin/env python
import serial, re, time

class InfotecBoard(object):
    def __init__(self, serialport):
        self.port = serial.Serial(serialport, 9600, timeout=1)
        self.lastmsg = ''

    def display(self, msg, permanent=True):
        assert isinstance(msg, unicode)
        msg = re.sub(r'([><\n^])', r'^\1', msg)

        if not re.match(r'^[ -~]*$', msg):
            raise ValueError('Standard ASCII only, please')

        self.set_text(str(msg))

        if permanent:
            self.lastmsg = msg

    def restore(self):
        self.set_text(str(self.lastmsg))

    def set_text(self, msg, args=[]):
      self.send_cmd(0, msg, args)

    def send_cmd(self, cmdnum, inbuf, args=[], serialtask=0, inflags=0, sendresponse=1):
      checksum = 0xcc # actually ignored
      cmd = '>%x#%x#%x#%02x#%s#%s#%02x<' % (
        inflags,
        sendresponse,
        cmdnum,
        serialtask,
        inbuf,
        ','.join('%x' % a for a in args),
        checksum,
      )
      self.port.write(cmd)

