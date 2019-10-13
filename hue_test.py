#!/usr/bin/python

from phue import Bridge, PhueRegistrationException

while True:
    try:
        b = Bridge('192.168.0.211')
        b.connect()
        break
    except PhueRegistrationException as e:
        raw_input('Press button on Bridge then hit Enter to try again')  # noqa

# If the app is not registered and the button is not pressed, press the button and call connect() (this only needs to be run a single time)


# phue.PhueRegistrationException

# Get the bridge state (This returns the full dictionary that you can explore)
import yaml
import random
import time

#print(yaml.safe_dump(b.get_api()))

# Prints if light 1 is on or not
'''b.get_light(1, 'on')

# Set brightness of lamp 1 to max
b.set_light(1, 'bri', 254)

# Set brightness of lamp 2 to 50%
b.set_light(2, 'bri', 127)

# Turn lamp 2 on
b.set_light(2,'on', True)

# You can also control multiple lamps by sending a list as lamp_id
b.set_light( [1,2], 'on', True)

# Get the name of a lamp
b.get_light(1, 'name')

# You can also use light names instead of the id
b.get_light('Kitchen')
b.set_light('Kitchen', 'bri', 254)

# Also works with lists
b.set_light(['Bathroom', 'Garage'], 'on', False)
'''

# The set_light method can also take a dictionary as the second argument to do more fancy stuff
# This will turn light 1 on with a transition time of 30 seconds

ENABLE_HUE = True
HUE_LIGHT_NAME = 'Hall Ceiling'
HUE_DEFAULT_BRIGHNESS = 128
HUE_FLICKER_MAX_BRIGHTNESS = 128

count = 0
while True:
    b.set_light(HUE_LIGHT_NAME, {
        'transitiontime' : 0,
        'on' : True,
        'bri' : random.randint(0,HUE_FLICKER_MAX_BRIGHTNESS)
    })
    count += 1
    if count > 100:
        break

b.set_light(HUE_LIGHT_NAME, {
    'transitiontime' : 100,
    'on' : True,
    'bri' : HUE_DEFAULT_BRIGHNESS
})

    