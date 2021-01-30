#!/usr/bin/env python
from distutils.core import setup, Extension

emulator_files = [
    'emulator/main.c',
    'emulator/devices/utilities.c',
    'emulator/devices/cpu/registers.c',
    'emulator/devices/memory/memspace.c',
    'emulator/debugger/debugger.c',
    'emulator/debugger/register_display.c',
    'emulator/devices/cpu/decoder.c',
    'emulator/devices/cpu/flag_handler.c',
    'emulator/devices/cpu/formatI.c',
    'emulator/devices/cpu/formatII.c',
    'emulator/devices/cpu/formatIII.c',
    'emulator/devices/peripherals/bcm.c',
    'emulator/devices/peripherals/timer_a.c',
    'emulator/devices/peripherals/usci.c',
    'emulator/devices/peripherals/port1.c',
    'emulator/debugger/websockets/emu_server.c',
    'emulator/debugger/websockets/packet_queue.c',
    'emulator/debugger/disassembler.c',
]
libraries = [
    'websockets',
    'readline',
    'rt',
    'ssl',
    'crypto',
    'pthread'
]
ext_mod = Extension(
    '_msp430emu', emulator_files, libraries=libraries, extra_compile_args=["-w"]
)

setup(name='msp430emu',
      version='1.0',
      description='MSP 430 Emulator',
      author_email='zceemja@ucl.ac.uk',
      packages=['msp430emu'],
      package_dir={'msp430emu': 'msp430emu'},
      package_data={'msp430emu': ['*.png']},
      ext_modules=[ext_mod],
      )
