import machine
import math
import utime

ADC_ENA = False

# buzz-buzz

buzzer = machine.PWM(machine.Pin(0)) # Setup GP0 as the pin controlling the buzzer with a PWM output
buzzer.freq(1000) # set the frequency of the PWM signal driving the buzzer to 1 kHz

buzzer.duty_u16(32767) # Set a 50% duty cycle for the buzzer to produce a consistent tone

# input

sw2 = machine.Pin(6, machine.Pin.IN, machine.Pin.PULL_UP)
sw1 = machine.Pin(7, machine.Pin.IN, machine.Pin.PULL_UP)
sw0 = machine.Pin(8, machine.Pin.IN, machine.Pin.PULL_UP)

if ADC_ENA:
    adc_gnd = machine.Pin(28, machine.Pin.OUT)
    adc = machine.ADC(1)

    # hard-pull pin to ground to act as the sink for the potenciometer
    adc_gnd.value(0)

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
    buzzer.duty_u16(int(duty * (1. + .2 * math.sin(utime.ticks_ms() / 100)))) # some spice

    if n_presses == 0:
        continue

    freq = new_freq // n_presses
    duty = 32767

    if ADC_ENA:
        # fine manual freq tuning
        freq += (adc.read_u16() - (65535 // 2)) // 100

    buzzer.freq(freq)