import RPi.GPIO as GPIO
import time

# Set up the GPIO pin numbering mode
GPIO.setmode(GPIO.BCM)

# Set up the GPIO pin for the LED
LED_PIN = 17
GPIO.setup(LED_PIN, GPIO.OUT)

try:
    while True:
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.01)  # Wait for 1 second

        GPIO.output(LED_PIN, GPIO.LOW)
        time.sleep(0.01)  # Wait for 1 second

except KeyboardInterrupt:
    # Clean up the GPIO pins on exit
    GPIO.cleanup()
    print("Program exited cleanly")