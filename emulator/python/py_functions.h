

#ifndef _PY_FUNCTIONS_H_
#define _PY_FUNCTIONS_H_

#include "../emulator.h"
#include "py_interface.h"

void play_emu();
void pause_emu();
void cmd_emu(char *line, int len);
void start_emu(char *file);
void stop_emu();
void reset_emu();

#endif