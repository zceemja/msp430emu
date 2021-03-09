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

#include "usci.h"

/*
int master;
FILE *slave;
int sp;
char c;

void *thrd (void *ctxt)
{
  Usci *usci = (Usci *)ctxt;
  char buf[64] = {0};

  while (true) {
    usleep(333);
    if ( read(sp, buf, 1) > 0 ) {
      while (*usci->IFG2 & RXIFG);

      if (*buf == '\n') {
	*buf = '\r';
      }
      if (*buf == '\\') {
	// Ah, escape sequence, what will I parse it as?
	read(sp, buf, 1);
	if (*buf == 'h') {
	  read(sp, buf, 2);
	  buf[2] = 0;
	  *usci->UCA0RXBUF = (uint8_t) strtoul(buf, NULL, 16);
	}
      }
      else {    
	*usci->UCA0RXBUF = *(uint8_t *) buf;
      }

      *usci->IFG2 |= RXIFG;
    }
  }  

  return NULL;
}

void open_pty (Emulator *emu) 
{
  Cpu *cpu = emu->cpu;

  char slavename[64], buf[64];
  struct termios termios_p;
  
  master = posix_openpt(O_RDWR);

  grantpt(master);
  unlockpt(master);
  ptsname_r(master, slavename, sizeof slavename);
  snprintf(buf, sizeof buf, "-S%s/%d", strrchr(slavename,'/')+1, master);
  
  // Child (pty)
  if( !fork() ) {   
    char * const args[] = {
      "xterm", buf, 
      NULL
    };

    setpgid(0, 0);
    execvp(args[0], args);
    exit(1);
  }
  // Parent                                                            

  sp = open(slavename, O_RDWR, O_NONBLOCK);  
  read(sp, buf, 100);

  tcgetattr(sp, &termios_p);
  termios_p.c_lflag |= ECHO;
  tcsetattr(sp, 0, &termios_p);
  
  pthread_t t;
  if( pthread_create(&t, NULL, thrd, (void *)cpu->usci ) ) {
    fprintf(stderr, "Error creating thread\n");
  }
}
*/

const uint32_t VALID_BAUD[] = {
    1200, 2400, 4800, 9600, 19200, 38400, 56000, 115200, 128000, 256000
};

void set_uart_buf(Emulator *emu, uint8_t *buf, int len) {
  Usci *usci = emu->cpu->usci;
  free(usci->UART_buf_data);
  usci->UART_buf_data = malloc(len);
  memcpy(usci->UART_buf_data, buf, len);
  usci->UART_buf_pnt = 0;
  usci->UART_buf_len = len;
}

void handle_usci (Emulator *emu) {
  Cpu *cpu = emu->cpu;
  Debugger *deb = emu->debugger;
  Usci *usci = cpu->usci;
  Port_1 *p1 = cpu->p1;

  if (!usci->USCI_RESET && (*usci->UCA0CTL1 & 0x01)) {
    usci->USCI_RESET = true;
  }
  else if (usci->USCI_RESET && !(*usci->UCA0CTL1 & 0x01)) {
    uint64_t clock = 0;
    usci->UART_baud = 0;
    usci->USCI_RESET = false;
    if((*usci->UCA0CTL1 & 0xc0) == 0x40) { // USCI clock source is ACLK
        clock = 32768;
    } else if ((*usci->UCA0CTL1 & 0x80) == 0x80) { // SMCLK
        clock = cpu->bcm->mclk_freq;
    }
    if(clock > 0) {
        double baud = clock / *usci->UCA0BR0;
        for(int i=0;i < sizeof(VALID_BAUD); i++) {
            double diff = ((double)VALID_BAUD[i])/baud;
            if(diff < 1.1 && diff > 0.9) {  // If error less than +/- 10%
                usci->UART_baud = VALID_BAUD[i];
                char message[35] = {0};
                sprintf(message, "Detected UART Baud Rate: %d\n", usci->UART_baud);
                print_console(emu, message);
                break;
            }
        }
    }
    if(usci->UART_baud == 0) {
        print_console(emu, "Invalid UART Baud Rate\n");
    }
  }
  if(usci->UART_baud > 0) {

    // Handle signal from RX pin (P1.1)
    if (p1->SEL_1 && p1->SEL2_1) {
      if((usci->UART_buf_pnt < usci->UART_buf_len) && !(*usci->IFG2 & RXIFG)) {
        uint64_t symbol_period = 1000000000/usci->UART_baud;
        if(cpu->nsecs >= (usci->UART_buf_sent + symbol_period)) {
          *usci->UCA0RXBUF = usci->UART_buf_data[usci->UART_buf_pnt];
          *usci->IFG2 |= RXIFG;
          usci->UART_buf_pnt++;
          usci->UART_buf_sent = cpu->nsecs; // Last time symbol was sent;
          if(*usci->IE2 & UCA0RXIE) {
            service_interrupt(emu, USCIAB0RX_VECTOR);
          }
        }
      }
    }
    // Handle sending from TX pin (P1.2)
    if (p1->SEL_2 && p1->SEL2_2) {
      // UCAxTXIFG
      if (*usci->IFG2 & TXIFG) {
        uint8_t c = *usci->UCA0TXBUF;
        unsigned char str[2];
        str[0] = c;
        str[1] = 0;

        *usci->IFG2 &= ~TXIFG;

        if (c & 0xFF) {
          if (deb->web_interface) {
              print_serial(emu, (char*)&str[0]);
          }
  	    *usci->UCA0TXBUF = 0;
        }
        *usci->IFG2 |= TXIFG;
      }
    }
  }
  return;
}

void setup_usci (Emulator *emu) 
{
  Cpu *cpu = emu->cpu;
  Usci *usci = cpu->usci;

  static const uint16_t UCA0CTL0_VLOC = 0x60; // Control Register 0
  static const uint16_t UCA0CTL1_VLOC = 0x61; // Control Register 1
  static const uint16_t UCA0BR0_VLOC  = 0x62; // Baud Rate ctl Register 0
  static const uint16_t UCA0BR1_VLOC  = 0x63; // Baud Rate ctl Register 1
  static const uint16_t UCA0MCTL_VLOC = 0x64; // Modulation ctl Register
  static const uint16_t UCA0STAT_VLOC = 0x65; // Status Register
  static const uint16_t UCA0RXBUF_VLOC = 0x66; // RECV buffer register
  static const uint16_t UCA0TXBUF_VLOC = 0x67; // Transmit buffer register
  static const uint16_t UCA0ABCTL_VLOC = 0x5D; // Auto-Baud control register
  static const uint16_t UCA0IRTCTL_VLOC = 0x5E; // IrDA transmit control reg
  static const uint16_t UCA0IRRCTL_VLOC = 0x5F; // IrDA Receive control reg
  static const uint16_t IE2_VLOC        = 0x01; // SFR interrupt enable register 2
  static const uint16_t IFG2_VLOC       = 0x03; // SFR interrupt flag register 2

  // Set initial values
  *(usci->UCA0CTL0   = (uint8_t *) get_addr_ptr(UCA0CTL0_VLOC))  = 0;
  *(usci->UCA0CTL1  = (uint8_t *) get_addr_ptr(UCA0CTL1_VLOC))   = 0x01;
  *(usci->UCA0BR0  = (uint8_t *) get_addr_ptr(UCA0BR0_VLOC))     = 0;
  *(usci->UCA0BR1  = (uint8_t *) get_addr_ptr(UCA0BR1_VLOC))     = 0;
  *(usci->UCA0MCTL  = (uint8_t *) get_addr_ptr(UCA0MCTL_VLOC))   = 0;
  *(usci->UCA0STAT  = (uint8_t *) get_addr_ptr(UCA0STAT_VLOC))   = 0;
  *(usci->UCA0RXBUF  = (uint8_t *) get_addr_ptr(UCA0RXBUF_VLOC)) = 0;
  *(usci->UCA0TXBUF  = (uint8_t *) get_addr_ptr(UCA0TXBUF_VLOC)) = 0;
  *(usci->UCA0ABCTL  = (uint8_t *) get_addr_ptr(UCA0ABCTL_VLOC))   = 0;
  *(usci->UCA0IRTCTL  = (uint8_t *) get_addr_ptr(UCA0IRTCTL_VLOC)) = 0;
  *(usci->UCA0IRRCTL  = (uint8_t *) get_addr_ptr(UCA0IRRCTL_VLOC)) = 0;  

  usci->IE2  = (uint8_t *) get_addr_ptr(IE2_VLOC);
  usci->IFG2  = (uint8_t *) get_addr_ptr(IFG2_VLOC);
  *usci->IFG2 |= TXIFG;
  *usci->IFG2 &= ~RXIFG;

  usci->UART_buf_data = NULL;
  usci->UART_buf_len = 0;
  usci->UART_buf_pnt = 0;
  usci->UART_buf_sent = 0;
  usci->UART_baud = 0;
  usci->USCI_RESET = false;
}
