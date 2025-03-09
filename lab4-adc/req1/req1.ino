#define ADC_START_CONVERSION() (ADCSRA |= (1 << ADSC))
#define ADC_CONVERSION_COMPLETE() ((ADCSRA & (1 << ADSC)))
#define ADC_READ_VALUE() (ADC)

void ADC_Init(void) {
    ADMUX = (1 << REFS0);                /* AREF = AVcc */
    ADCSRA = (1 << ADEN) |               /* Enable ADC */
             (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0); /* Prescaler 128 */
}

void ADC_SelectChannel(uint8_t channel) {
    ADMUX = (ADMUX & 0xF8) | (channel & 0x07);
}


uint16_t ADC_Read(uint8_t channel) {
    ADC_SelectChannel(channel);
    ADC_START_CONVERSION();
    //while(ADC_CONVERSION_COMPLETE());
    return ADC;
}


int main(void) {
    Serial.begin(9600);
    ADC_Init();
    

    while(true) {
        Serial.println("hi");
        // Read ADC value on channel 0 (PC0)
        uint16_t reading = ADC_Read(PC0);
        Serial.println(reading);
        delay(50);
    }
}

