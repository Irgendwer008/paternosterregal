import time
from rpi_ws281x import PixelStrip, Color


# LED strip configuration:
LED_COUNT = 5        # Number of LED pixels.
LED_PIN = 18          # GPIO pin co nnected to the pixels (18 uses PWM!).
#LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

def clear():
    for j in range(strip.numPixels()):
        strip.setPixelColor(j, Color(0, 0, 0, 0))
        strip.show()
        
def rainbow():
    for i in range(255):
        for j in range(strip.numPixels()):
            strip.setPixelColor(j, Color(255-i, i, 0, 0))
            strip.show()
    for i in range(255):
        for j in range(strip.numPixels()):
            strip.setPixelColor(j, Color(0, 255-i, i, 0))
            strip.show()
    for i in range(255):
        for j in range(strip.numPixels()):
            strip.setPixelColor(j, Color(i, 0, 255-i, 0))
            strip.show()

# Main program logic follows:
if __name__ == '__main__':

    # Create NeoPixel object with appropriate configuration.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    
    try:
        # Lauf
        for i in range(strip.numPixels()):
            for j in range(strip.numPixels()):
                if i == j:
                    strip.setPixelColor(j, Color(255, 100, 0, 0))
                else:
                    strip.setPixelColor(j, Color(0, 0, 0, 0))
                strip.show()
                time.sleep(0.01)
            time.sleep(0.33)
        
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(255, 100, 0, 0))
            time.sleep(0.01)
        strip.show()
            
        time.sleep(0.33)
        
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0, 0))
        strip.show()
        
        # Regenbogen
        rainbow()
        rainbow()
 
        clear()

    except KeyboardInterrupt:
        clear()
