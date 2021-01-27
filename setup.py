#!/usr/bin/env python

from distutils.core import setup, Extension

emulator_files = [
    'emulator/main.cpp',
    'emulator/devices/utilities.c',
    'emulator/devices/cpu/registers.c',
    'emulator/devices/memory/memspace.c',
    'emulator/debugger/debugger.c',
    'emulator/debugger/disassembler.c',
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
    'emulator/debugger/websockets/emu_server.cpp',
    'emulator/debugger/websockets/packet_queue.c',
]
# emulator_files.reverse()

setup(name='msp430emu',
      version='1.0',
      description='MSP 430 Emulator',
      author_email='zceemja@ucl.ac.uk',
      # packages=['msp430emu'],
      # package_dir={'msp430emu': '', 'emulator': 'emulator'},
      # libraries=['wx', 'websocket'],
      ext_modules=[Extension('emulator', emulator_files)]
      )
