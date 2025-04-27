#define F_CPU 16000000UL

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

#define TARGET_OVERFLOW 61
#define TARGET_OFFSET 9

volatile uint8_t tot_overflow;

void INIT_ADC(void) {
  PIN_SET(ADMUX, REFS0);
  PIN_SET(ADCSRA, ADEN);
  PIN_SET(ADCSRA, ADPS2);
  PIN_SET(ADCSRA, ADPS1);
  PIN_SET(ADCSRA, ADPS0);
}

void INIT_TIMER(void) {
  PIN_SET(TCCR2B, CS22);
  PIN_SET(TCCR2B, CS21);
  PIN_SET(TCCR2B, CS20);
  TCNT2 = 0;
  PIN_SET(TIMSK2, TOIE0);
  sei();
  tot_overflow = 0;
}

uint16_t adc_read(uint8_t ch) {
  ch &= 0x07;
  ADMUX = (ADMUX & 0XF8) | ch;
  PIN_SET(ADCSRA, ADSC);

  while (ADCSRA & (1 << ADSC))
    ;

  return ADC;
}

ISR(TIMER2_OVF_vect) {
  tot_overflow += 1;
}

int main(void) {
  Serial.begin(9600);
  INIT_ADC();
  INIT_TIMER();
  uint16_t adc_result;

  while (1) {
    if (tot_overflow >= TARGET_OVERFLOW) {
      if (TCNT2 >= TARGET_OFFSET) {
        Serial.println("Reading= " + String(adc_read(0)));
        TCNT2 = 0;
        tot_overflow = 0;
      }
    }
  }

  return 0;
}