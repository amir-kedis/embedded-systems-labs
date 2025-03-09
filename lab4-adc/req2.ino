#define ADC_START_CONVERSION() (ADCSRA |= (1 << ADSC))
#define ADC_CONVERSION_COMPLETE() (!(ADCSRA & (1 << ADSC)))
#define ADC_READ_VALUE() (ADC)

void ADC_Init(void) {
    ADMUX = (1 << REFS0);                /* AREF = AVcc */
    ADCSRA = (1 << ADEN) |               /* Enable ADC */
             (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0); /* Prescaler 128 */
}

void ADC_SelectChannel(uint8_t channel) {
    ADMUX = (ADMUX & 0xF8) | (channel & 0x07);
}

void ADC_WaitConversion(void) {
    while(!ADC_CONVERSION_COMPLETE());
}


uint16_t ADC_Read(uint8_t channel) {
    ADC_SelectChannel(channel);
    ADC_START_CONVERSION();
    ADC_WaitConversion();
    return ADC_READ_VALUE();
}

void ADC_InterruptEnable(void) {
    ADCSRA |= (1 << ADIE);
}

void ADC_InterruptDisable(void) {
    ADCSRA &= ~(1 << ADIE);
}

#define ADC_START_CONVERSION_IT() (ADCSRA |= (1 << ADSC))

volatile uint16_t adc_result = 0;
volatile bool adc_ready = false;

ISR(ADC_vect) {
    adc_result = ADC;
    adc_ready = true;
}

void example_interrupt(void) {
    ADC_Init();
    ADC_InterruptEnable();
    ADC_SelectChannel(0);

    Serial.begin(9600);

    ADC_START_CONVERSION_IT();

    while(1) {
        if(adc_ready) {
            Serial.println(adc_result);
            adc_ready = false;
            ADC_START_CONVERSION_IT();
            delay(500);
        }
    }
}
