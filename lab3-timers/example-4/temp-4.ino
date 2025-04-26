#ifndef MACROS_H
#define MACROS_H

#define PIN_SET(REG, PIN) REG |= (1 << PIN)
#define PIN_UNSET(REG, PIN) REG &= ~(1 << PIN)
#define PIN_TOGGLE(REG, PIN) REG ^= (1 << PIN)
#define PIN_READ(REG, PIN) ((REG & (1 << PIN)) >> PIN)

#endif

#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>

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

void INIT_TIMER2(void){
    TCCR2B |= (1<<CS20) | (1<<CS22) | (1<<CS)
}

int main(void)
{
    return 0;
}