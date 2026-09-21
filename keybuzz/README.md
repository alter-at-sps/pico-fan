# Key-buzz

a mini synth keyboard entirely based on a PWM controlled piezo buzzer. Three tones available with three buttons.

you already heard it. :)

# Schema

Connect a piezo (over a 180 ohm resistor for lower volume) to the gpio1 pin and gnd. then connect three buttons to gpio 6, 7 and 8 respectively and also to gnd (buttons are driven with an internal pull-up).
