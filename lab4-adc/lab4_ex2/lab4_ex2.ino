void adc_init() {
  // AREF = AVcc
  ADMUX = (1 << REFS0);

  // ADC Enable and prescaler of 128
  // 16000000/128 = 125000
  // (1<<ADIE)=1 🡪 set ADC interrupt enable
  ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0)
           | (1 << ADIE);
  // Set global interrupt
  sei();
}


uint8_t ADC_endconversion_Flag = 0;
int16_t adc_read(uint8_t ch) {
  // select the corresponding channel 0~5
  // ANDing with ’7′ will always keep the value
  // of ‘ch’ between 0 and 5
  ch &= 0b00000111;             // AND operation with 7
  ADMUX = (ADMUX & 0xF8) | ch;  // clears the bottom 3 bits before ORing
  // start single conversion
  // write ’1′ to ADSC
  ADCSRA |= (1 << ADSC);

  // wait for conversion to complete
  // ADSC becomes ’0′ again
  // till then, run loop continuously
  if (ADC_endconversion_Flag == 1) {
    ADC_endconversion_Flag = 0;
    return (ADC);
  } else
    return (-1);
}

ISR(ADC_vect) {
  ADC_endconversion_Flag = 1;
}

int main() {
  int16_t adc_result0;
  DDRB = 0x20;  // to connect led to PB5
  Serial.begin(9600);
  // initialize adc
  adc_init();
  while (1) {
    adc_result0 = adc_read(0);  // read adc value at PA0

    // condition for led to turn on or off
    if (adc_result0 != -1) {
      Serial.println((adc_result0));
    }
  }
}
