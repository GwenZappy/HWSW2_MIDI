import spidev
from time import sleep, time
import board
import neopixel
import math

# Initialize SPI
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000
spi.mode = 0

def read_adc(channel):
    """Read from the ADC channel."""
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def map_value(value, from_low, from_high, to_low, to_high):
    """Map value using exponential mapping to increase sensitivity at lower range."""
    range_ratio = (value - from_low) / (from_high - from_low)
    exp_ratio = range_ratio ** 0.5  # Apply square root to increase sensitivity
    return (exp_ratio * (to_high - to_low)) + to_low

def low_pass_filter(new_value, last_value, alpha=0.5):
    """Apply low-pass filter to smooth the signal."""
    return alpha * new_value + (1 - alpha) * last_value

# Setup NeoPixel
pixel_pin = board.D18
num_pixels = 10
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, auto_write=False)

# Setup thresholds and timing
threshold = 100
max_raw_value = 1023
debounce_time = 0.1  # Cooldown period to prevent multiple detections
last_impact_time = 0
last_filtered_value = 0  # Initial value for the low-pass filter

# Calibrate this based on experimental observations
to_low = 0.1  # Adjust this value to the lowest visible brightness on your NeoPixels
to_high = 1.0  # Maximum brightness for the strongest impact

# Main loop
while True:
    current_time = time()
    raw_value = read_adc(0)
    filtered_value = low_pass_filter(raw_value, last_filtered_value)
    last_filtered_value = filtered_value  # Update the last filtered value

    if current_time - last_impact_time > debounce_time:
        if filtered_value > threshold:
            last_impact_time = current_time  # Update time of last impact
            brightness = map_value(filtered_value, threshold, max_raw_value, 0.1, 1.0)
            pixels.brightness = brightness
            pixels.fill((255, 0, 100))
            pixels.show()
            print(f"Impact detected with raw value: {raw_value}, filtered value: {filtered_value}")

        else:
            pixels.fill((0, 0, 0))
            pixels.show()

    #sleep(0.01)  # Sleep to reduce CPU usage
