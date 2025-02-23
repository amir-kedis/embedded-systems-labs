#ifndef MACROS_H
#define MACROS_H

#define PIN_SET(REG, PIN)       REG |= (1 << PIN)
#define PIN_UNSET(REG, PIN)     REG &= ~(1 << PIN)
#define PIN_TOGGLE(REG, PIN)    REG ^= (1 << PIN)
#define PIN_READ(REG, PIN)      ((REG & (1 << PIN)) >> PIN)

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

#define TARGET_OVERFLOW_COUNT 30
#define TARGEST_OFFSET 128

volatile uint8_t tot_overflow;

ISR(TIMER2_OVF_vect)
{
  tot_overflow++;
}

void timer2_init(){
  TCCR2B |= (1 << CS20) | (1 << CS22) | ( 1 << CS21);
  TCNT2 = 0;
  TIMSK2 |= (1 << TOIE2);
  sei();
  tot_overflow = 0;
}

int main(void){
  timer2_init();
  Serial.begin(9600);
  
  PIN_SET(DDRC, PC0);
  PIN_SET(PORTC, PC0);

  

  while(1) {
    if (tot_overflow >= TARGET_OVERFLOW_COUNT){
      if (TCNT2 >= TARGEST_OFFSET){
        PORTC ^= (1 << PC0);
        TCNT2 = 0;
        Serial.println("Interrupted");
        tot_overflow = 0;
      }
    }
  }
  return 0;
}



