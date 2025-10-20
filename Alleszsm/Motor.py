import RPi.GPIO as GPIO
import time

class Motor():
    def __init__(self, STEP_PIN, DIR_PIN):
        self.STEP_PIN = STEP_PIN
        self.DIR_PIN = DIR_PIN
        
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(STEP_PIN, GPIO.OUT)
        GPIO.setup(DIR_PIN, GPIO.OUT)
        
        self.position = 0
        
    def move(self, target: int):
        if target != self.position:
            self.step(target - self.position)
    
    def step(self, steps: int):
        if steps == 0:
            return
        
        if steps > 0:
            GPIO.output(self.DIR_PIN, GPIO.HIGH)
            for i in range(steps):
                GPIO.output(self.STEP_PIN, GPIO.HIGH)
                time.sleep(0.015)
                GPIO.output(self.STEP_PIN, GPIO.LOW)
                self.position += 1
        else:
            GPIO.output(self.DIR_PIN, GPIO.LOW)
            for i in range(-steps):
                GPIO.output(self.STEP_PIN, GPIO.HIGH)
                time.sleep(0.015)
                GPIO.output(self.STEP_PIN, GPIO.LOW)
                self.position -= 1
    
    def exit(self):
        GPIO.cleanup()