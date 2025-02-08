#define F_CPU 16000000UL

#include "pin_macros.h"
#include <avr/io.h>
#include <util/delay.h>

int main(void) {
  PIN_UNSET(DDRB, DDB0);
  PIN_SET(PORTB, PORTB0);

  PIN_SET(DDRC, DDC0);
  PIN_SET(PORTC, PORTC0);

  uint8_t prevState = 1;

  while (1) {
    uint8_t currentState = PIN_READ(PINB, PINB0);

    if (currentState != prevState) {
      _delay_ms(30);

      if (currentState == 0) {
        PIN_TOGGLE(PORTC, PORTC0);
      }

      prevState = currentState;
    }
  }
}
