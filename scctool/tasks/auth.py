"""Request auth tokens from twitch and nightbot."""
import base64
import http.server
import logging
import threading
import urllib.parse
import webbrowser
from uuid import uuid4

from PyQt5 import QtCore

module_logger = logging.getLogger('scctool.tasks.auth')

try:
    NIGHTBOT_CLIENT_ID = base64.b64decode(
        b'YzEyMGE5YWQ0MjM3MGNmNTViYzFhNjA5ZjFjYTM0Y2E=').decode("utf8")
    NIGHTBOT_REDIRECT_URI = "http://localhost:65010/nightbot_callback"

    TWITCH_CLIENT_ID = base64.b64decode(
        b'ZHVhbTRneDlhcnlkNDZ1YjZxY2RqcmN4b2doeWFr').decode("utf8")
    TWITCH_REDIRECT_URI = "http://localhost:65010/twitch_callback"

except Exception as e:
    module_logger.exception("message")
    raise


class myHandler(http.server.SimpleHTTPRequestHandler):

    # Handler for the GET requests
    def do_GET(self):
        if self.path in ['/nightbot', '/twitch']:
            js_response = ('<script type="text/javascript">'
                           'window.location = "{}";'
                           '</script>')
            state = str(uuid4())
            scope = self.path.replace('/', '')
            url = getattr(self, 'get_auth_url_{}'.format(scope))(state)
            self.send_content(js_response.format(url))
        if self.path in ['/nightbot_callback', '/twitch_callback']:
            js_response = ('<script type="text/javascript">'
                           ' var token = window.location.href.split("#")[1];'
                           ' window.location = "{}_token?" + token;</script>')
            self.send_content(js_response.format(self.path))
        elif self.path.split('?')[0] in ['/nightbot_callback_token',
                                         '/twitch_callback_token']:
            content = _("StarCraft Casting Tool: Succesfully recived access"
                        " to {} - you can close this tab now.")
            if self.path.split('?')[0] == '/twitch_callback_token':
                scope = 'twitch'
            else:
                scope = 'nightbot'
            self.send_content(content.format(scope.capitalize()))
            par = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            self.server.emit_token(scope, par.get('access_token', [''])[0])
        else:
            self.send_error(404, "File not found")

    def log_message(self, format, *args):
        pass

    def send_content(self, response):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-length", len(response))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def get_auth_url_nightbot(self, state):
        """Generate auth url for nightbot."""
        # Generate a random string for the state parameter
        # Save it for use later to prevent xsrf attacks
        params = {"client_id": NIGHTBOT_CLIENT_ID,
                  "response_type": "token",
                  "state": state,
                  "redirect_uri": NIGHTBOT_REDIRECT_URI,
                  "scope": "commands"}
        url = "https://api.nightbot.tv/oauth2/authorize?" + \
            urllib.parse.urlencode(params)
        return url

    def get_auth_url_twitch(self, state):
        """Generate auth url for twitch."""
        # Generate a random string for the state parameter
        # Save it for use later to prevent xsrf attacks
        params = {"client_id": TWITCH_CLIENT_ID,
                  "response_type": "token",
                  "state": state,
                  "redirect_uri": TWITCH_REDIRECT_URI,
                  "scope": "channel_editor"}
        url = "https://api.twitch.tv/kraken/oauth2/authorize?" + \
            urllib.parse.urlencode(params)
        return url


class AuthThread(http.server.HTTPServer, QtCore.QThread):
    """Define thread for flask."""

    tokenRecived = QtCore.pyqtSignal(str, str)
    pending_requests = set()

    def __init__(self):
        """Init thread."""
        QtCore.QThread.__init__(self)
        http.server.HTTPServer.__init__(self, ('', 65010), myHandler)

    def __del__(self):
        """Delete thread."""
        self.terminate()

    def terminate(self):
        self.shutdown()

    def emit_token(self, scope, token):
        self.pending_requests.remove(scope)
        if len(self.pending_requests) == 0:
            assassin = threading.Thread(target=self.shutdown)
            assassin.daemon = True
            assassin.start()
        self.tokenRecived.emit(scope, token)

    def run(self):
        """Run thread."""
        module_logger.info("AuthThread started")
        try:
            self.serve_forever()
        except OSError as e:
            pass
        finally:
            module_logger.info("AuthThread done")

    def requestToken(self, scope):
        if scope not in ['twitch', 'nightbot']:
            return

        if not self.isRunning():
            self.start()
        self.pending_requests.add(scope)

        webbrowser.open("http://localhost:65010/{}".format(scope))

    def server_bind(self):
        http.server.HTTPServer.server_bind(self)
        self.socket.setsockopt(http.server.socket.SOL_SOCKET,
                               http.server.socket.SO_REUSEADDR, 1)