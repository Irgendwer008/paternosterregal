import RPi.GPIO as GPIO
import time

class Motor():
    def __init__(self, STEP_PIN, DIR_PIN, HALL_PIN, PAUSE_TIME):
        self.STEP_PIN = STEP_PIN
        self.DIR_PIN = DIR_PIN
        self.HALL_PIN = HALL_PIN
        
        self.PAUSE_TIME = PAUSE_TIME
        
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(STEP_PIN, GPIO.OUT)
        GPIO.setup(DIR_PIN, GPIO.OUT)
        GPIO.setup(HALL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        self.position = 0
        
    def move_to_position(self, target: int):
        if target != self.position:
            self.move_step(target - self.position)
    
    def move_step(self, steps: int):
        if steps == 0:
            return
        
        if steps < 0:
            GPIO.output(self.DIR_PIN, GPIO.HIGH)
            for i in range(-steps):
                GPIO.output(self.STEP_PIN, GPIO.HIGH)
                time.sleep(self.PAUSE_TIME)
                GPIO.output(self.STEP_PIN, GPIO.LOW)
                time.sleep(self.PAUSE_TIME)
                self.position -= 1
        else:
            GPIO.output(self.DIR_PIN, GPIO.LOW)
            for i in range(steps):
                GPIO.output(self.STEP_PIN, GPIO.HIGH)
                time.sleep(self.PAUSE_TIME)
                GPIO.output(self.STEP_PIN, GPIO.LOW)
                time.sleep(self.PAUSE_TIME)
                self.position += 1
    
    def exit(self):
        GPIO.cleanup()
    
    def homing(self):
        if GPIO.input(22):
            GPIO.output(self.DIR_PIN, GPIO.LOW)
            while True:
                GPIO.output(self.STEP_PIN, GPIO.HIGH)
                time.sleep(self.PAUSE_TIME)
                GPIO.output(self.STEP_PIN, GPIO.LOW)
                time.sleep(self.PAUSE_TIME)
                if not GPIO.input(22):
                    self.position = 1080
                    break
        else:
            GPIO.output(self.DIR_PIN, GPIO.HIGH)
            while True:
                GPIO.output(self.STEP_PIN, GPIO.HIGH)
                time.sleep(self.PAUSE_TIME)
                GPIO.output(self.STEP_PIN, GPIO.LOW)
                time.sleep(self.PAUSE_TIME)
                if GPIO.input(22):
                    self.position = 1140
                    break