#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import serial, re, time, threading, Queue
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

q = Queue.Queue(42)

class SixteenWorker():
    def __init__(self, serialport, queue):
        try:
            self.port = serial.Serial(serialport, 9600, timeout=2)
        except serial.SerialException:
            # errors went to stderr, which went to Harry Potter land.
            # ideally these would go to irc or something.
            raise RuntimeError('unable to open serial port?')
        self.lastmsg = ''
        self.queue = queue
        self.scroller = None
        self.stop = threading.Event()

        self.clear()

    def run(self):
        while True:
            try:
                # clear the board after 10 mins, stops it being left on all night
                message = self.queue.get(True, 60 * 10)
                self.display(message[0], message[1])
            except Queue.Empty:
                self.clear()

    def message(self, str):
        for c in str:
            self.port.write("w" + mangle(font[c]))
            time.sleep(0.5)

    def scroll_message(self, msg, stop):
        pos = 0
        # add a space on the end to the wrap around works better
        if msg[-1] != " ":
            msg += " "

        while True:
            if stop.isSet():
                break
            self.port.write("w" + mangle(font[msg[pos]]))
            if stop.wait(0.5):
                break
            pos += 1
            if pos == len(msg):
                pos = 0

    def clear(self):
        if self.scroller:
            self.stop.set()
            self.scroller.join()
            self.stop.clear()
        # "r" dosn't work properly, clocked too fast?!?
#        self.port.write("r")
        for i in range(0,7):
            self.port.write("w" + mangle(font[" "]))
            time.sleep(0.25)
#        self.port.write("r")

    def display(self, msg, permanent=True):
        assert isinstance(msg, unicode)
        if len(msg) == 0:
            self.clear()
            return
#        msg = msg.replace(u'\xa3', '\x1f') # Fix up for pound
        # XXX no £ sign in the font :(

        if not re.match('^[ -~]*$', msg):
            raise ValueError('Standard ASCII only, please')
        
        self.clear()
        if len(msg) <= 8:
            self.message(msg)
        else:
            self.scroller = threading.Thread(name="sixteen_scroll", target=self.scroll_message, kwargs={"msg": msg, "stop": self.stop})
            self.scroller.setDaemon(True)
            self.scroller.start()

        if permanent:
            self.lastmsg = msg

    def restore(self):
        self.display(str(self.lastmsg), True)

class SixteenBoard(object):
    def __init__(self, serialport):
        self.queue = Queue.Queue(42)
        self.worker = SixteenWorker(serialport, self.queue)
        self.t = threading.Thread(name="sixteen_work", target=self.worker.run)
        self.t.setDaemon(True)
        self.t.start()
