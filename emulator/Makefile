CC:=gcc
CXX:=g++
PYDIR:= $(word 1, $(wildcard /usr/include/python3*))
CCFLAGS:=-fPIC -DPYTHON -I$(PYDIR)
LLFLAGS:=-s

all: MSP430 SERVER _msp430emu.so

MSP430 : main.o utilities.o emu_server.o registers.o memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o formatII.o formatIII.o \
	usci.o port1.o packet_queue.o bcm.o timer_a.o interrupts.o
	g++ -o MSP430 launcher.o emu_server.o utilities.o registers.o memspace.o debugger.o disassembler.o interrupts.o \
	register_display.o decoder.o flag_handler.o formatI.o formatII.o formatIII.o usci.o port1.o bcm.o timer_a.o packet_queue.o \
	-lreadline -lwebsockets -lpthread -lrt -lssl -lcrypto;

_msp430emu.so: py_functions.o py_interface.o utilities.o registers.o memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o formatII.o formatIII.o \
	usci.o port1.o bcm.o timer_a.o interrupts.o
	$(CC) $(LLFLAGS) py_functions.o py_interface.o utilities.o registers.o memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o formatII.o formatIII.o usci.o port1.o bcm.o timer_a.o \
	interrupts.o -o _msp430emu.so -shared


main.o : main.c
	$(CC) $(CCFLAGS) -c main.c

py_functions.o : python/py_functions.c
	$(CC) $(CCFLAGS) -c python/py_functions.c

py_interface.o : python/py_interface.c
	$(CC) $(CCFLAGS) -c python/py_interface.c

utilities.o : devices/utilities.c
	$(CC) $(CCFLAGS) -c devices/utilities.c

registers.o : devices/cpu/registers.c
	$(CC) $(CCFLAGS) -c devices/cpu/registers.c

memspace.o : devices/memory/memspace.c
	$(CC) $(CCFLAGS) -c devices/memory/memspace.c

debugger.o : debugger/debugger.c
	$(CC) $(CCFLAGS) -c debugger/debugger.c

disassembler.o : debugger/disassembler.c
	$(CC) $(CCFLAGS) -c debugger/disassembler.c

register_display.o : debugger/register_display.c
	$(CC) $(CCFLAGS) -c debugger/register_display.c

decoder.o : devices/cpu/decoder.c
	$(CC) $(CCFLAGS) -c devices/cpu/decoder.c

flag_handler.o : devices/cpu/flag_handler.c
	$(CC) $(CCFLAGS) -c devices/cpu/flag_handler.c

formatI.o : devices/cpu/formatI.c
	$(CC) $(CCFLAGS) -c devices/cpu/formatI.c

formatII.o : devices/cpu/formatII.c
	$(CC) $(CCFLAGS) -c devices/cpu/formatII.c

formatIII.o : devices/cpu/formatIII.c
	$(CC) $(CCFLAGS) -c devices/cpu/formatIII.c

interrupts.o : devices/cpu/interrupts.c
	$(CC) $(CCFLAGS) -c devices/cpu/interrupts.c

bcm.o : devices/peripherals/bcm.c
	$(CC) $(CCFLAGS) -c devices/peripherals/bcm.c

timer_a.o : devices/peripherals/timer_a.c
	$(CC) $(CCFLAGS) -c devices/peripherals/timer_a.c

usci.o : devices/peripherals/usci.c
	$(CC) $(CCFLAGS) -c devices/peripherals/usci.c

port1.o : devices/peripherals/port1.c
	$(CC) $(CCFLAGS) -c devices/peripherals/port1.c

emu_server.o : debugger/websockets/emu_server.c
	$(CC) $(CCFLAGS) -c debugger/websockets/emu_server.c

packet_queue.o : debugger/websockets/packet_queue.c
	$(CC) $(CCFLAGS) -c debugger/websockets/packet_queue.c

# Server Program

SERVER : server.o
	cc -o server server.o -lrt -lpthread -lwebsockets -lssl -lcrypto;

server.o : debugger/server/server.c
	cc -c debugger/server/server.c


clean :
	rm py.o server.o main.o utilities.o emu_server.o registers.o \
	memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o \
	formatII.o formatIII.o py_functions.o py_interface.o \
	usci.o port1.o packet_queue.o bcm.o timer_a.o \
	*.bin *.tmp *.elf \
	MSP430 server _msp430emu.so;
