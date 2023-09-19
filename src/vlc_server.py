import socketserver
import time
import hashlib
import json
from alsa_vol_ctrl import VolumeControl
from output_ffplay import OutputFFPlay

class VlcServer(socketserver.BaseRequestHandler):

    my_stream = None
    my_title = None
    my_state = 'stopped'
    my_time = None
    my_vol_ctrl = None
    my_player = None
    my_cfg = None

    def setup(self):
        self.my_cfg = self.server.conn
        self.my_vol_ctrl = VolumeControl(self.my_cfg['audio']['volume_device'])
        self.my_player = OutputFFPlay()

    def handle(self):
        client = self.client_address[0]
        print(f"Incoming connection from {client}")
        if(not client in self.my_cfg['server']['allow_list']):
            print("! Not in server.allow_list !")
            self.request.close()
            return
        if(not self.authenticate()):
            self.request.close()
            return
        self.command_loop()

    def authenticate(self):
        attempts = 3
        while attempts > 0:
            self.request.sendall(b'Password: ')
            self.data = self.request.recv(1024).strip()
            if not self.data: return False

            hashed = hashlib.sha256(self.data).hexdigest()
            print(f"Password received, hash: {hashed}")
            if(hashed == self.my_cfg['server']['password']):
                self.request.sendall(b'Welcome, Master\r\n')
                self.request.sendall(b'> ')
                return True
            else:
                self.request.sendall(b'Wrong password\r\n')
                attempts -= 1
        print("! Password authentication failed.")

    def command_loop(self):
        while True:
            self.data = self.request.recv(1024).strip()
            if not self.data: break
            cmd = self.data.decode()
            print(f"--> Command: {cmd}")
            cmd = cmd.split(None, 1)
            args = cmd[1:]
            cmd = cmd[0]
            if(cmd == 'status'): self.cmd_status()
            elif(cmd == 'info'): self.cmd_info()
            elif(cmd == 'add'): self.cmd_add(args[0])
            elif(cmd == 'play'): self.cmd_play()
            elif(cmd == 'stop'): self.cmd_stop()
            elif(cmd == 'pause'): self.cmd_pause()
            elif(cmd == 'get_length'): self.cmd_get_length()
            elif(cmd == 'get_time'): self.cmd_get_time()
            elif(cmd == 'volume'): self.cmd_volume(args[0])
            else:
                print("!!! Unknown command")
            self.request.sendall(b'> ')
        print(f"-> Bye bye")

    def send_output(self, output: str):
        print(output)
        self.request.sendall(output.encode('utf-8'))

    def cmd_status(self):
        output = '';
        if( self.my_stream != None ):
            output = f"( new input: {self.my_stream} )\r\n"
        output += f"( audio volume: {self.my_vol_ctrl.get_volume() * 5} )\r\n"
        if(self.my_player.is_running() == False):
            self.cmd_stop()
        output += f"( state {self.my_state} )\r\n"
        self.send_output(output)

    def cmd_info(self):
        if(self.my_state == 'playing'):
            output = f"""+----[ Meta data ]\r
| filename: {self.my_title}\r
+----[ Stream 0 ]\r
| Type: Audio\r
+----[ end of stream info ]\r
"""
            self.send_output(output)

    def cmd_add(self, arg: str):
        if(arg[0] == '{'):
            print("Parsing json:")
            print(arg)
            arg = json.loads(arg)
            self.my_stream = arg['stream']
            self.my_title = arg['title']
            print(f"Json input: {self.my_title}: {self.my_stream}")
        else:
            self.my_stream = arg
            self.my_title = "Stream-FM"
        self.cmd_play()

    def cmd_play(self):
        if(self.my_stream != None):
            self.my_state = "playing"
            self.my_player.play(self.my_stream)
            self.my_time = time.time()

    def cmd_stop(self):
        self.my_state = "stopped"
        self.my_player.stop()
        self.my_time = None

    def cmd_pause(self):
        if(self.my_stream != None):
            if(self.my_state == "playing"):
                self.my_state = "paused"
                self.my_player.stop()
            else:
                self.my_state = "playing"
                self.my_player.play(self.my_stream)

    def cmd_get_length(self):
        self.send_output("0\r\n")
            
    def cmd_get_time(self):
        seconds = 0
        if(self.my_time != None):
            seconds = int(time.time() - self.my_time)
        self.send_output(f"{seconds}\r\n")

    def cmd_volume(self, new_vol: str):
        vol = int(new_vol)
        # VLC supports volume in range 0-512, so approx vol / 5 = % volume for ALSA
        self.my_vol_ctrl.set_volume(vol / 5)


def run_vlc_server(cfg):
    port = cfg['server']['port']
    assert type(port) is int, 'Port must be integer'
    with socketserver.TCPServer(('0.0.0.0', port), VlcServer) as server:
        server.conn = cfg
        server.serve_forever()
