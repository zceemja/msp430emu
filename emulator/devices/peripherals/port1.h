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

#ifndef _PORT_1_
#define _PORT_1_

#include "../cpu/registers.h"
#include "../utilities.h"

struct Port_1 {
  // Peripheral register pointers
  
  // Port 1        = r/w =   = reset? =
  uint8_t *_IN;   /* r          -      */
  uint8_t *_OUT;  /* r/w     unchanged */
  uint8_t *_DIR;  /* r/w     PUC reset */
  uint8_t *_IFG;  /* r/w     PUC reset */
  uint8_t *_IES;  /* r/w     unchanged */
  uint8_t *_IE;   /* r/w     PUC reset */
  uint8_t *_SEL;  /* r/w     PUC reset */
  uint8_t *_SEL2; /* r/w     PUC reset */
  uint8_t *_REN;  /* r/w     PUC reset */

  // Peripherals activation flags (for emulator)
  bool DIR_0, OUT_0, IFG_0, IE_0, SEL_0, SEL2_0, REN_0;
  bool DIR_1, OUT_1, IFG_1, IE_1, SEL_1, SEL2_1, REN_1;
  bool DIR_2, OUT_2, IFG_2, IE_2, SEL_2, SEL2_2, REN_2;
  bool DIR_3, OUT_3, IFG_3, IE_3, SEL_3, SEL2_3, REN_3;
  bool DIR_4, OUT_4, IFG_4, IE_4, SEL_4, SEL2_4, REN_4;
  bool DIR_5, OUT_5, IFG_5, IE_5, SEL_5, SEL2_5, REN_5;
  bool DIR_6, OUT_6, IFG_6, IE_6, SEL_6, SEL2_6, REN_6;
  bool DIR_7, OUT_7, IFG_7, IE_7, SEL_7, SEL2_7, REN_7;

  // Pin flags
  uint8_t PIN0F, PIN1F, PIN2F, PIN3F, PIN4F, PIN5F, PIN6F, PIN7F;

};

void setup_port_1(Emulator *emu);
void handle_port_1(Emulator *emu);

#endif
