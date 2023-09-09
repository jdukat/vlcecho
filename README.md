# vlcecho
This is a trivial Python app to mimic VLC media player telnet interface (only partial implementation) and play the audio streams on ffplay.
It is intended to use with Home Assistant and VLC Telnet integration.  
Doesn't support any video features.  
It has tons of limitations.  
It has no security features.  
It's an initial implementation that just works "good enough" for me.  

## Running the server
Recommend to run in tmux or similar environment.  
Just run:  
    python3 src/main.py
