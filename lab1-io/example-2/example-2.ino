#define F_CPU 16000000UL

#include <avr/io.h>
#include <util/delay.h>

#ifndef PIN_MACROS_H
#define PIN_MACROS_H

#define PIN_SET(REG, PIN)       REG |= (1 << PIN)
#define PIN_UNSET(REG, PIN)     REG &= ~(1 << PIN)
#define PIN_TOGGLE(REG, PIN)    REG ^= (1 << PIN)
#define PIN_READ(REG, PIN)      ((REG & (1 << PIN)) >> PIN)

#endif



int main(void) {
  PIN_UNSET(DDRB, PB0);
  PIN_UNSET(DDRB, PB1);

  PIN_SET(DDRC, PC0);
  PIN_SET(DDRC, PC1);

  PIN_UNSET(PORTB, PC0);
  PIN_UNSET(PORTB, PC1);

  while (1) {

    if (PIN_READ(PINB, PB0)) {
      PIN_SET(PORTC, PC0);
    } else {
      PIN_UNSET(PORTC, PC0);
    }

    if (PIN_READ(PINB, PB1)) {
      PIN_SET(PORTC, PC1);
    } else {
      PIN_UNSET(PORTC, PC1);
    }

  }

  return 0;
}
