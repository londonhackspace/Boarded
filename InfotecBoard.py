#!/usr/bin/env python
import serial, re, time
from datetime import datetime

class InfotecBoard(object):
    def __init__(self, serialport):
        self.port = serial.Serial(serialport, 9600, timeout=1)
        self.lastmsg = ''

    def display(self, msg, permanent=True):
        assert isinstance(msg, unicode)
        msg = re.sub(r'([><\n^])', r'^\1', msg)

        if not re.match(r'^[ -~]*$', msg):
            raise ValueError('Standard ASCII only, please')

        self.scroll_text(str(msg))

        if permanent:
            self.lastmsg = msg

    def restore(self):
        self.set_text(str(self.lastmsg))

    def set_text(self, msg, centre=False, dunno=None):
      args = []
      if centre:
        args.append(1)
      self.send_cmd(0, msg, args)

    def scroll_text(self, msg, delay=2, repeat=False):
      args = [delay]
      if repeat:
        args.append(1)
      self.send_cmd(2, msg, args)

    def set_clock(self, dt):
      assert 1990 <= dt.year < 2090
      self.send_cmd(0x8b, args=[dt.hour, dt.minute, dt.second])
      this.send_cmd(0x8c, args=[dt.day, dt.month, dt.year % 100])

    def send_cmd(self, cmdnum, inbuf='', args=None, serialtask=0, inflags=0, sendresponse=1):
      if args is None:
        args = []
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

if __name__ == '__main__':
  import sys
  if len(sys.argv) <= 1:
    print 'Usage: %s /dev/ttyS1 [ --set-clock | your message here ]' % sys.argv[0]
  else:
    board = InfotecBoard(sys.argv[1])
    msg = ' '.join(sys.argv[2:])
    if msg == '--set-clock':
      board.set_clock(datetime.now())
    else:
      board.scroll_text(msg)

