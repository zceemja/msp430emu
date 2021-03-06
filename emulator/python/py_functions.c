#include "py_functions.h"

#ifdef _MSC_VER
#include <Windows.h>
#else
#include <time.h>
#endif

uint64_t getnano() {
#ifdef _MSC_VER
    static LARGE_INTEGER frequency;
    if (frequency.QuadPart == 0) QueryPerformanceFrequency(&frequency);
    LARGE_INTEGER now;
    QueryPerformanceCounter(&now);
    double x = (double)now.QuadPart / (double)frequency.QuadPart;
    return (uint64_t)(x * 1000000000.0);
#else
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    return now.tv_sec * 1000000000 + now.tv_nsec;
#endif
}

// This is an ugly solution but heh
Emulator *emuInst = NULL;

void play_emu() {
    emuInst->cpu->running = true;
    emuInst->debugger->debug_mode = false;
}

void pause_emu() {
    if (emuInst->cpu->running) {
        emuInst->cpu->running = false;
        emuInst->debugger->debug_mode = true;

         // display first round of registers
//         display_registers(emu);
//         disassemble(emu, cpu->pc, 1);
//         update_register_display(emu);
    }
}

void reset_emu() {
    if(emuInst == NULL) return;
    cpu_reset(emuInst);
    print_console(emuInst, "CPU Reset\n");
}

void set_reg(uint8_t reg_type, uint8_t value) {
    if(emuInst == NULL) return;
    Port_1 *p = emuInst->cpu->p1;
    switch(reg_type) {
    case SET_REG_P1_EN:
    p->EXT_EN = value;
    break;
    case SET_REG_P1_DIR:
    p->EXT_DIR = value;
    break;
    }
}

PyObject *get_misc_data() {
    if(emuInst == NULL) return Py_None;
    Cpu *cpu = emuInst->cpu;
    Bcm *bcm = cpu->bcm;
    PyObject *dict = PyDict_New();
    PyDict_SetItemString(dict, "period", PyLong_FromUnsignedLongLong(cpu->nsecs));
    PyDict_SetItemString(dict, "mclk", PyLong_FromUnsignedLongLong(bcm->mclk_freq));
    PyDict_SetItemString(dict, "aclk", PyLong_FromUnsignedLongLong(bcm->aclk_freq));
    PyDict_SetItemString(dict, "smclk", PyLong_FromUnsignedLongLong(bcm->smclk_freq));
    PyDict_SetItemString(dict, "uart_baud", PyLong_FromUnsignedLong(cpu->usci->UART_baud));
    PyDict_SetItemString(dict, "timer_a0_freq", PyFloat_FromDouble(cpu->timer_a->timer_0_freq));
    PyDict_SetItemString(dict, "timer_a0_duty", PyFloat_FromDouble(cpu->timer_a->timer_0_duty));
    uint8_t pwm_pins = ~*cpu->p1->_OUT & *cpu->p1->_SEL & ~*cpu->p1->_SEL2;
    PyDict_SetItemString(dict, "timer_pwm_pins", PyBytes_FromStringAndSize(&pwm_pins, 1));

    return dict;
}

PyObject *get_port1_regs() {
    if(emuInst == NULL) return Py_None;
    char regs[9];
    Port_1 *p = emuInst->cpu->p1;
    regs[0] = *p->_OUT;
    regs[1] = *p->_DIR;
    regs[2] = *p->_IFG;
    regs[3] = *p->_IES;
    regs[4] = *p->_IE;
    regs[5] = *p->_SEL;
    regs[6] = *p->_SEL2;
    regs[7] = *p->_REN;
    regs[8] = *p->_IN;
    return PyBytes_FromStringAndSize(regs, 9);
}

PyObject *get_cpu_regs() {
    if(emuInst == NULL) return Py_None;
    Cpu *cpu = emuInst->cpu;
    uint16_t regs[] = {
        cpu->pc, cpu->sp, sr_to_value(emuInst), cpu->cg2,
        cpu->r4, cpu->r5, cpu->r6, cpu->r7,
        cpu->r8, cpu->r9, cpu->r10, cpu->r11,
        cpu->r12, cpu->r13, cpu->r14, cpu->r15
    };
    return PyBytes_FromStringAndSize((char *)regs, sizeof(regs));
}

PyObject *get_bcm_regs() {
    if(emuInst == NULL) return Py_None;
    char regs[6];
    Bcm *bcm = emuInst->cpu->bcm;
    regs[0] = *bcm->DCOCTL;
    regs[1] = *bcm->BCSCTL1;
    regs[2] = *bcm->BCSCTL2;
    regs[3] = *bcm->BCSCTL3;
    regs[4] = *bcm->IE1;
    regs[5] = *bcm->IFG1;

    return PyBytes_FromStringAndSize(regs, 6);
}

PyObject *get_timer_regs() {
    if(emuInst == NULL) return Py_None;
    uint16_t regs[18];
    Timer_a *timer = emuInst->cpu->timer_a;
    regs[0] = *timer->TA0CTL;
    regs[1] = *timer->TA0R;
    regs[2] = *timer->TA0CCTL0;
    regs[3] = *timer->TA0CCR0;
    regs[4] = *timer->TA0CCTL1;
    regs[5] = *timer->TA0CCR1;
    regs[6] = *timer->TA0CCTL2;
    regs[7] = *timer->TA0CCR2;
    regs[8] = *timer->TA0IV;

    regs[9] = *timer->TA1CTL;
    regs[10] = *timer->TA1R;
    regs[11] = *timer->TA1CCTL0;
    regs[12] = *timer->TA1CCR0;
    regs[13] = *timer->TA1CCTL1;
    regs[14] = *timer->TA1CCR1;
    regs[15] = *timer->TA1CCTL2;
    regs[16] = *timer->TA1CCR2;
    regs[17] = *timer->TA1IV;

    return PyBytes_FromStringAndSize((char*)regs, 18*2);
}

PyObject *get_usci_regs() {
    if(emuInst == NULL) return Py_None;
    char regs[12];
    Usci *usci = emuInst->cpu->usci;
    regs[0] = *usci->UCA0CTL0;
    regs[1] = *usci->UCA0CTL1;
    regs[2] = *usci->UCA0BR0;
    regs[3] = *usci->UCA0BR1;
    regs[4] = *usci->UCA0MCTL;
    regs[5] = *usci->UCA0STAT;
    regs[6] = *usci->UCA0RXBUF;
    regs[7] = *usci->UCA0TXBUF;
    regs[8] = *usci->UCA0ABCTL;
    regs[9] = *usci->UCA0IRTCTL;
    regs[10] = *usci->UCA0IRRCTL;
    regs[11] = *usci->IFG2;

    return PyBytes_FromStringAndSize(regs, 12);
}

void cmd_emu(char *line, int len) {
    if(emuInst == NULL) return;
    if (!emuInst->cpu->running && emuInst->debugger->debug_mode) {
        exec_cmd(emuInst, line, len);
//	         update_register_display(emu);
    }
}

void stop_emu() {
    if(emuInst == NULL) return;
    emuInst->debugger->quit = true;
    print_console(emuInst, "Stopping emulator..\n");
}


void write_serial(uint8_t *data, int len) {
    if(emuInst == NULL) return;
    set_uart_buf(emuInst, data, len);
////    int i = 0;
////    uint8_t *bytes = data;
//    *usci->UCA0RXBUF = data[0];
//    *usci->IFG2 |= RXIFG;
//    puts("Setting interrupt");
//    service_interrupt(emuInst, USCIAB0RX_VECTOR);
//    printf("len is %d\n", len);
//    for(int i=0; i < len; i++) {
//        usleep(333);
//        printf("waiting.. ");
//        while (*usci->IFG2 & RXIFG) {
//            usleep(333);
//            if(emuInst->debugger->quit) {
//                puts("debugger stopped");
//                return;
//            }
//        }
////        uint8_t thing = *(bytes);
//        *usci->UCA0RXBUF = data[i];
//        *usci->IFG2 |= RXIFG;
//        printf("0x%04X in UCA0RXBUF\n", (uint8_t)*usci->UCA0RXBUF);
//        printf("waiting.. ");
//        while (*usci->IFG2 & RXIFG) {
//            usleep(333);
//            if(emuInst->debugger->quit) {
//                puts("debugger stopped");
//                return;
//            }
//        }
//        puts("done\n");
//    }


//    while (true) {
//        usleep(333);
//        while (*usci->IFG2 & RXIFG);
//        uint8_t thing = *(bytes);
//
////        if (thing == '\n') {
////          thing = '\r';
////        }
//        *usci->UCA0RXBUF = thing;
//        *usci->IFG2 |= RXIFG;
//
//        //printf("\n0x%04X in UCA0RXBUF\n", (uint8_t)*usci->UCA0RXBUF);
//        //puts("waiting..");
//        while (*usci->IFG2 & RXIFG);
//        //puts("done");
//        //*usci->IFG2 |= RXIFG;
//        if (*usci->UCA0RXBUF == '\r' || *usci->UCA0RXBUF == '\n') break;
//        ++bytes;
//      }
}

void start_emu(char *file) {
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

//    deb->server = (Server *) calloc(1, sizeof(Server));

    initialize_msp_memspace();
    initialize_msp_registers(emuInst);

    setup_bcm(emuInst);
    setup_timer_a(emuInst);
    setup_port_1(emuInst);
    setup_usci(emuInst);

    print_console(emuInst, "[MSP430 Emulator]\n Copyright (C) 2020 Rudolf Geosits (rgeosits@live.esu.edu)\n");

    load_bootloader(0x0C00);
    if(load_firmware(emuInst, file, 0xC000) == 0) {
        //    display_registers(emuInst);
        disassemble(emuInst, cpu->pc, 1);
        //    update_register_display(emuInst);

        uint16_t counter = 0;
        uint64_t time_delta = 0;
        uint64_t time_last = getnano();

        while (!deb->quit) {
            // Handle debugger when CPU is not running
            if (!cpu->running) {
                counter = 0;
                time_delta = 0;
                time_last = getnano();
                usleep(10000);
                continue;
            }

            // Handle Breakpoints
            //handle_breakpoints(emuInst);
            cpu_step(emuInst);

            counter++;
            if(counter > 500) {
                uint64_t time_now = getnano();
                if(cpu->bcm->mclk_period == 0) break;

                // Average of 4 cycles per instruction
                uint64_t cycles_time = cpu->bcm->cpu_period * 500;
                uint64_t delta = time_now - time_last;
                if(time_last > time_now) delta = 0;
                uint64_t sleep_time = cycles_time - delta;
                if(delta > cycles_time) {
                    time_delta += (delta - cycles_time);
                } else if(time_delta > sleep_time) {
                    time_delta -= sleep_time;
                } else {
                    sleep_time += time_delta;
                    time_delta = 0;
                    usleep(sleep_time/1000);
                }
                time_last = time_now;
                counter = 0;
            }
        }
    }

    uninitialize_msp_memspace();
    free(cpu->usci->UART_buf_data);
    free(cpu->timer_a);
    free(cpu->bcm);
    free(cpu->p1);
    free(cpu->usci);
    free(cpu);
    free(deb->server);
    free(deb);
    free(emuInst);

    return;
}

//void init_packet_queue (Emulator *emu){
//    Server *s = emu->debugger->server;
//    s->pending_packets_head = NULL;
//    s->pending_packets_tail = NULL;
//    s->packets_queued = 0;
//    s->spin_lock = false;
//}


//void *emulator (void *ctxt) {
//    emu = (Emulator *) ctxt;
//    Debugger *deb = emu->debugger;
//
//    init_packet_queue(emu);
//    printf("starting emulator...\n");
//}