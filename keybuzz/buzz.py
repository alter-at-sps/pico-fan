import machine
import math
import utime

# buzz-buzz

buzzer = machine.PWM(machine.Pin(1)) # Setup GP15 as the pin controlling the buzzer with a PWM output
buzzer.freq(1000) # set the frequency of the PWM signal driving the buzzer to 1 kHz

buzzer.duty_u16(32767) # Set a 50% duty cycle for the buzzer to produce a consistent tone

# input

sw2 = machine.Pin(6, machine.Pin.IN, machine.Pin.PULL_UP)
sw1 = machine.Pin(7, machine.Pin.IN, machine.Pin.PULL_UP)
sw0 = machine.Pin(8, machine.Pin.IN, machine.Pin.PULL_UP)

freq = 1000
duty = 0

while True:
    n_presses = 0
    new_freq = 0

    utime.sleep_ms(1)

    if not sw0.value():
        new_freq += 400
        n_presses += 1
    if not sw1.value():
        new_freq += 800
        n_presses += 1
    if not sw2.value():
        new_freq += 1600
        n_presses += 1

    duty = int(duty * .98)
    buzzer.duty_u16(int(duty * (1. + .2 * math.sin(utime.ticks_ms() / 100))))

    if n_presses == 0:
        continue

    freq = new_freq // n_presses
    duty = 32767

    buzzer.freq(freq)