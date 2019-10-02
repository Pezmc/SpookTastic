import RPi.GPIO as GPIO
import time

PIR_PIN = 14

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

print "Ready"
while True:
    if GPIO.input(PIR_PIN):
        print "Motion Detected!"
    else:
        print "."            

    time.sleep(0.25)