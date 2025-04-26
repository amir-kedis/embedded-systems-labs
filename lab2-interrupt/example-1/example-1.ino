#define PIN_SET(REG, PIN) REG |= (1 << PIN)
#define PIN_UNSET(REG, PIN) REG &= ~(1 << PIN)
#define PIN_TOGGLE(REG, PIN) REG ^= (1 << PIN)
#define PIN_READ(REG, PIN) ((REG & (1 << PIN)) >> PIN)

#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>

void INIT_I0(void)
{
    PIN_UNSET(SREG, 7);
    PIN_UNSET(DDRD, PD2);
    PIN_SET(EIMSK, INT0);
    PIN_SET(EICRA, ISC00);
    PIN_SET(EICRA, ISC01);
    PIN_SET(SREG, 7);
}

ISR(INT0_vect)
{
    PIN_TOGGLE(PORTC, PC0);
    _delay_ms(50);
}

int main(void)
{
    INIT_I0();

    PIN_SET(DDRC, PC0);
    PIN_UNSET(PORTC, PC0);

    while (true)
        ;
    return 0;
}