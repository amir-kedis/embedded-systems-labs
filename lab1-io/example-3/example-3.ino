#define F_CPU 16000000UL


#define PIN_SET(REG, PIN)       REG |= (1 << PIN)
#define PIN_UNSET(REG, PIN)     REG &= ~(1 << PIN)
#define PIN_TOGGLE(REG, PIN)    REG ^= (1 << PIN)
#define PIN_READ(REG, PIN)      ((REG & (1 << PIN)) >> PIN)


#include <avr/io.h>
#include <util/delay.h>

int main(void) {
  PIN_UNSET(DDRB, PB0);
  PIN_SET(PORTB, PB0);

  PIN_SET(DDRC, PC0);
  PIN_SET(PORTC, PC0);

  uint8_t prevState = 1;

  while (1) {
    uint8_t currentState = PIN_READ(PINB, PB0);

    if (currentState != prevState) {
      _delay_ms(30);

      if (currentState == 0) {
        PIN_TOGGLE(PORTC, PORTC0);
      }

      prevState = currentState;
    }
  }
}
