import time
from rpi_hardware_pwm import HardwarePWM

pwm = HardwarePWM(pwm_channel=0, hz=60, chip=0)
pwm.start(100) # full duty cycle

pwm.change_duty_cycle(50)
pwm.change_frequency(25_000)

time.sleep(5)

pwm.stop()

