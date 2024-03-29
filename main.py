# TODO: Add no network connection handling
import pygame
import RPi.GPIO as GPIO
import time
import glob
import random
import sys
import argparse

from omxplayer.player import OMXPlayer, OMXPlayerDeadError
from dbus import DBusException
from pathlib import Path

import logging
logging.basicConfig(level=logging.INFO)

DEV_MODE = False
FULLSCREEN = True

MANUAL_TRIGGER = False

MIN_MIN_GAP_BETWEEN_VIDEOS = 10
MAX_MIN_GAP_BETWEEN_VIDEOS = 30

PIR_PIN = 14

HUE_ENABLED = False
HUE_BRIDGE_IP = '192.168.0.211'
HUE_LIGHT_NAME = 'Hall Ceiling'
HUE_DEFAULT_BRIGHNESS = 128
HUE_FLICKER_MAX_BRIGHTNESS = 64

#### Args

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--fullscreen", help="Open full screen", action="store_true")
parser.add_argument("-d", "--devmode", help="Shorten the sleeps for use in development", action="store_true")
args = parser.parse_args()

FULLSCREEN = FULLSCREEN or args.fullscreen
DEV_MODE = DEV_MODE or args.devmode

#### Setup

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

print "Loading Videos"

time.sleep(1)

videos = glob.glob("/home/pi/Videos/*")
videosInQueue = list(videos)
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
    global videosInQueue, videos

    if len(videosInQueue) == 0:
        print "Resetting the queue"
        videosInQueue = list(videos)
        random.shuffle(videosInQueue)

    video = videosInQueue.pop()

    print "Playing video", video
    return play_video(video)

def play_video(video):
    VIDEO_PATH = Path(video)

    player = None
    try:
        arguments = "--no-osd -o alsa --aspect-mode fill"
        if DEV_MODE:
            arguments = arguments + " --win '0 0 400 300'"

        player = OMXPlayer(VIDEO_PATH, args=arguments)

        # App is real slow to boot and start playing video
        time.sleep(1)

        player.play()

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

        result = player.is_playing()

        return result

    except OMXPlayerDeadError:
        print "OMXPlayer appeared to close, video likely ended!"
        return False

    except DBusException:
        print "OMXPlayer not replying, video likely ended!"
        return False

def check_events():
    sys.stdout.write(".")
    sys.stdout.flush()

    global FULLSCREEN, MANUAL_TRIGGER
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
            elif event.unicode.lower() == "t":
                print "Manual trigger"
                MANUAL_TRIGGER = not MANUAL_TRIGGER
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

lastPrintAt = 0
lastVideoStateCheckAt = 0
lastEventCheckAt = 0

startFlashingAt = 0
stopFlashingAt = 0

print "Ready"
if DEV_MODE:
    print "DEV_MODE enabled"
if FULLSCREEN:
    print "FULLSCREEN enabled"
try:
    while running:
        currentTime = time.time()

        if currentTime > lastEventCheckAt - 1: # check for events once per second
            lastEventCheckAt = currentTime
            running = check_events()
            if not running:
                if videoPlayer:
                    videoPlayer.quit()
                break

        if videoPlaying:
            if HUE_ENABLED and currentTime > startFlashingAt and currentTime < stopFlashingAt:
                print "flashing"
                flash_light(bridge)

            if currentTime > lastVideoStateCheckAt + 1: # only check video state every second
                lastVideoStateCheckAt = currentTime
                videoPlaying = check_if_video_playing(videoPlayer)
                if not videoPlaying:
                    if HUE_ENABLED:
                        print "Returning light to default"
                        return_light_to_default(bridge)
                    sleepFor = random.randint(1 if DEV_MODE else MIN_MIN_GAP_BETWEEN_VIDEOS, 5 if DEV_MODE else MAX_MIN_GAP_BETWEEN_VIDEOS)
                    waitUntilBeforeNextVideo = time.time() + sleepFor
                    print "Played video, not playing another for", int(sleepFor), "seconds"

        else:
            if GPIO.input(PIR_PIN) or MANUAL_TRIGGER:
                MANUAL_TRIGGER = False
                print "Motion Detected!"
                if currentTime > waitUntilBeforeNextVideo:
                    videoPlaying = True
                    videoPlayer = start_random_video()
                    startFlashingAt = currentTime + 3 # wait before flashing
                    stopFlashingAt = startFlashingAt + 10 # flash for this long
                else:
                    if currentTime > lastPrintAt + 3: # only print every 3 seconds
                        lastPrintAt = currentTime
                        print "Not triggering video, waiting", int(waitUntilBeforeNextVideo - currentTime), "seconds"

        if HUE_ENABLED and videoPlaying:
            # Skip sleeping while flashing
            if currentTime < startFlashingAt or currentTime > stopFlashingAt:
                time.sleep(0.5) 
        else:
            time.sleep(0.5)

finally:
    pygame.quit()
