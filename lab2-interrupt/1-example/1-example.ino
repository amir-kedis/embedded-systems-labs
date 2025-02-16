#define PIN_SET(REG, PIN)       REG |= (1 << PIN)
#define PIN_UNSET(REG, PIN)     REG &= ~(1 << PIN)
#define PIN_TOGGLE(REG, PIN)    REG ^= (1 << PIN)
#define PIN_READ(REG, PIN)      ((REG & (1 << PIN)) >> PIN)


#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>

#define NUM_LEDS 3
#define NUM_BLINKS 5

uint8_t flashing_mode = 0;

void INIT_INT0(void)
{
  PIN_UNSET(SREG, 7);
  PIN_UNSET(DDRD, PD2);
  PIN_SET(EIMSK, INT0);
  PIN_SET(EICRA, ISC00);
  PIN_SET(EICRA, ISC01);
  PIN_SET(SREG, 7);
}

void INIT_INT1(void)
{
  PIN_UNSET(SREG, 7);
  PIN_UNSET(DDRD, PD3);
  PIN_SET(EIMSK, INT1);

  PIN_SET(EICRA, ISC10);
  PIN_SET(EICRA, ISC11);

  PIN_SET(SREG, 7);
}

ISR(INT0_vect)
{
  PIN_TOGGLE(PORTC, PC0);
  _delay_ms(50);
}

ISR(INT1_vect)
{
  flashing_mode = 1;
  _delay_ms(50);
}


void blink_led(uint8_t num_blinks)
{
  for (uint8_t i = 1; i < num_blinks+1; i++)
  {
    PIN_SET(PORTC, PC1);
    PIN_SET(PORTC, PC2);
    PIN_SET(PORTC, PC3);
    _delay_ms(500);
    PIN_UNSET(PORTC, PC1);
    PIN_UNSET(PORTC, PC2);
    PIN_UNSET(PORTC, PC3);
    _delay_ms(500);
  }
  flashing_mode = 0;
}

void roll_led()
{
  for (uint8_t j = 1; j <= NUM_LEDS ; j++)
  {
    PIN_SET(PORTC, j);
    _delay_ms(500);
    PIN_UNSET(PORTC, j);
  }
}

int main(void)
{
  INIT_INT0();
  INIT_INT1();

  // Set PC0 as output
  PIN_SET(DDRC, PC0);
  PIN_UNSET(PORTC, PC0);
  PIN_SET(DDRC, PC1);
  PIN_UNSET(PORTC, PC1);
  PIN_SET(DDRC, PC2);
  PIN_UNSET(PORTC, PC2);
  PIN_SET(DDRC, PC3);
  PIN_UNSET(PORTC, PC3);


  while (true)
  {
    if (flashing_mode)
      blink_led(NUM_BLINKS);
    else
      roll_led();
  }

  return 0;
}
