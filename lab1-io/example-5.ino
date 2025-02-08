#define F_CPU 16000000UL

#include "pin_macros.h"
#include <avr/io.h>
#include <util/delay.h>

const uint8_t segments[] = {
    0b00111111, // 0
    0b00000110, // 1
    0b01011011, // 2
    0b01001111, // 3
    0b01100110, // 4
    0b01101101, // 5
    0b01111101, // 6
    0b00000111, // 7
    0b01111111, // 8
    0b01101111  // 9
};

int main(void) {
  DDRD = 0xFF;

  PIN_UNSET(DDRC, PC0);
  PIN_SET(PORTC, PC0);

  PIN_UNSET(DDRC, PC1);
  PIN_SET(PORTC, PC1);

  uint8_t counter = 0;
  PORTD = segments[counter];

  while (1) {
    if (PIN_READ(PINC, PC0) == 0) {
      _delay_ms(50);

      if (PIN_READ(PINC, PC0) == 0) {
        counter++;
        if (counter > 9) {
          counter = 0;
        }
        PORTD = segments[counter];
      }
    }

    if (PIN_READ(PINC, PC1) == 0) {
      _delay_ms(50);

      if (PIN_READ(PINC, PC1) == 0) {
        counter++;
        if (counter > 9) {
          counter = 0;
        }
        PORTD = segments[counter];
      }
    }
  }

  return 0;
}
