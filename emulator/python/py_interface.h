

#ifndef _PY_INTERFACE_H_
#define _PY_INTERFACE_H_

#include "py_functions.h"
#include <Python.h>

void print_serial (Emulator *emu, char *buf);
void print_console (Emulator *emu, const char *buf);
void send_control (Emulator *emu, uint8_t opcode, void *data, size_t size);

#endif