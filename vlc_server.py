import socketserver
import time
from alsa_vol_ctrl import VolumeControl
from output_ffplay import OutputFFPlay

class VlcServer(socketserver.BaseRequestHandler):

    my_stream = None
    my_state = 'stopped'
    my_time = None
    my_vol_ctrl = None
    my_player = None

    def initialize(self):
        self.my_vol_ctrl = VolumeControl('pulse')
        self.my_player = OutputFFPlay()

    def handle(self):
        print(f"Incoming connection from {self.client_address[0]}")
        self.initialize()
        self.authenticate()
        self.command_loop()

    def authenticate(self):
        self.request.sendall(b'Password: ')
        self.data = self.request.recv(1024).strip()
        print(f"-> Password received: {self.data.decode()}")
        self.request.sendall(b'Welcome, Master\r\n')
        self.request.sendall(b'> ')

    def command_loop(self):
        while True:
            self.data = self.request.recv(1024).strip()
            if not self.data: break
            cmd = self.data.decode()
            print(f"--> Command: {cmd}")
            cmd = cmd.split()
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
        output += f"( state {self.my_state} )\r\n"
        self.send_output(output)

    def cmd_info(self):
        None

    def cmd_add(self, arg: str):
        self.my_stream = arg
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


def run_vlc_server():
    with socketserver.TCPServer(('0.0.0.0', 4212), VlcServer) as server:
        server.serve_forever()
