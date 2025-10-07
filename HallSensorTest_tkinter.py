from gpiozero import Button, Device
from gpiozero.pins.pigpio import PiGPIOFactory
import tkinter as tk

Device.pin_factory = PiGPIOFactory()

root = tk.Tk()
root.geometry("500x300")

GPIObutton = Button(17)
textvariable = tk.StringVar(value="")
label = tk.Label(root, textvariable=textvariable, font=("liberation sans", 40))
label.pack()

if GPIObutton.is_pressed:
    textvariable.set("An")
else:
    textvariable.set("Aus")

def on():
    textvariable.set("An")
    
def off():
    textvariable.set("Aus")

GPIObutton.when_pressed = on
GPIObutton.when_released = off

root.mainloop()
