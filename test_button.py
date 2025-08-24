from gpiozero import Button
from signal import pause

button = Button(21, pull_up=True, bounce_time=0.1)

button.when_pressed = lambda: print("Button Pressed______________")
button.when_released = lambda: print("Button released")

pause()
