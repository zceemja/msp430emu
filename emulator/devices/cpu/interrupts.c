
#include "interrupts.h"

void service_interrupt(Emulator *emu, uint16_t cause) {
    Cpu *cpu = emu->cpu;
    if(!cpu->sr.GIE) return;
    if((cpu->interrupt == NULL_VECTOR) || (cause > cpu->interrupt)) {
        cpu->interrupt = cause;
    }
    return;
}

void handle_interrupts(Emulator *emu) {
    Cpu *cpu = emu->cpu;
    if(cpu->interrupt != NULL_VECTOR) {
        cpu->sp -= 2;
        uint16_t *stack_address = get_stack_ptr(emu);
        *stack_address = cpu->pc;

        cpu->sp -= 2;
        stack_address = get_stack_ptr(emu);
        *stack_address = sr_to_value(emu);
        // ISV memory space (0xFFE0) + cause
        cpu->pc = *get_addr_ptr(0xFFE0 + cpu->interrupt);
        cpu->sr.GIE = 0;
        cpu->sr.CPUOFF = 0;
        cpu->sr.OSCOFF = 0;
        cpu->sr.SCG1 = 0;
        cpu->interrupt = NULL_VECTOR;
    }
}