


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

#define TARGET_OVERFLOW_COUNT 30
#define TARGEST_OFFSET 128

#include <avr/io.h>

#include <util/delay.h>
#include <avr/interrupt.h>


int main(void) {
  unsigned int t;
  
  DDRB = 0xFF;
  PORTD = 0xFF;
  TCCR1A = 0;
  PIN_SET(TIFR1, ICF1);
  TCCR1B = 0x41;

  while (PIN_READ(TIFR1, ICF1));
  t = ICR1;
  PIN_SET(TIFR1, ICF1);
  while (PIN_READ(TIFR1, ICF1));

  t -= ICR1;

  Serial.println(t);

  while (1);
  return 0;
}



