from rpi_ws281x import PixelStrip, Color

class LED():
    def __init__(self, LED_COUNT, LED_PIN, LED_FREQ_HZ = 800000, LED_DMA = 10, LED_BRIGHTNESS = 255, LED_INVERT = False, LED_CHANNEL = 0):# Create NeoPixel object with appropriate configuration.
        self.strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        # Intialize the library (must be called once before other functions).
        self.strip.begin()

    def clear(self):
        for j in range(self.strip.numPixels()):
            self.strip.setPixelColorRGB(j, 0, 0, 0)
            self.strip.show()
            
    def rainbow(self):
        for i in range(255):
            for j in range(self.strip.numPixels()):
                self.strip.setPixelColorRGB(j, 255-i, i, 0)
                self.strip.show()
        for i in range(255):
            for j in range(self.strip.numPixels()):
                self.strip.setPixelColorRGB(j, 0, 255-i, i)
                self.strip.show()
        for i in range(255):
            for j in range(self.strip.numPixels()):
                self.strip.setPixelColorRGB(j, i, 0, 255-i)
                self.strip.show()
    
    def highlight(self, start: int, end: int, r: int = 255, g: int = 255, b: int = 255):
        for i in range(0, start-1):
            self.strip.setPixelColorRGB(i, 0, 0, 0)
            
        for i in range(start-1, end):
            self.strip.setPixelColorRGB(i, r, g, b)
            
        for i in range(end, self.strip.numPixels()):
            self.strip.setPixelColorRGB(i, 0, 0, 0)
            
        self.strip.show()