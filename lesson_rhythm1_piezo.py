import sys
import signal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import pygame
import spidev
import RPi.GPIO as GPIO
import board
import neopixel
from time import sleep, time

# Signal handler to catch interrupts
def signal_handler(sig, frame):
    print('Interrupt received, exiting...')
    QApplication.quit()

signal.signal(signal.SIGINT, signal_handler)

# Initialize pygame and SPI
pygame.init()
pygame.mixer.init()
drum_sound = pygame.mixer.Sound("kick1.wav")

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000
spi.mode = 0

# Setup NeoPixel
pixel_pin = board.D18
num_pixels = 6
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, auto_write=False)

# Define timing for the notes
note_times = [1, 2, 3, 5, 7]
tolerance = 0.5

# Read from ADC channel
def read_channel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

# Play sequence
def play_sequence():
    start_time = time()
    for note_time in note_times:
        while time() < start_time + note_time:
            sleep(0.01)
        pixels.fill((0, 255, 255))  # Turn all pixels red
        pixels.show()
        drum_sound.play()  # Play the drum sound when LED lights up
        sleep(0.1)  # LED on duration
        pixels.fill((0, 0, 0))  # Turn off all pixels
        pixels.show()

# Record responses
def record_responses():
    start_time = time()
    scores = []
    response_times = []

    while time() - start_time < 10:
        current_time = time() - start_time
        sensor_value = read_channel(0)

        if sensor_value > 800:  # Threshold for sensor press
            response_times.append(current_time)
            pixels.fill((255, 0, 255))  # Turn all pixels green
            pixels.show()
            drum_sound.play()  # Play the drum sound on sensor press
            sleep(0.1)  # LED feedback on sensor press
            pixels.fill((0, 0, 0))  # Turn off all pixels
            pixels.show()
            while read_channel(0) > 800:  # Debounce by waiting for release
                sleep(0.01)

    # Check each response time against the expected times
    for note_time in note_times:
        scores.append(any(abs(note_time - t) <= tolerance for t in response_times))

    return scores

# RhythmLesson class
class RhythmLesson(QThread):
    progress = pyqtSignal(str)
    sequence_complete = pyqtSignal()
    score_signal = pyqtSignal(str)

    def __init__(self, username):
        super().__init__()
        self.username = username

    def run(self):
        play_sequence()
        self.sequence_complete.emit()
        scores = record_responses()
        score = sum(scores)
        self.score_signal.emit(f"Your score: {score}/{len(note_times)}")
'''
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Setup a QTimer to periodically check for signals
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Dummy slot to keep the event loop responsive
    timer.start(100)

    username = "Player1"
    lesson = RhythmLesson(username)
    lesson.progress.connect(print)
    lesson.score_signal.connect(print)
    lesson.start()
    
    signal.signal(signal.SIGINT, signal_handler)

    app.exec_()
    lesson.wait()  # Ensure the thread is properly terminated
    sys.exit()'''