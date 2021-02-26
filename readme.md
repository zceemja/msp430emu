# MSP430 Emulator with GUI

A python wrapper for MSP430 emulator. Emulator itself has been taken from 
[https://github.com/RudolfGeosits/MSP430-Emulator](https://github.com/RudolfGeosits/MSP430-Emulator)

It has been modified to work without websocket or any other 3rd party libraries, enabling it to be easily compiled on any platform.
## Setup

More detailed description for multiple platforms will be added.

Install latest via pip:
```bash
pip install https://github.com/zceemja/msp430emu/archive/master.zip
```

## Work Done

List of features that are added:

- [x] Source build on linux
- [x] Source build on windows
- [x] Source build on mac
- [x] Working Emulator
- [x] Python GUI
- [x] Blinking LEDs
- [x] UART Serial output
- [ ] UART Serial input
- [x] Reset button
- [x] Button for P1.3
- [x] Interrupts
- [ ] Timer A
- [ ] PWM Signals
- [x] Unbiased circuit simulation (due to internal pull-up/down resistors)
- [ ] Watchdog Timer
- [ ] GPIO Oscilloscope
- [ ] Port 2 GPIO
- [ ] Invalid register configuration checks
- [ ] Information about UART Band
- [ ] ADC
