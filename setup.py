#!/usr/bin/env python
from setuptools.dist import Distribution
from distutils.core import setup, Extension


emulator_files = [
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
    'emulator/debugger/disassembler.c',
    'emulator/python/py_functions.c',
    'emulator/python/py_interface.c',
    'emulator/win.c',
]


class BinaryDistribution(Distribution):
    def is_pure(self):
        return False


setup(name='msp430emu',
      version='0.2',
      description='MSP 430 Emulator',
      author_email='zceemja@ucl.ac.uk',
      packages=['msp430emu'],
      package_dir={'msp430emu': 'msp430emu'},
      package_data={'msp430emu': ['*.png']},
      include_package_data=True,
      ext_modules=[Extension(
          '_msp430emu', emulator_files, extra_compile_args=["-w", "-DPYTHON"]
      )],
      distclass=BinaryDistribution,
      install_requires=[
          "wxPython >= 4",
      ],
      )
