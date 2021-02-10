#include "py_functions.h"
// This is an ugly solution but heh
Emulator *emuInst;

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
    if(!emuInst) return;
    emuInst->cpu->pc = 0xC000;
    print_console(emuInst, "Resetting program counter to 0xC000\n");
}

void set_reg(uint8_t reg_type, uint8_t value) {
    if(!emuInst) return;
    switch(reg_type) {
    case SET_REG_P1_IN:
        *emuInst->cpu->p1->_IN = value;
    }
}

PyObject *get_port1_regs() {
    if(!emuInst) return Py_None;
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

void cmd_emu(char *line, int len) {
    if(!emuInst) return;
    if (!emuInst->cpu->running && emuInst->debugger->debug_mode) {
        exec_cmd(emuInst, line, len);
//	         update_register_display(emu);
    }
}

void stop_emu() {
    if(!emuInst) return;
    emuInst->debugger->quit = true;
    print_console(emuInst, "Stopping emulator..\n");
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

    load_bootloader(0x0C00);
    load_firmware(emuInst, file, 0xC000);

    display_registers(emuInst);
    disassemble(emuInst, cpu->pc, 1);
    update_register_display(emuInst);

    while (!deb->quit) {
        // Handle debugger when CPU is not running
        if (!cpu->running) {
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