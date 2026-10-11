"""Two-player LAN prototype. Token-protected; no public internet hosting."""
import json
import secrets
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from model import PETS, THEMES

class RoomServer:
    def __init__(self, host='0.0.0.0', port=47832):
        self.token = secrets.token_urlsafe(24)
        self.players = {}
        self.lock = threading.Lock()
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                if self.path != '/room':
                    self.send_error(404); return
                if not secrets.compare_digest(self.headers.get('Authorization',''), 'Bearer '+owner.token):
                    self.send_error(403); return
                try:
                    length = int(self.headers.get('Content-Length','0'))
                    if not 0 < length <= 1024: raise ValueError()
                    incoming = json.loads(self.rfile.read(length))
                    identity = incoming['id']
                    if not isinstance(identity,str) or not 1 <= len(identity) <= 64: raise ValueError()
                    if incoming['pet'] not in PETS or incoming['room'] not in THEMES: raise ValueError()
                    if incoming['reaction'] not in ('idle','typing','heart','wave','sleep','click','pet','toy'): raise ValueError()
                    if not isinstance(incoming['name'],str): raise ValueError()
                    state = {k:incoming[k] for k in ('pet','room','reaction')}
                    state['name'] = incoming['name'][:24]
                    state['seen'] = time.monotonic()
                except (ValueError,KeyError,TypeError):
                    self.send_error(400); return
                with owner.lock:
                    owner.players = {k:v for k,v in owner.players.items() if time.monotonic()-v['seen'] < 8}
                    if identity not in owner.players and len(owner.players) >= 2:
                        self.send_error(409,'Room is full'); return
                    if incoming.get('leave'):
                        owner.players.pop(identity,None)
                    else:
                        owner.players[identity] = state
                    result = [dict(id=identity,**{k:v[k] for k in ('pet','name','room','reaction')}) for identity,v in owner.players.items()]
                body = json.dumps(result).encode()
                self.send_response(200)
                self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(body)))
                self.end_headers(); self.wfile.write(body)
        self.server = ThreadingHTTPServer((host,port),Handler)
        self.server.daemon_threads = True
        self.server.timeout = 2
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
    @property
    def port(self): return self.server.server_port
    def close(self):
        self.server.shutdown(); self.server.server_close()

def exchange(url, token, state):
    request = urllib.request.Request(url.rstrip('/')+'/room', data=json.dumps(state).encode(),
              headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
    with urllib.request.urlopen(request,timeout=2) as response:
        return json.loads(response.read(4096))
