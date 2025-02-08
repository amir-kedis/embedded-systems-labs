#define F_CPU 16000000UL

#ifndef PIN_MACROS_H
#define PIN_MACROS_H

#define PIN_SET(REG, PIN)       REG |= (1 << PIN)
#define PIN_UNSET(REG, PIN)     REG &= ~(1 << PIN)
#define PIN_TOGGLE(REG, PIN)    REG ^= (1 << PIN)
#define PIN_READ(REG, PIN)      ((REG & (1 << PIN)) >> PIN)

#endif


#include <avr/io.h>
#include <util/delay.h>

int main(void) {
  PIN_SET(DDRD, DDD6);
  PIN_SET(PORTD, PORTD6);

  while (1) {
    PIN_SET(PORTD, PORTD6);
    _delay_ms(1000);
    PIN_UNSET(PORTD, PORTD6);
    _delay_ms(1000);
  }

  return 0;
}
