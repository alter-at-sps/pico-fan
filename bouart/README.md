# Button-over-UART

Mirror the state of a button over UART on a different pico, `urx.py` is the receive side which will toggle a led based on the uart bus data.

Only connect a led across GPIO1 to Ground, resistor is not needed. The UART is connected over pins GPIO4 and GPIO5 as tx and rx pins respectively (only the rx pin is truly necessary). A connected Ground might also be required for stable communication.