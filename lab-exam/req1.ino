void adc_init()
{
  // AREF = AVcc
  ADMUX = (1<<REFS0);
  // ADC Enable and prescaler of 128
  // 16000000/128 = 125000  
  ADCSRA = (1<<ADEN)|(1<<ADPS2)|(1<<ADPS1)|(1<<ADPS0);
}

void timer2_init(){
  // set up timer with no prescaling
  TCCR2B |= (1 << CS20) | (1 << CS21) | (1 << CS22);

  // initialize counter
  TCNT2 = 0;
  // enable overflow INT
  TIMSK2 |= (1 << TOIE2);

  sei();
}

uint16_t adc_read(uint8_t ch)
{
  // select the corresponding channel 0~5
  // ANDing with ’7′ will always keep the value
  // of ‘ch’ between 0 and 5
  ch &= 0b00000111;// AND operation with 7
  ADMUX = (ADMUX & 0xF8)|ch; // clears the bottom 3 bits before ORing

  // start single conversion
  // write ’1′ to ADSC
  ADCSRA |= (1<<ADSC);

  // wait for conversion to complete
  // ADSC becomes ’0′ again
  // till then, run loop continuously
  while(ADCSRA & (1<<ADSC));

  return (ADC);
}

uint8_t read_adc_plz = 0;
uint8_t num_overflows = 0;
ISR(TIMER2_OVF_vect)
{
  //Serial.println("OVERFLOW");
  num_overflows += 1;
  if (num_overflows >= 61)
  {
    read_adc_plz = 1;
    num_overflows = 0;
  }
}

int main()
{
  Serial.begin(9600);
  
  
  uint16_t adc_result0;
  
  

  // initialize adc
  adc_init();

  // init timer
  timer2_init();

  while(1)
  {
    if (read_adc_plz == 1) {
      // TO BE PRECISE LOL (:
      if (TCNT2 < 9) continue;

      Serial.println("adc: ");
      adc_result0 = adc_read(0);// read adc value at PC0
      // condition for led to turn on or off
      Serial.println(adc_result0);
      read_adc_plz = 0;
    }

    //Serial.println("FLUSH");
    Serial.flush();
  }

  return 0;
}
