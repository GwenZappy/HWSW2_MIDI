import math
import time
import pygame
import spidev
import board
import neopixel

# Initialize pygame mixer
pygame.init()
pygame.mixer.init()
drum_sound = pygame.mixer.Sound("kick1.wav")
drum_intensity_sound = pygame.mixer.Sound("kick1.wav")

# Setup SPI for MCP3008
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

# Setup NeoPixel
pixel_pin = board.D18
num_pixels = 6
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, auto_write=True)

# Define timing for the notes
note_times = [1, 2, 3, 5, 7]
tolerance = 0.5

# Setup thresholds and other parameters
threshold = 100
max_raw_value = 1023

# Low-pass filter alpha value
alpha = 0.5

# Last filtered value
last_filtered_value = 0

# Debounce parameters
debounce_time = 0.3  # 100 ms debounce time
last_press_time = 0


def read_channel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data


def map_value(value, from_low, from_high, to_low, to_high):
    # Ensure the input value is within the expected range
    value = max(from_low, min(value, from_high))
    range_ratio = (value - from_low) / (from_high - from_low)
    exp_ratio = math.sqrt(range_ratio)  # Use sqrt to avoid complex numbers
    mapped_value = (exp_ratio * (to_high - to_low)) + to_low
    return max(to_low, min(mapped_value, to_high))  # Clamp to the output range


def low_pass_filter(new_value, last_value, alpha):
    return alpha * new_value + (1 - alpha) * last_value


def play_sequence():
    start_time = time.time()
    for note_time in note_times:
        while time.time() < start_time + note_time:
            time.sleep(0.01)
        pixels.fill((255, 0, 0))  # Turn all pixels red
        pixels.show()
        drum_sound.play()  # Play the drum sound when LED lights up
        time.sleep(0.1)  # LED on duration
        pixels.fill((0, 0, 0))  # Turn off all pixels
        pixels.show()


def record_responses():
    start_time = time.time()
    scores = []
    response_times = []
    last_second = 0

    while time.time() - start_time < 10:
        current_time = time.time() - start_time
        current_second = int(current_time)

        if current_second != last_second:  # Print every new second
            print(f"{current_second} second(s)")
            last_second = current_second

        sensor_value = read_channel(0)

        if sensor_value > threshold:  # Threshold for sensor press
            response_times.append(current_time)
            pixels.fill((0, 255, 0))  # Turn all pixels green
            pixels.show()
            drum_sound.play()  # Play the drum sound on sensor press
            time.sleep(0.1)  # LED feedback on sensor press
            pixels.fill((0, 0, 0))  # Turn off all pixels
            pixels.show()
            while read_channel(0) > 800:  # Debounce by waiting for release
                time.sleep(0.01)

    for note_time in note_times:
        scores.append(any(abs(note_time - t) <= tolerance for t in response_times))

    return scores


def lesson_rhythm():
    username = input("Enter your username to start the rhythm lesson: ")
    print("Lesson 1: Rhythm. Follow the LED and press on time.")
    input("Press Enter when ready to start...")
    print("Starting in 3 seconds...")
    time.sleep(1)
    print("2 seconds...")
    time.sleep(1)
    print("1 second...")
    time.sleep(1)
    play_sequence()
    print("Now, follow the sequence. Press on the seconds indicated starting in 3 seconds...")
    time.sleep(1)
    print("2 seconds...")
    time.sleep(1)
    print("1 second...")
    time.sleep(1)
    print("Start!")
    scores = record_responses()
    score = sum(scores)
    print(f"Your score: {score}/{len(note_times)}")


def lesson_intensity():
    print(
        "Lesson 2: Intensity. The volume and brightness will vary based on how hard you press the piezo sensor."
    )
    input("Press Enter when ready to start experimenting...")
    print(
        "Hit the piezo sensor with different intensities to test changes. Press CTRL+C to exit."
    )
    try:
        global last_filtered_value, last_press_time  # Ensure we modify the global values
        while True:
            sensor_value = read_channel(0)
            filtered_value = low_pass_filter(sensor_value, last_filtered_value, alpha)
            last_filtered_value = filtered_value

            brightness = map_value(filtered_value, threshold, max_raw_value, 0, 255)
            brightness = int(brightness)  # Ensure brightness is an integer
            pixels.fill((brightness, 0, 0))  # Adjust NeoPixel brightness
            pixels.show()

            current_time = time.time()
            if filtered_value > threshold and (current_time - last_press_time) > debounce_time:  # Debounce check
                last_press_time = current_time
                normalized_value = filtered_value / 1023  # Normalize the filtered value to a 0.0-1.0 range
                drum_intensity_sound.set_volume(normalized_value)
                drum_intensity_sound.play()
                print(
                    f"Sensor Value: {sensor_value} | Filtered Value: {filtered_value} | LED Brightness: {brightness}"
                )
            time.sleep(0.01)  # Shorter delay to avoid missing impacts
    except KeyboardInterrupt:
        pass
    finally:
        pixels.fill((0, 0, 0))  # Turn off all pixels
        pixels.show()



def main():
    while True:
        print("\nMenu:")
        print("1. Lesson 1: Rhythm")
        print("2. Lesson 2: Intensity")
        choice = input("Enter 1 or 2 to select a lesson, or 'exit' to quit: ")
        if choice == "1":
            lesson_rhythm()
        elif choice == "2":
            lesson_intensity()
        elif choice == "exit":
            break
        else:
            print("Invalid selection. Please choose 1, 2, or 'exit'.")


if __name__ == "__main__":
    try:
        main()
    finally:
        spi.close()
        pygame.quit()
