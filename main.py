import pygame
import RPi.GPIO as GPIO
import time
import glob
import random
import sys
from omxplayer.player import OMXPlayer, OMXPlayerDeadError
from dbus import DBusException
from pathlib import Path

DEV_MODE = True
FULLSCREEN = False

#### Setup

GPIO.setmode(GPIO.BCM)
PIR_PIN = 14
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
        player = OMXPlayer(VIDEO_PATH, args='--no-osd -o alsa')

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

#### Main loop

pygame.init()
running = True

videoPlaying = False
videoPlayer = None

waitUntilBeforeNextVideo = time.time()

print "Ready"
try:
    while running:        
        running = check_events()
        if not running: 
            if videoPlayer:
                videoPlayer.quit()
            break

        if videoPlaying:
            videoPlaying = check_if_video_playing(videoPlayer)
            if not videoPlaying:
                sleepFor = random.randint(1 if DEV_MODE else 15, 5 if DEV_MODE else 45)
                waitUntilBeforeNextVideo = time.time() + sleepFor
                print "Played video, not playing another for", sleepFor, "seconds"

        else:
            if GPIO.input(PIR_PIN):
                print "Motion Detected!"
                if time.time() > waitUntilBeforeNextVideo:
                    videoPlaying = True
                    videoPlayer = start_random_video()
                else:
                    print "Not triggering video, waiting until", waitUntilBeforeNextVideo

        time.sleep(0.25)

finally:
    pygame.quit()
