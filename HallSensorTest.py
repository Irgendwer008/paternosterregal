from gpiozero import Button, Device
from gpiozero.pins.pigpio import PiGPIOFactory
from signal import pause

Device.pin_factory = PiGPIOFactory()

button = Button(22)

state = False

def on_change():
    global state
    new_state = button.is_pressed
    if new_state != state:
        state = new_state
        print(f"State changed: {state}")

button.when_pressed = on_change
button.when_released = on_change

pause()
