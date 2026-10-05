# AVR Slopgrammer

A tiny micropython based programmer for the ATtiny13 for the pi pico w.

On boot-up the pico programmer will flash the `prog.bin` file placed inside the pico's littlefs partition and verify it.

## Pinout

The ATtiny runs on 3.3V, same as the pico

MOSI:  GP2
MISO:  GP3
SCK:   GP4
RESET: GP5