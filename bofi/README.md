# Button-over-WiFi

Mirror the state of a button over WiFi on a different pico, `wrx.py` is the receive side which will toggle a led based on *properly formated* wifi udp packets data. This completes task 5.

The project needs an external Wifi AP, as the Pico AP mode seems to not be close to usable, make sure to change the correct `ssid` and `cred` when trying to run in your environment.

Only connect a led across GPIO1 to Ground, resistor is not needed.

`wtx.py` is the transmit side:
> Při změně stavu tlačítka odešle přes Wi‑Fi pomocí UDP textový příkaz do druhé jednotky Pico. Stisknuté tlačítko vyšle příkaz k vypnutí LED; uvolněné tlačítko příkaz k jejímu zapnutí.
> 
> GP0 (1) -> tlačítko -> GND (3)