

#ifndef _INTERRUPTS_H_
#define _INTERRUPTS_H_

// From msp430g2553.h version 1.2
#define TRAPINT_VECTOR      (0x0000)  /* 0xFFE0 TRAPINT */
#define PORT1_VECTOR        (0x0004)  /* 0xFFE4 Port 1 */
#define PORT2_VECTOR        (0x0006)  /* 0xFFE6 Port 2 */
#define ADC10_VECTOR        (0x000A)  /* 0xFFEA ADC10 */
#define USCIAB0TX_VECTOR    (0x000C)  /* 0xFFEC USCI A0/B0 Transmit */
#define USCIAB0RX_VECTOR    (0x000E)  /* 0xFFEE USCI A0/B0 Receive */
#define TIMER0_A1_VECTOR    (0x0010)  /* 0xFFF0 Timer0_A CC1, TA0 */
#define TIMER0_A0_VECTOR    (0x0012)  /* 0xFFF2 Timer0_A CC0 */
#define WDT_VECTOR          (0x0014) /* 0xFFF4 Watchdog Timer */
#define COMPARATORA_VECTOR  (0x0016) /* 0xFFF6 Comparator A */
#define TIMER1_A1_VECTOR    (0x0018) /* 0xFFF8 Timer1_A CC1-4, TA1 */
#define TIMER1_A0_VECTOR    (0x001A) /* 0xFFFA Timer1_A CC0 */
#define NMI_VECTOR          (0x001C) /* 0xFFFC Non-maskable */
#define RESET_VECTOR        (0x001E) /* 0xFFFE Reset [Highest Priority] */

#define NULL_VECTOR         (0xFFFF) /* Used by emulator indicate no interrupt */

#include "../utilities.h"

void service_interrupt(Emulator *emu, uint16_t cause);
void handle_interrupts(Emulator *emu);

#endif