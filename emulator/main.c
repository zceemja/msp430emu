/*
  MSP430 Emulator
  Copyright (C) 2020 Rudolf Geosits (rgeosits@live.esu.edu)
  
  "MSP430 Emulator" is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  "MSP430 Emulator" is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU General Public License for more details.
  
  You should have received a copy of the GNU General Public License
  along with this program. If not, see <https://www.gnu.org/licenses/>.
*/

#include "main.h"
#include <Python.h>

// This is an ugly solution but heh
Emulator *emuInst;

static PyObject *method_run(PyObject *self, PyObject *args) {
    unsigned int port;
    if(!PyArg_ParseTuple(args, "H", &port)) {
        return NULL;
    }
    Py_BEGIN_ALLOW_THREADS
    run(port);
    Py_END_ALLOW_THREADS
    return Py_None;
}

static PyObject *method_stop(PyObject *self, PyObject *args) {
    if(emuInst != NULL) {
        emuInst->debugger->quit = true;
    }
    return Py_None;
}

static PyMethodDef RunMethods[] = {
    {"run", method_run, METH_VARARGS, "Python function to start msp430 emulator"},
    {"stop", method_stop, METH_NOARGS, "Python function to stop msp430 emulator"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef msp430module = {
    PyModuleDef_HEAD_INIT,
    "_msp430emu",
    "Python interface for msp430 emulator",
    -1,
    RunMethods
};

 PyMODINIT_FUNC PyInit__msp430emu(void) {
    return PyModule_Create(&msp430module);
}

int run(unsigned int port) {

    emuInst = (Emulator *) calloc( 1, sizeof(Emulator) );
    Cpu *cpu = NULL; Debugger *deb = NULL;

    emuInst->cpu       = (Cpu *) calloc(1, sizeof(Cpu));
    emuInst->cpu->bcm  = (Bcm *) calloc(1, sizeof(Bcm));
    emuInst->cpu->timer_a  = (Timer_a *) calloc(1, sizeof(Timer_a));
    emuInst->cpu->p1   = (Port_1 *) calloc(1, sizeof(Port_1));
    emuInst->cpu->usci = (Usci *) calloc(1, sizeof(Usci));

    emuInst->debugger  = (Debugger *) calloc(1, sizeof(Debugger));
    setup_debugger(emuInst);

    cpu = emuInst->cpu;
    deb = emuInst->debugger;

    deb->server = (Server *) calloc(1, sizeof(Server));

    if (deb->web_interface == true)
        {
            deb->ws_port = port;

            pthread_t *t = &deb->web_server_thread;

            if ( pthread_create(t, NULL, web_server, (void *)emuInst ) )
            {
                fprintf(stderr, "Error creating web server thread\n");
                return 1;
            }


            while (!deb->web_server_ready)
                usleep(10000);

            print_console(emuInst, " [MSP430 Emulator]\n Copyright (C) 2020 Rudolf Geosits (rgeosits@live.esu.edu)\n");
//            print_console(emuInst, " [!] Upload your firmware (ELF format only); Type 'h' for debugger options.\n\n");

            while (!deb->web_firmware_uploaded)
                usleep(10000);
        }

        //register_signal(SIGINT); // Register Callback for CONTROL-c

        initialize_msp_memspace();
        initialize_msp_registers(emuInst);

        setup_bcm(emuInst);
        setup_timer_a(emuInst);
        setup_port_1(emuInst);
        setup_usci(emuInst);

        load_bootloader(0x0C00);

        if (deb->web_interface)
            load_firmware(emuInst, (char*)"tmp.bin", 0xC000);

        // display first round of registers
        display_registers(emuInst);
        disassemble(emuInst, cpu->pc, 1);
        update_register_display(emuInst);

        // Fetch-Decode-Execute Cycle (run machine)
        while (!deb->quit)
        {
            // Handle debugger when CPU is not running
            if (!cpu->running)
            {
                usleep(10000);
                continue;
            }

            // Handle Breakpoints
            handle_breakpoints(emuInst);

            // Instruction Decoder
            decode(emuInst, fetch(emuInst), EXECUTE);

            // Handle Peripherals
            handle_bcm(emuInst);
            handle_timer_a(emuInst);
            handle_port_1(emuInst);
            handle_usci(emuInst);

            // Average of 4 cycles per instruction
            mclk_wait_cycles(emuInst, 4);
        }
        uninitialize_msp_memspace();
        free(cpu->timer_a);
        free(cpu->bcm);
        free(cpu->p1);
        free(cpu->usci);
        free(cpu);
        free(deb->server);
        free(deb);
        free(emuInst);

        return 0;
}


int main(int argc, char *argv[])
{
    if (argv[1] == NULL)
    {
        puts("Need port argument");
        return(1);
    }
    return run(strtoul(argv[1], NULL, 10));
}
