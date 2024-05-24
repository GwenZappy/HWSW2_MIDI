import spidev
from time import sleep, time
import board
import neopixel
import math
import statistics

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

def low_pass_filter(new_value, last_value, alpha=0.1):
    """Apply low-pass filter to smooth the signal."""
    return alpha * new_value + (1 - alpha) * last_value

def moving_average(values, window_size=5):
    """Calculate moving average to smooth the signal."""
    if len(values) < window_size:
        return sum(values) / len(values)
    else:
        return sum(values[-window_size:]) / window_size

# Setup NeoPixel strip
pixel_pin = board.D18
num_pixels = 2 # Only two pixels are controlled
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, auto_write=False)

# Setup thresholds and timing for each sensor
threshold_1 = 100
threshold_2 = 100
max_raw_value = 1023
debounce_time = 0.1  # Cooldown period to prevent multiple detections
last_impact_time_1 = 0
last_impact_time_2 = 0
last_filtered_value_1 = 0  # Initial value for the low-pass filter
last_filtered_value_2 = 0

# Moving average window for smoothing
window_size = 5
values_1 = []
values_2 = []

# Calibrate this based on experimental observations
to_low = 0.1  # Adjust this value to the lowest visible brightness on your NeoPixels
to_high = 1.0  # Maximum brightness for the strongest impact

# Main loop
while True:
    current_time = time()
    raw_value_1 = read_adc(0)  # Read from first piezo sensor
    raw_value_2 = read_adc(1)  # Read from second piezo sensor
    
    # Append raw values to the moving average window
    values_1.append(raw_value_1)
    values_2.append(raw_value_2)
    
    # Apply moving average filter
    avg_value_1 = moving_average(values_1, window_size)
    avg_value_2 = moving_average(values_2, window_size)
    
    # Apply low-pass filter to smooth the readings
    filtered_value_1 = low_pass_filter(avg_value_1, last_filtered_value_1)
    filtered_value_2 = low_pass_filter(avg_value_2, last_filtered_value_2)
    
    last_filtered_value_1 = filtered_value_1  # Update the last filtered value for sensor 1
    last_filtered_value_2 = filtered_value_2  # Update the last filtered value for sensor 2

    # Check for impact on the first sensor
    if current_time - last_impact_time_1 > debounce_time:
        if filtered_value_1 > threshold_1:
            last_impact_time_1 = current_time  # Update time of last impact for sensor 1
            brightness_1 = map_value(filtered_value_1, threshold_1, max_raw_value, 0.1, 1.0)
            pixels[0] = (200, 100, 0)  # First pixel color
            pixels.show()
            print(f"sensor1 impact detected {raw_value_1}")
        else:
            pixels[0] = (0, 0, 0)  # Turn off the first pixel
            pixels.show()
            print(f"sensor1 impact detected {raw_value_1}")  # Print even when no impact detected

    # Check for impact on the second sensor
    if current_time - last_impact_time_2 > debounce_time:
        if filtered_value_2 > threshold_2:
            last_impact_time_2 = current_time  # Update time of last impact for sensor 2
            brightness_2 = map_value(filtered_value_2, threshold_2, max_raw_value, 0.1, 1.0)
            pixels[1] = (0, 200, 100)  # Second pixel color
            pixels.show()
            print(f"sensor2 impact detected {raw_value_2}")
        else:
            pixels[1] = (0, 0, 0)  # Turn off the second pixel
            pixels.show()
            print(f"sensor2 impact detected {raw_value_2}")  # Print even when no impact detected

    sleep(0.01)  # Sleep to reduce CPU usage
