#!/usr/bin/env python
import sys, time, imp, ConfigParser, os
import BaseHTTPServer, urlparse, urllib

config = ConfigParser.ConfigParser()
config.read((
    'boarded.conf',
    sys.path[0] + '/boarded.conf',
    '/etc/boarded.conf'
))

# if we don't do this board.log ends up in /
# which is no use to anyone.
os.chdir(sys.path[0])

logfile = config.get('boarded', 'logfile')
log = open(logfile, 'a')
log.write(time.strftime('%a, %d %b %Y %H:%M:%S +0000\n', time.gmtime()))

boardtype = config.get('boarded', 'type')
module = __import__(boardtype)

params = dict(config.items(boardtype))
if len(sys.argv) > 1:
    params['serialport'] = sys.argv[1]
cls = getattr(module, boardtype)
try:
    board = cls(**params)
except RuntimeError, err:
    # ('172.31.24.101', 37292) GET '/test' HTTP/1.1: "test"
    log.write('%s %s %s %s: "%s"\n' % (('127.0.0.1', 0),
                    'FAIL', '/', 'HTTP/1.1', str(err) + " quitting."))
    exit(-1)

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

    # Disable logging DNS lookups
    def address_string(self):
        return str(self.client_address[0])

    def do_GET(self):
        global message_old

        url = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(url.query)
        path = url.path

        path = path.lstrip('/')
        message = urllib.unquote(path).decode('utf8')

        if message == 'favicon.ico':
            # Prevent annoying warnings
            return

        if message.startswith('$W$') or 'restoreAfter' in params:
            permanent = False
        else:
            permanent = True

        try:
            if hasattr(board, "queue"):
                print "enquing"
                board.queue.put_nowait([message, permanent])
            else:
                board.display(message, permanent)

        except Exception, e:
            self.send_error(400)
            self.end_headers()
            self.wfile.write('Bad request: %s' % e)

        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('OK')

            log.write('%s %s %s %s: "%s"\n' % (self.client_address,
                self.command, repr(self.path), self.request_version, message))

            if 'restoreAfter' in params:
                time.sleep(float(params['restoreAfter'][0]))
                board.restore()

PORT = config.getint('boarded', 'tcpport')
httpd = BaseHTTPServer.HTTPServer(("", PORT), Handler)
httpd.serve_forever()

