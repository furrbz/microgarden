import sys
import Adafruit_DHT
import time
import RPi.GPIO as GPIO

if __name__=='__main__':
    #setup the GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(4,GPIO.OUT)

    try:
        #GPIO.output(3,GPIO.LOW) #activates relay
        #time.sleep(1)
        GPIO.output(4,GPIO.HIGH) #deactivates relay
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Bye")