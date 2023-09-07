import subprocess

class OutputFFPlay:
    my_ffplay = None  # current ffplay subprocess

    #def __init__(self):

    def play(self, media: str):
        self.stop()
        self.my_ffplay = subprocess.Popen(['ffplay',
            '-nodisp', '-hide_banner', '-autoexit',
            '-loglevel', 'error',
            media])

    def stop(self):
        if(self.my_ffplay != None):
            self.my_ffplay.kill()
            self.my_ffplay = None
