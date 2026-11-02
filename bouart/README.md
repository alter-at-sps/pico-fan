# Button-over-UART

Mirror the state of a button over UART on a different pico, `urx.py` is the receive side which will toggle a led based on the uart bus data. This completes task 3

Only connect a led across GPIO1 to Ground, resistor is not needed. The UART is connected over pins GPIO4 and GPIO5 as tx and rx pins respectively (only the rx pin is truly necessary). A connected Ground might also be required for stable communication.

`utx.py` is the transmit side:
> Při změně stavu tlačítka odešle jeho hodnotu ('0' nebo '1') přes UART do druhé jednotky Pico.
> 
> GP0 (1) -> tlačítko -> GND (3)
> 
> UART1 TX (6) -> UART1 RX (Pico In, 7)
> UART1 TX (Pico In, 6) -> UART1 RX (7)
> GND (3) -> GND (Pico In, 3)