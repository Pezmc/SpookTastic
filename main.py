import pygame
import RPi.GPIO as GPIO
import time
import glob
import random
import sys
from omxplayer.player import OMXPlayer
from pathlib import Path


GPIO.setmode(GPIO.BCM)
PIR_PIN = 14
GPIO.setup(PIR_PIN, GPIO.IN)

print "Loading Videos"

time.sleep(1)

videos = glob.glob("/home/pi/Videos/*")
videosInQueue = videos
random.shuffle(videosInQueue)

print "Found",  len(videos), "videos"

FULLSCREEN = False

if FULLSCREEN:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((640, 480))

pygame.display.set_caption("Spook Tastic")
pygame.mouse.set_visible(False)

####

def play_random_video():
    global videosInQueue

    if len(videosInQueue) == 0:
        videosInQueue = videos
        random.shuffle(videosInQueue)

    video = videosInQueue.pop()

    print "Playing video", video
    play_video(video)

def play_video(video):
    VIDEO_PATH = Path(video)
    print VIDEO_PATH


    player = None
    try: 
        player = OMXPlayer(VIDEO_PATH)

        # App is real slow to boot and start playing video
        time.sleep(5)

        player.play()

        while player.is_playing():
            print "status:", player.playback_status(),
            print "position:", player.position()
            time.sleep(0.1)

    except SystemError:
        print "OMXPlayer failed to start, maybe"
        print "Sleeping for 60 seconds in case it didn't actually fail..."
        print player
        time.sleep(60)

    except OMXPlayerDeadError:
        print "OMXPlayer appeared to close, video likely ended!"
        print "Waiting 15 seconds"
        time.sleep(15)

    finally: 
        sleepFor = random.randint(15,60)
        print "Played video, not playing another for", sleepFor, "seconds"
        time.sleep(sleepFor)


######

pygame.init()
print "Ready"
try:
    running = True
    while running:
        sys.stdout.write(".")
        sys.stdout.flush()
        for event in pygame.event.get():
            #print "Event", event
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.unicode.lower() == 'q':
                    print "Escape pressed, closing"
                    running = False
                    break
                elif event.unicode.lower() == "f":
                    print "Toggling fullscreen"
                    FULLSCREEN = not FULLSCREEN
                    if FULLSCREEN:
                        pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        pygame.display.set_mode((640, 480))


        if GPIO.input(PIR_PIN):
            print "Motion Detected!"
            play_random_video()

        time.sleep(0.25)

finally:
    pygame.quit()

# Close screen
pygame.quit()

#######

