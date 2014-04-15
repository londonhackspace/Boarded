#!/usr/bin/env python
import serial, re, time, threading, Queue
from datetime import datetime

class InfotecWorker(object):
    def __init__(self, serialport, queue, verbose=False):
      try:
        self.port = serial.Serial(serialport, 9600, timeout=1)
      except serial.SerialException:
        raise RuntimeError('unable to open serial port?')
      self.lastmsg = ''
      self.queue = queue
      self.verbose = verbose
      self.set_clock(datetime.now())

    def run(self):
      while True:
        try:
          # timeout after 10 mins
          message = self.queue.get(True, 60 * 10)
          # Ignore the message cos we can't change back to the clock...
          #self.display(message[0], message[1])
        except Queue.Empty:
          self.set_clock(datetime.now())

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
      self.send_cmd(0x8c, args=[dt.day, dt.month, dt.year % 100])

    def send_cmd(self, cmdnum, inbuf='', args=None, serialtask=0, inflags=0, sendresponse=1, verbose=False):
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
      if self.verbose:
        print cmd
      self.port.write(cmd)
      if self.verbose:
        if self.port.inWaiting() > 0:
          print self.port.read()

    def crash_and_reboot(self):
      # we don't know how to turn the display back
      # to clock mode, so crash the display and make it reboot.
      # >0#1#1#00#blah#2#cc<
      #
      # Some times the display stays blank and needs power cycling :(
      #
      self.send_cmd(1, 'blah', [2,])

class InfotecBoard(object):
  def __init__(self, serialport):
    self.queue = Queue.Queue(42)
    self.worker = InfotecWorker(serialport, self.queue)
    self.t = threading.Thread(name="infotec_work", target=self.worker.run)
    self.t.setDaemon(True)
    self.t.start()

if __name__ == '__main__':
  import sys
  if len(sys.argv) <= 1:
    print 'Usage: %s /dev/ttyS1 [ --set-clock | your message here ]' % sys.argv[0]
  else:
    board = InfotecWorker(sys.argv[1], None, True)
    msg = ' '.join(sys.argv[2:])
    if msg == '--set-clock':
      board.set_clock(datetime.now())
#      board.crash_and_reboot()
    else:
      board.scroll_text(msg)

