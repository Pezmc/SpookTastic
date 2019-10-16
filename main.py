import pygame
import RPi.GPIO as GPIO
import time
import glob
import random
import sys
from omxplayer.player import OMXPlayer, OMXPlayerDeadError
from dbus import DBusException
from pathlib import Path

DEV_MODE = False
FULLSCREEN = False

MIN_MIN_GAP_BETWEEN_VIDEOS = 15
MAX_MIN_GAP_BETWEEN_VIDEOS = 45

PIR_PIN = 14

HUE_ENABLED = True
HUE_BRIDGE_IP = '192.168.0.211'
HUE_LIGHT_NAME = 'Hall Ceiling'
HUE_DEFAULT_BRIGHNESS = 128
HUE_FLICKER_MAX_BRIGHTNESS = 128

#### Setup

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

print "Loading Videos"

time.sleep(1)

videos = glob.glob("/home/pi/Videos/*")
videosInQueue = videos
random.shuffle(videosInQueue)

print "Found",  len(videos), "videos"

if FULLSCREEN:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((640, 480))

pygame.display.set_caption("SpookTastic")
pygame.mouse.set_visible(False)

#### Functions

def start_random_video():
    global videosInQueue

    if len(videosInQueue) == 0:
        videosInQueue = videos
        random.shuffle(videosInQueue)

    video = videosInQueue.pop()

    print "Playing video", video
    return play_video(video)

def play_video(video):
    VIDEO_PATH = Path(video)
    print VIDEO_PATH

    player = None
    try:
        player = OMXPlayer(VIDEO_PATH, args='--no-osd -o alsa --aspect-mode fill')

        # App is real slow to boot and start playing video
        time.sleep(1)

        #player.play()

    except SystemError:
        print "OMXPlayer failed to start, maybe"
        print "Sleeping for 60 seconds in case it didn't actually fail..."
        time.sleep(60)

    except OMXPlayerDeadError:
        print "OMXPlayer appeared to close, video likely ended!"

    except DBusException:
        print "OMXPlayer not replying, video likely ended!"

    finally:
        return player

def check_if_video_playing(player):
    try: 
        if not player:
            return False

        return player.is_playing()

    except OMXPlayerDeadError:
        print "OMXPlayer appeared to close, video likely ended!"
        return False

    except DBusException:
        print "OMXPlayer not replying, video likely ended!"
        return False

def check_events():
    sys.stdout.write(".")
    sys.stdout.flush()

    global FULLSCREEN
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            print "Pygame quit triggered, closing"
            pygame.quit()
            return False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.unicode.lower() == 'q':
                print "Escape pressed, closing"
                pygame.quit()
                return False
            elif event.unicode.lower() == "f":
                print "Toggling fullscreen"
                FULLSCREEN = not FULLSCREEN
                if FULLSCREEN:
                    pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    pygame.display.set_mode((640, 480))

    return True

def connect_to_hue():
    global HUE_BRIDGE_IP
    from phue import Bridge, PhueRegistrationException
    bridge = False
    try:
        bridge = Bridge(HUE_BRIDGE_IP)
        bridge.connect()
    except PhueRegistrationException as e:
        raw_input('Press button on Bridge then hit Enter to try again')
	bridge = connect_to_hue()

    return bridge

def flash_light(bridge):
    global HUE_LIGHT_NAME, HUE_FLICKER_MAX_BRIGHTNESS
    bridge.set_light(HUE_LIGHT_NAME, {
        'transitiontime' : 0,
        'on' : True,
        'bri' : random.randint(0, HUE_FLICKER_MAX_BRIGHTNESS)
    })

def return_light_to_default(bridge):
    global HUE_LIGHT_NAME, HUE_DEFAULT_BRIGHNESS
    bridge.set_light(HUE_LIGHT_NAME, {
        'transitiontime' : 100,
        'on' : True,
        'bri' : HUE_DEFAULT_BRIGHNESS
    })

#### Main loop

pygame.init()
running = True

videoPlaying = False
videoPlayer = None
lastPIRState = False

waitUntilBeforeNextVideo = time.time()

if HUE_ENABLED:
    print "Using Hue light"
    bridge = connect_to_hue()
    return_light_to_default(bridge)

print "Ready"
try:
    while running:
        running = check_events()
        if not running:
            if videoPlayer:
                videoPlayer.quit()
            break

        if videoPlaying:
            if HUE_ENABLED:
                print "flashing"
                flash_light(bridge)
            videoPlaying = check_if_video_playing(videoPlayer)
            if not videoPlaying:
                return_light_to_default(bridge)
                sleepFor = random.randint(1 if DEV_MODE else MIN_MIN_GAP_BETWEEN_VIDEOS, 5 if DEV_MODE else MAX_MIN_GAP_BETWEEN_VIDEOS)
                waitUntilBeforeNextVideo = time.time() + sleepFor
                print "Played video, not playing another for", sleepFor, "seconds"

        else:
            if GPIO.input(PIR_PIN):
                print "Motion Detected!"
                currentTime = time.time()
                if currentTime > waitUntilBeforeNextVideo:
                    videoPlaying = True
                    videoPlayer = start_random_video()
                else:
                    print "Not triggering video, waiting", waitUntilBeforeNextVideo - currentTime, "seconds"

        if HUE_ENABLED and videoPlaying:
            time.sleep(0.01)
            print "short sleep"
        else:
            print "long sleep"
            time.sleep(0.5)

finally:
    pygame.quit()
