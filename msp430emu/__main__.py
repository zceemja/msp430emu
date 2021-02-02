from msp430emu import emulator
import sys
import os

if __name__ == '__main__':
    load = None
    if len(sys.argv) >= 2:
        if os.path.exists(sys.argv[1]):
            load = sys.argv[1]
        else:
            print(f"File '{sys.argv[1]}' does not exist")
    emulator.run(load)
