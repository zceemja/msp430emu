

#ifndef _PY_FUNCTIONS_H_
#define _PY_FUNCTIONS_H_

#include "../emulator.h"
#include "py_interface.h"
#include <Python.h>


#define SET_REG_P1_IN 0x05
#define SET_REG_P2_IN 0x06

#define GET_REG_GP 0x04
#define GET_REG_P1 0x05
#define GET_REG_P2 0x06
#define GET_REG_TIMER_A 0x07
#define GET_REG_USCI 0x08

// This is an ugly solution but heh

void play_emu();
void pause_emu();
void cmd_emu(char *line, int len);
void start_emu(char *file);
void stop_emu();
void reset_emu();
void set_reg(uint8_t reg_type, uint8_t value);
PyObject *get_port1_regs();

#endif