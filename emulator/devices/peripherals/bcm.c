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

#include "bcm.h"


void handle_bcm (Emulator *emu) 
{
  Cpu *cpu = emu->cpu;
  Bcm *bcm = cpu->bcm;

  uint8_t DCOCTL  = *bcm->DCOCTL;
  uint8_t BCSCTL1 = *bcm->BCSCTL1;
  uint8_t BCSCTL2 = *bcm->BCSCTL2;
  uint8_t BCSCTL3 = *bcm->BCSCTL3;

  // HANDLE MCLK -------------------
  uint8_t SELMx = BCSCTL2 >> 6;
  uint8_t DIVMx = (BCSCTL2 >> 4) & 0x03;

  if (SELMx == 0b00 || SELMx == 0b01) { // source = DCOCLK
    bcm->mclk_freq = (bcm->dco_freq*1.0) / (1 << DIVMx);
    bcm->mclk_period = (1.0/(bcm->mclk_freq))*1000000000.0;
    bcm->cpu_period = bcm->mclk_period * CLK_PER_INSTR;
  }
  else if (SELMx == 0b10) { // XT2CLK
    bcm->mclk_freq = 0;
    bcm->mclk_period = 0;
  }
  else if (SELMx == 0b11) { // LFXT1CLK
    bcm->mclk_freq = (bcm->lfxt1_freq*1.0) / (1 << DIVMx);
    bcm->mclk_period = (1.0/(bcm->mclk_freq))*1000000000.0;
    bcm->cpu_period = bcm->mclk_period * CLK_PER_INSTR;
  }

  // HANDLE SMCLK -------------------
  uint8_t SELS  = (BCSCTL2 >> 3) & 0x01;
  uint8_t DIVSx = (BCSCTL2 >> 1) & 0x03;
  if (SELS == 0) { // DCOCLK
    bcm->smclk_freq = (bcm->dco_freq*1.0) / (1 << DIVSx);
    bcm->smclk_period = (1.0/(bcm->smclk_freq))*1000000000.0;
  }
  else if (SELS == 1) { // XT2CLK or LFXT1CLK
    bcm->smclk_freq = (bcm->lfxt1_freq*1.0) / (1 << DIVSx);
    bcm->smclk_period = (1.0/(bcm->smclk_freq))*1000000000.0;
  }

  // HANDLE ACLK -------------------
  uint8_t DIVAx = (BCSCTL1 >> 4) & 0x03;
  bcm->aclk_freq = bcm->lfxt1_freq / (1 << DIVAx);
  bcm->aclk_period = (1.0/(bcm->aclk_freq))*1000000000.0;

  // HANDLE LOW POWER MODES --------

  // Active Mode (CPU is active, all enabled clocks are active)
  if (!cpu->sr.SCG1 && !cpu->sr.SCG0 && !cpu->sr.OSCOFF && !cpu->sr.CPUOFF) {

  }

  // LPM0 (CPU, MCLK are disabled, SMCLK, ACLK are active)
  else if (!cpu->sr.SCG1 && !cpu->sr.SCG0 && !cpu->sr.OSCOFF && cpu->sr.CPUOFF){

  }

  /* LPM1 (CPU, MCLK are disabled. DCO and DC generator are
     disabled if the DCO is not used for SMCLK. ACLK is
     active.)
  */
  else if (!cpu->sr.SCG1 && cpu->sr.SCG0 && !cpu->sr.OSCOFF && cpu->sr.CPUOFF){

  }

  /* LPM2 (CPU, MCLK, SMCLK, DCO are disabled. DC generator remains enabled. 
     ACLK is active.) */
  else if (cpu->sr.SCG1 && !cpu->sr.SCG0 && !cpu->sr.OSCOFF && cpu->sr.CPUOFF){

  }

  // LPM3 (CPU, MCLK, SMCLK, DCO are disabled. DC generatordisabled.ACLK active.
  else if (cpu->sr.SCG1 && cpu->sr.SCG0 && !cpu->sr.OSCOFF && cpu->sr.CPUOFF){

  }

  // LPM4 (CPU and all clocks are disabled)
  else if (cpu->sr.SCG1 && cpu->sr.SCG0 && cpu->sr.OSCOFF && cpu->sr.CPUOFF){
    
  }

  // HANDLE DCO --------------------

  uint8_t DCOx   = DCOCTL >> 5;
  uint8_t MODx   = DCOCTL & 0x1F;
  uint8_t RSELx  = BCSCTL1 & 0x0F;  

  // Default state of BCM after reset ~1.03 MHz
  if (DCOx == 0b011 && RSELx == 0b0111) {
    bcm->dco_freq = 1030000;
    bcm->dco_period = 971;    
    bcm->dco_pulse_width = 485;
  }
  // 16 Mhz
  else if (DCOx == 0b100 && RSELx == 0b1111) {
    bcm->dco_freq = 16000000;
    bcm->dco_period = 63;
    bcm->dco_pulse_width = 31;    
  }
  // 12 MHz
  else if (DCOx == 0b100 && RSELx == 0b1110) {
    bcm->dco_freq = 12000000;
    bcm->dco_period = 83;
    bcm->dco_pulse_width = 42;            
  }
  // 8 Mhz
  else if (DCOx == 0b100 && RSELx == 0b1101) {
    bcm->dco_freq = 8000000;
    bcm->dco_period = 125;
    bcm->dco_pulse_width = 62;        
  }
  // 1 MHz
  else if (DCOx == 0b110 && RSELx == 0b0110) {
    bcm->dco_freq = 1000000;
    bcm->dco_period = 1000;
    bcm->dco_pulse_width = 500;        
  }

  // HANDLE LFXT1CLK -------------------
  uint8_t XTS = (BCSCTL1 >> 6) & 0x01; // LFXT1CLK select (high/low)
  
}

void setup_bcm (Emulator *emu) 
{
  Cpu *cpu = emu->cpu;
  Bcm *bcm = cpu->bcm;

  static const uint16_t DCOCTL_VLOC = 0x56;
  static const uint16_t BCSCTL1_VLOC = 0x57;
  static const uint16_t BCSCTL2_VLOC = 0x58;
  static const uint16_t BCSCTL3_VLOC = 0x53;
  static const uint16_t IE1_VLOC = 0x0;
  static const uint16_t IFG1_VLOC = 0x2;

  *(bcm->DCOCTL   = (uint8_t *) get_addr_ptr(DCOCTL_VLOC)) = 0x60;
  *(bcm->BCSCTL1   = (uint8_t *) get_addr_ptr(BCSCTL1_VLOC)) = 0x87;
  *(bcm->BCSCTL2   = (uint8_t *) get_addr_ptr(BCSCTL2_VLOC)) = 0;
  *(bcm->BCSCTL3   = (uint8_t *) get_addr_ptr(BCSCTL3_VLOC)) = 0x5;
  *(bcm->IE1   = (uint8_t *) get_addr_ptr(IE1_VLOC)) = 0;
  *(bcm->IFG1   = (uint8_t *) get_addr_ptr(IFG1_VLOC)) = 0;

  // 1.03 MHz
  bcm->dco_freq = 1030000;
  bcm->dco_period = 971;
  bcm->dco_pulse_width = 970 / 2;

  bcm->lfxt1_freq = 2000; // measured internal frequency
}


//uint64_t nanosec_diff(struct timespec *timeA_p, struct timespec *timeB_p)
//{
//    return ((timeA_p->tv_sec * 1000000000) + timeA_p->tv_nsec) - ((timeB_p->tv_sec * 1000000000) + timeB_p->tv_nsec);
//}

double mclk_clock_nstime(Emulator *emu) {
    Cpu *cpu = emu->cpu;
    Bcm *bcm = cpu->bcm;
    double nsec;

    nsec = (1.0/(bcm->mclk_freq))*1000000000.0;
    return nsec;
}

void mclk_wait_cycles (Emulator *emu, uint64_t cycles)
{
//    Cpu *cpu = emu->cpu;
//    Bcm *bcm = cpu->bcm;
//
//    uint64_t start = getnano();
//
////    uint64_t start, end;
////    uint64_t i, elapsed_nsecs;
//    double thing = 1000;
//
//    if (bcm->mclk_source == DCOCLK) {
//        thing = (1.0/(bcm->dco_freq/bcm->mclk_div))*1000000000.0;
//    }
//    thing *= cycles;
//
//    if (last_nano > 0) {
//        thing -= (double)(start - last_nano);
//    }
//    if (thing > 0) {
////        struct timespec tv;
////        tv.tv_sec = 0;
////        tv.tv_nsec = (long)thing;
////        nanosleep(&tv, &tv);
//        usleep((long)(thing / 1000.0));
//    }
//
//    last_nano = start;
//    return;
/*

    for (i = 0;i < cycles;i++)
    {
        start = getnano();
//        clock_gettime(CLOCK_MONOTONIC, &start);

        while (true)
        {
//            clock_gettime(CLOCK_MONOTONIC, &end);
            end = getnano();
            elapsed_nsecs = end - start;//nanosec_diff(&end, &start);

            // Choose timing based on clock source
            if (bcm->mclk_source == DCOCLK)
            {
                double thing = (1.0/(bcm->dco_freq/bcm->mclk_div))*1000000000.0;

                if (elapsed_nsecs >= (uint64_t)thing)
                    break;
            }
            else
            {
                puts("Error, clock source");
            }
        }
    }
*/
}

void smclk_wait_cycles (Emulator *emu, uint64_t cycles)
{
//  Cpu *cpu = emu->cpu;
//  Bcm *bcm = cpu->bcm;
//
//  uint64_t start, end;
//  uint64_t i, elapsed_nsecs;
//
//  for (i = 0;i < cycles;i++) {
//    start = getnano();
//    //    clock_gettime(CLOCK_MONOTONIC, &start);
//
//    while (true) {
//      end = getnano();
////      clock_gettime(CLOCK_MONOTONIC, &end);
//      elapsed_nsecs = end - start;//nanosec_diff(&end, &start);
//
//      // Choose timing based on clock source
//      if (bcm->mclk_source == DCOCLK) {
//	//printf("div: %llu\n",
//	//(long long unsigned)(1/(bcm->dco_freq/bcm->mclk_div)));
//
//	double thing = (1.0/(bcm->dco_freq/bcm->mclk_div))*1000000000.0;
//
//	if (elapsed_nsecs >= (uint64_t)thing) {
//	  break;
//	}
//      }
//      else {
//	puts("Error, clock source");
//      }
//
//    }
//  }
  
}
/*
  /*
  // Start Sources DCO, etc
  pthread_t pp;

  if ( pthread_create(&pp, NULL, DCO_source, (void *)emu ) ) {
    printf("Error creating DCO  thread\n");
    exit(1);
  }

void *DCO_source (void *data) 
{
  Emulator *emu = (Emulator *)data;
  Bcm *bcm = emu->cpu->bcm;
  
  printf("In source thread...\n");

  struct timespec start, end;
  uint64_t elapsed_nsecs;
  uint64_t trimmer = 0;

  while (true) {
    clock_gettime(CLOCK_MONOTONIC, &start);    

    while (true) {
      clock_gettime(CLOCK_MONOTONIC, &end);
      elapsed_nsecs = nanosec_diff(&end, &start);      
      if (elapsed_nsecs >= bcm->dco_period) break;
    }
  }

  /*
  while (true) {
    clock_gettime(CLOCK_MONOTONIC, &start);    
    bcm->dco_high = true;

    while (true) {
      clock_gettime(CLOCK_MONOTONIC, &end);
      elapsed_nsecs = nanosec_diff(&end, &start);
      
      if (elapsed_nsecs >= bcm->dco_pulse_width) {
	bcm->dco_high = false;
      }

      if (elapsed_nsecs >= bcm->dco_period) break;
    }
  }

  return NULL;
}
*/
