# AVR Slopgrammer

A tiny micropython based ISP programmer for the ATtiny13 for the pi pico w. This project completes task 1 (the bus is bitbanged) and 3 (it's a spi device).

On boot-up the pico programmer will flash the `prog.bin` file placed inside the pico's littlefs partition and verify it.

## Pinout

The ATtiny runs on 3.3V, same as the pico

MOSI (PB0):  GP2
MISO (PB1):  GP3
SCK (PB2):   GP4
RESET (PB5): GP5