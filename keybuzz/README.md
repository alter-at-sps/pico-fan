# Key-buzz

a mini synth keyboard entirely based on a PWM controlled piezo buzzer. Three tones available with three buttons. This project completes task 1 and 2.

Optional ADC support can also be added by flipping `ADC_ENA` to `True` and inserting a potenciometer between the ADC1 pin, GP28 pin and the 3.3V out pin.

you already heard it. :)

# Schema

Connect a piezo (over a 180 ohm resistor for lower volume) to the gpio 0 pin and gnd. then connect three buttons to gpio 6, 7 and 8 respectively and also to gnd (buttons are driven with an internal pull-up).
