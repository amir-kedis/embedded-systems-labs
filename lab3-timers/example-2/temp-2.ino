#define F_CPU 16000000UL

#ifndef MACROS_H
#define MACROS_H

#define PIN_SET(REG, PIN) REG |= (1 << PIN)
#define PIN_UNSET(REG, PIN) REG &= ~(1 << PIN)
#define PIN_TOGGLE(REG, PIN) REG ^= (1 << PIN)
#define PIN_READ(REG, PIN) ((REG & (1 << PIN)) >> PIN)

#endif

#define TARGET_OVERFLOW 244
#define TARGET_OFFSET 36

volatile uint8_t tot_overflow;

void INTI_TIMER2(void)
{
    PIN_SET(TCCR2B, CS22);
    PIN_SET(TIMSK2, TOIE2);
    TCNT2 = 0;
    sei();
    tot_overflow = 0;
}

ISR(TIMER2_OVF_vect)
{
    tot_overflow++;
}

const uint8_t segments[]  {
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
};=

#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>

int main(void)
{
    int count = 0;
    DDRC = 0x7F;

    PORTC = segments[count];

    while (true)
    {
        if (tot_overflow >= TARGET_OVERFLOW)
        {
            if (TCNT2 >= TARGET_OFFSET)
            {
                count = (count + 1) % 10;
                PORTC = segments[count];
                tot_overflow = 0;
                TCNT2 = 0;
            }
        }
    }
    return 0;
}
