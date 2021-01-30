all: MSP430 SERVER

MSP430 : main.o utilities.o emu_server.o registers.o memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o formatII.o formatIII.o \
	usci.o port1.o packet_queue.o bcm.o timer_a.o
	g++ -o MSP430 main.o emu_server.o utilities.o registers.o memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o formatII.o formatIII.o usci.o port1.o bcm.o timer_a.o packet_queue.o -lreadline -lwebsockets -lpthread -lrt -lssl -lcrypto;

_msp430emu.so: main.o utilities.o emu_server.o registers.o memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o formatII.o formatIII.o \
	usci.o port1.o packet_queue.o bcm.o timer_a.o
	gcc $(LLFLAGS) main.o emu_server.o utilities.o registers.o memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o formatII.o formatIII.o usci.o port1.o bcm.o timer_a.o packet_queue.o \
	-lwebsockets -lreadline -lrt -lssl -lcrypto -lpthread -o _msp430emu.so -shared

main.o : main.c
	gcc $(CCFLAGS) -c main.c

utilities.o : devices/utilities.c
	gcc $(CCFLAGS) -c devices/utilities.c

registers.o : devices/cpu/registers.c
	gcc $(CCFLAGS) -c devices/cpu/registers.c

memspace.o : devices/memory/memspace.c
	gcc $(CCFLAGS) -c devices/memory/memspace.c

debugger.o : debugger/debugger.c
	gcc $(CCFLAGS) -c debugger/debugger.c

disassembler.o : debugger/disassembler.c
	gcc $(CCFLAGS) -c debugger/disassembler.c

register_display.o : debugger/register_display.c
	gcc $(CCFLAGS) -c debugger/register_display.c

decoder.o : devices/cpu/decoder.c
	gcc $(CCFLAGS) -c devices/cpu/decoder.c

flag_handler.o : devices/cpu/flag_handler.c
	gcc $(CCFLAGS) -c devices/cpu/flag_handler.c

formatI.o : devices/cpu/formatI.c
	gcc $(CCFLAGS) -c devices/cpu/formatI.c

formatII.o : devices/cpu/formatII.c
	gcc $(CCFLAGS) -c devices/cpu/formatII.c

formatIII.o : devices/cpu/formatIII.c
	gcc $(CCFLAGS) -c devices/cpu/formatIII.c

bcm.o : devices/peripherals/bcm.c
	gcc $(CCFLAGS) -c devices/peripherals/bcm.c

timer_a.o : devices/peripherals/timer_a.c
	gcc $(CCFLAGS) -c devices/peripherals/timer_a.c

usci.o : devices/peripherals/usci.c
	gcc $(CCFLAGS) -c devices/peripherals/usci.c

port1.o : devices/peripherals/port1.c
	gcc $(CCFLAGS) -c devices/peripherals/port1.c

emu_server.o : debugger/websockets/emu_server.c
	gcc $(CCFLAGS) -c debugger/websockets/emu_server.c

packet_queue.o : debugger/websockets/packet_queue.c
	gcc $(CCFLAGS) -c debugger/websockets/packet_queue.c

# Server Program

SERVER : server.o
	cc -o server server.o -lrt -lpthread -lwebsockets -lssl -lcrypto;

server.o : debugger/server/server.c
	cc -c debugger/server/server.c


clean :
	rm py.o server.o main.o utilities.o emu_server.o registers.o \
	memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o \
	formatII.o formatIII.o \
	usci.o port1.o packet_queue.o bcm.o timer_a.o \
	*.bin *.tmp *.elf \
	MSP430 server;
