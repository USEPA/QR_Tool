###########
# My Pi Traffic Light Tester app
import RPi.GPIO as GPIO
import time
#GPIO.setwarnings(False)
# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme. This uses the pin numbers that
# match the pin numbers on the Pi Traffic light.

GPIO.setup(9, GPIO.OUT) # Red LED pin set as output
GPIO.setup(10, GPIO.OUT) # Yellow LED pin set as output
GPIO.setup(11, GPIO.OUT) # Green LED pin set as output

# Set the pin HIGH
GPIO.output(9, True) # Turns on the Red LED
GPIO.output(10, True) # Turns on the Red LED
GPIO.output(11, True) # Turns on the Red LED

time.sleep(10)
# Set the pin LOW
GPIO.output(9, False) # Turns off the Red LED
GPIO.output(10, False) # Turns on the Red LED
GPIO.output(11, False) # Turns on the Red LED

# Tidy things up when you exit.
GPIO.cleanup()
###############################################