import board
import neopixel
import time

# Number of pixels per strisp
num_pixels = 6

# Initialize the NeoPixel objects for each pin
pixels_A = neopixel.NeoPixel(board.D18, num_pixels, auto_write=True)
pixels_B = neopixel.NeoPixel(board.D12, num_pixels, auto_write=True)

def light_up_staggered():
    while True:
        # Turn on Pixel A and turn off Pixel B
        pixels_A.fill((255, 0, 0))  # Red color for Pixel A
        pixels_B.fill((0, 0, 0))    # Off for Pixel B
        time.sleep(1)  # Delay for 1 second

        # Turn off Pixel A and turn on Pixel B
        pixels_A.fill((0, 0, 0))    # Off for Pixel A
        pixels_B.fill((0, 255, 0))  # Green color for Pixel B
        time.sleep(1)  # Delay for 1 second

if __name__ == '__main__':
    light_up_staggered()
