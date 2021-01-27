all: MSP430 SERVER

MSP430 : main.o utilities.o emu_server.o registers.o memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o formatII.o formatIII.o \
	usci.o port1.o packet_queue.o bcm.o timer_a.o

	g++ -o MSP430 main.o emu_server.o utilities.o registers.o memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o formatII.o formatIII.o usci.o port1.o bcm.o timer_a.o packet_queue.o -lreadline -lwebsockets -lpthread -lrt -lssl -lcrypto;

libmsp430.so: main.o utilities.o emu_server.o registers.o memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o formatII.o formatIII.o \
	usci.o port1.o packet_queue.o bcm.o timer_a.o
	g++ main.o emu_server.o utilities.o registers.o memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o formatII.o formatIII.o usci.o port1.o bcm.o timer_a.o packet_queue.o -lreadline -lwebsockets -lpthread -lrt -lssl -lcrypto -shared -o libmsp430.so;

main.o : main.cpp
	g++ -c -fPIC main.cpp

utilities.o : devices/utilities.c
	g++ -c -fPIC devices/utilities.c

registers.o : devices/cpu/registers.c
	g++ -c -fPIC devices/cpu/registers.c

memspace.o : devices/memory/memspace.c
	g++ -c -fPIC devices/memory/memspace.c

debugger.o : debugger/debugger.c
	g++ -c -fPIC debugger/debugger.c

disassembler.o : debugger/disassembler.c
	g++ -c -fPIC debugger/disassembler.c

register_display.o : debugger/register_display.c
	g++ -c -fPIC debugger/register_display.c

decoder.o : devices/cpu/decoder.c
	g++ -c -fPIC devices/cpu/decoder.c

flag_handler.o : devices/cpu/flag_handler.c
	g++ -c -fPIC devices/cpu/flag_handler.c

formatI.o : devices/cpu/formatI.c
	g++ -c -fPIC devices/cpu/formatI.c

formatII.o : devices/cpu/formatII.c
	g++ -c -fPIC devices/cpu/formatII.c

formatIII.o : devices/cpu/formatIII.c
	g++ -c -fPIC devices/cpu/formatIII.c

bcm.o : devices/peripherals/bcm.c
	g++ -c -fPIC devices/peripherals/bcm.c

timer_a.o : devices/peripherals/timer_a.c
	g++ -c -fPIC devices/peripherals/timer_a.c

usci.o : devices/peripherals/usci.c
	g++ -c -fPIC devices/peripherals/usci.c

port1.o : devices/peripherals/port1.c
	g++ -c -fPIC devices/peripherals/port1.c

emu_server.o : debugger/websockets/emu_server.cpp
	g++ -c -fPIC debugger/websockets/emu_server.cpp

packet_queue.o : debugger/websockets/packet_queue.c
	g++ -c -fPIC debugger/websockets/packet_queue.c

# Server Program

SERVER : server.o
	cc -o server server.o -lrt -lpthread -lwebsockets -lssl -lcrypto;

server.o : debugger/server/server.c
	cc -c debugger/server/server.c


clean :
	rm server.o main.o utilities.o emu_server.o registers.o \
	memspace.o debugger.o disassembler.o \
	register_display.o decoder.o flag_handler.o formatI.o \
	formatII.o formatIII.o \
	usci.o port1.o packet_queue.o bcm.o timer_a.o \
	*.bin *.tmp *.elf \
	MSP430 server;
