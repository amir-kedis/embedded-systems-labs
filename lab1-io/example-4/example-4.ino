#define F_CPU 16000000UL


#include <avr/io.h>
#include <util/delay.h>

#define PIN_SET(REG, PIN)       REG |= (1 << PIN)
#define PIN_UNSET(REG, PIN)     REG &= ~(1 << PIN)
#define PIN_TOGGLE(REG, PIN)    REG ^= (1 << PIN)
#define PIN_READ(REG, PIN)      ((REG & (1 << PIN)) >> PIN)

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
  PIN_UNSET(DDRC, PC4);
  PIN_SET(PORTC, PC4);

  uint8_t counter = 0;
  PORTD = segments[counter];

  while (1) {
    if (PIN_READ(PINC, PINC4) == 1) {
      _delay_ms(50);

      if (PIN_READ(PINC, PINC4) == 1) {
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
