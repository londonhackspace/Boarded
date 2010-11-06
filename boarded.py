#!/usr/bin/env python

import BaseHTTPServer, urlparse, serial, ConfigParser, re, sys, urllib, time

config = ConfigParser.ConfigParser()
config.read((
    'boarded.conf',
    sys.path[0] + '/boarded.conf',
    '/etc/boarded.conf'
))

logfile = config.get('boarded', 'logfile')
log = open(logfile, 'a')
log.write(time.strftime('%a, %d %b %Y %H:%M:%S +0000\n', time.gmtime()))

serialPort = config.get('boarded', 'serialport')
port = serial.Serial(serialPort, 9600, timeout=1)

message_old = ""

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

    # Disable logging DNS lookups
    def address_string(self):
        return str(self.client_address[0])

    def do_GET(self):
        url = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(url.query)
        path = url.path

        path = path.lstrip('/')
        message = urllib.unquote(path).decode('utf8')
        message = message[:162]

        if (message == 'favicon.ico'):
            return

        if not re.match('^[ -~]*$', message):
            self.send_error(400)
            self.end_headers()
            self.wfile.write('Bad request, standard ASCII only please')
            return 

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write('OK')

        log.write('%s %s %s %s: "%s"\n' % (self.client_address,
            self.command, self.path, self.request_version, message))
        port.write(str(message + '\n'))

        if 'restoreAfter' in params:
            global message_old
            time.sleep(float(params['restoreAfter'][0]))
            port.write(str(message_old + "\n"))
        else:
            message_old = message
        

PORT = config.getint('boarded', 'tcpport')
httpd = BaseHTTPServer.HTTPServer(("", PORT), Handler)
httpd.serve_forever()
