#define F_CPU 16000000UL

#include "pin_macros.h"
#include <avr/io.h>
#include <util/delay.h>

int main(void) {
  PIN_SET(DDRB, DDB0);
  PIN_SET(DDRB, DDB1);

  PIN_UNSET(PORTB, DDC0);
  PIN_UNSET(PORTB, DDC1);

  while (1) {
    if (PIN_READ(PINB, PINB0)) {
      PIN_SET(PORTC, PORTC0);
    } else {
      PIN_UNSET(PORTC, PORTC0);
    }

    if (PIN_READ(PINB, PINB1)) {
      PIN_SET(PORTC, PORTC1);
    } else {
      PIN_UNSET(PORTC, PORTC1);
    }
  }

  return 0;
}
