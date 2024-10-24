## Installation

You may need to reference the picamera2 documentation to get this script to work,
rpi5 no longer uses the original picamera library

https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf

The "generate" function of this tool expects ffmpeg to be installed on the system

```
git clone https://github.com/mcmcford/simple_pi_timelapse.git
cd simple_pi_timelapse
```

```
python3 -m venv venv
python3 -m venv --system-site-packages venv
pip install requirements.txt
```

```
python main.py
```

