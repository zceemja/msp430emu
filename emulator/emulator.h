
#ifndef _EMULATOR_H_
#define _EMULATOR_H_

#include <stdio.h>
#include <time.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>
#include <stdint.h>
#include <signal.h>
#include <sys/wait.h>
#include <errno.h>
#include <stdbool.h>
#include <pthread.h>
#include <readline/readline.h>
#include <readline/history.h>

#ifdef WEBSOCKETS
#include <libwebsockets.h>
#endif

typedef struct Emulator Emulator;

typedef struct Cpu Cpu;
typedef struct Port_1 Port_1;
typedef struct Usci Usci;
typedef struct Bcm Bcm;
typedef struct Timer_a Timer_a;
typedef struct Status_reg Status_reg;

typedef struct Debugger Debugger;
typedef struct Server Server;
typedef struct Packet Packet;

#include "devices/peripherals/bcm.h"
#include "devices/peripherals/timer_a.h"
#include "devices/peripherals/port1.h"
#include "devices/peripherals/usci.h"
#include "devices/cpu/registers.h"
#include "devices/utilities.h"
#include "devices/memory/memspace.h"

#ifdef WEBSOCKETS
#include "debugger/websockets/emu_server.h"
#endif

#include "devices/cpu/decoder.h"
#include "debugger/debugger.h"
#include "debugger/register_display.h"
#include "debugger/disassembler.h"

#ifdef PYTHON
#include "python/py_interface.h"
#endif

struct Emulator {
    Cpu *cpu;
    Debugger *debugger;
};

#endif