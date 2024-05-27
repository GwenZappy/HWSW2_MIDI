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
    """Map value using exponential mapping to increase sensitivity at lower range."""
    range_ratio = (value - from_low) / (from_high - from_low)
    exp_ratio = range_ratio ** 0.5  # Apply square root to increase sensitivity
    mapped_value = (exp_ratio * (to_high - to_low)) + to_low
    return max(min(mapped_value, to_high), to_low)  # Clamp the value to ensure it stays within range

def low_pass_filter(new_value, last_value, alpha=0.3):
    """Apply low-pass filter to smooth the signal."""
    return alpha * new_value + (1 - alpha) * last_value

# Setup NeoPixel strip
pixel_pin = board.D18
num_pixels = 6  # Adjust to six pixels
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, auto_write=False)

# Define fixed colors for each pixel
base_colors = [
    (255, 0, 0),   # redfor pixel 1
    (0, 255, 0),   # Green for pixel 2
    (0, 0, 255),   # blue for pixel 3
    (0, 255, 255), # Yellow for pixel 4
    (255, 255, 0),   # Cyan for pixel 5
    (255, 0, 128)    # Magenta for pixel 6
]

# Setup thresholds and timing for each sensor
thresholds = [50] * 6  # Same threshold for simplicity, adjust per sensor as needed
max_raw_value = 1023
debounce_time = 0.1
last_impact_time = [0] * 6
last_filtered_value = [0] * 6

# Function to handle each LED separately
def handle_led(sensor_index):
    current_time = time()
    raw_value = read_adc(sensor_index)
    filtered_value = low_pass_filter(raw_value, last_filtered_value[sensor_index])
    last_filtered_value[sensor_index] = filtered_value

    print(f"Sensor {sensor_index+1}: raw_value={raw_value}, filtered_value={filtered_value}")

    if current_time - last_impact_time[sensor_index] > debounce_time:
        if filtered_value > thresholds[sensor_index]:
            last_impact_time[sensor_index] = current_time
            brightness = int(map_value(filtered_value, thresholds[sensor_index], max_raw_value, 0, 255))
            base_color = base_colors[sensor_index]
            color = (
                int(base_color[0] * (brightness / 255)),
                int(base_color[1] * (brightness / 255)),
                int(base_color[2] * (brightness / 255))
            )
            pixels[sensor_index] = color
            print(f"Impact detected on sensor {sensor_index+1} with color: {color}")
        else:
            pixels[sensor_index] = (0, 0, 0)  # Turn off the pixel if no impact is detected
            print(f"No impact detected on sensor {sensor_index+1}, turning off pixel.")

# Main loop
while True:
    handle_led(0)
    handle_led(1)
    handle_led(2)
    handle_led(3)
    handle_led(4)
    handle_led(5)
    pixels.show()  # Update all pixels once per loop iteration
    sleep(0.01)  # Sleep to reduce CPU usage
