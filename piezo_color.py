import spidev
from time import sleep, time
import board
import neopixel

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
    """Map value to a different range, applying a square root to increase sensitivity at lower range."""
    range_ratio = (value - from_low) / (from_high - from_low)
    exp_ratio = range_ratio ** 0.5
    return (exp_ratio * (to_high - to_low)) + to_low

def low_pass_filter(new_value, last_value, alpha=0.2):
    """Apply low-pass filter to smooth the signal."""
    return alpha * new_value + (1 - alpha) * last_value

# Setup NeoPixel
pixel_pin = board.D18
num_pixels = 6
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, auto_write=False)

# Define unique colors for each LED
colors = [
    (255, 0, 0),    # Red
    (0, 255, 0),    # Green
    (100, 0, 255),    # Blue
    (255, 255, 0),  # Yellow
    (0, 255, 255),  # Cyan
    (255, 0, 255)   # Magenta
]

# Setup thresholds and timing for each sensor
threshold = [300] * 6
max_raw_value = 1023
debounce_time = 0.1
last_impact_time = [0] * 6
last_filtered_value = [0] * 6

# Calibrate brightness
to_low = 0.1
to_high = 1.0

# Main loop
while True:
    current_time = time()
    for i in range(num_pixels):
        raw_value = read_adc(i)
        filtered_value = low_pass_filter(raw_value, last_filtered_value[i])
        last_filtered_value[i] = filtered_value

        if current_time - last_impact_time[i] > debounce_time:
            if filtered_value > threshold[i]:
                last_impact_time[i] = current_time
                brightness = map_value(filtered_value, threshold[i], max_raw_value, to_low, to_high)
                scaled_color = tuple(int(c * brightness) for c in colors[i])
                pixels[i] = scaled_color
                pixels.show()
                print(f"Sensor {i} impact detected with raw value: {raw_value}, filtered value: {filtered_value}, color: {scaled_color}")
            else:
                pixels[i] = (0, 0, 0)
                pixels.show()
    sleep(0.01)
