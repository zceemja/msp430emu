from msp430emu import emulator
import sys
import os

if __name__ == '__main__':
    load = None
    if len(sys.argv) >= 2:
        load = sys.argv[1]
    emulator.run(load)
