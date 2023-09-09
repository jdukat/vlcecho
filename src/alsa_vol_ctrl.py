import subprocess
import re

class VolumeControl:
    my_volume = -1  # current value [%]

    my_alsa_device = ''
    my_alsa_master_ctrl_id = -1
    my_alsa_vol_min = -1    # absolute min
    my_alsa_vol_max = -1    # absolute max    

    def __init__(self, device: str):
        self.my_alsa_device = device;
        self.determine_numid()
        self.read_volume()

    def determine_numid(self):
        """Determine volume control numid"""
        # Sample amixer output:
        #   $amixer -D pulse controls
        #   numid=4,iface=MIXER,name='Master Playback Switch'
        #   numid=3,iface=MIXER,name='Master Playback Volume'
        #   numid=2,iface=MIXER,name='Capture Switch'
        #   numid=1,iface=MIXER,name='Capture Volume'
        cmd = f"amixer -D {self.my_alsa_device} controls"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        for ctrl in result.stdout.splitlines():
            if('master playback volume' in ctrl.lower()):
                match = re.search('^numid=([0-9]+),.*$', ctrl)
                if(match != None):
                    self.my_alsa_master_ctrl_id = match.group(1)
                    return
        raise Exception(f"Unable to determine Master Volume Control numid for device: {self.my_alsa_device}")

    def read_volume(self):
        """Read min/max/current volume from ALSA mixer"""
        self.my_volume = -1
        self.my_alsa_vol_min = -1
        self.my_alsa_vol_max = -1

        # Sample amixer output:
        #   $ amixer -D pulse cget numid=3
        #   numid=3,iface=MIXER,name='Master Playback Volume'
        #     ; type=INTEGER,access=rw------,values=2,min=0,max=65536,step=1
        #     : values=13107,13107
        cmd = f"amixer -D {self.my_alsa_device} cget numid={self.my_alsa_master_ctrl_id}"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        for ctrl in result.stdout.splitlines():
            match = re.search('min=([0-9]+),max=([0-9]+)', ctrl)
            if(match != None):
                self.my_alsa_vol_min = int(match.group(1))
                self.my_alsa_vol_max = int(match.group(2))
                continue
            match = re.search('values=([0-9]+)', ctrl)
            if(match != None):
                vol = int(match.group(1))
                self.my_volume = round((100.0 * (vol - self.my_alsa_vol_min)) / (self.my_alsa_vol_max - self.my_alsa_vol_min))
                continue

        if(self.my_volume == -1 or self.my_alsa_vol_min == -1 or self.my_alsa_vol_max == -1):
            raise Exception(f"Unable to determine current volume setting for device: {self.my_alsa_device}, numid={self.my_alsa_master_ctrl_id}")

    def set_volume(self, vol: int):
        """Set % volume [0-100]"""
        cmd = f"amixer -M -D {self.my_alsa_device} cset numid={self.my_alsa_master_ctrl_id} {vol}%"
        result = subprocess.run(cmd.split())
        self.read_volume()

    def get_volume(self) -> int:
        return self.my_volume
