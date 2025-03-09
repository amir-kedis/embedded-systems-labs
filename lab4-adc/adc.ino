// ADC Handling Functions and Macros for Arduino/AVR

// ======== ADC INITIALIZATION ========

// Initialize ADC with AVCC reference, enabled, and prescaler 128
void ADC_Init(void) {
    ADMUX = (1 << REFS0);                /* AREF = AVcc */
    ADCSRA = (1 << ADEN) |               /* Enable ADC */
             (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0); /* Prescaler 128 */
}

// ======== CHANNEL SELECTION ========

// Select ADC channel (0-7)
void ADC_SelectChannel(uint8_t channel) {
    ADMUX = (ADMUX & 0xF8) | (channel & 0x07);
}

// ======== ADC READING (POLLING METHOD) ========

// Start ADC conversion
#define ADC_START_CONVERSION() (ADCSRA |= (1 << ADSC))

// Check if ADC conversion is complete
#define ADC_CONVERSION_COMPLETE() (!(ADCSRA & (1 << ADSC)))

// Wait for ADC conversion to complete
void ADC_WaitConversion(void) {
    while(!ADC_CONVERSION_COMPLETE());
}

// Read ADC value (10-bit)
#define ADC_READ_VALUE() (ADC)

// Complete ADC read sequence for a given channel (blocking)
uint16_t ADC_Read(uint8_t channel) {
    ADC_SelectChannel(channel);
    ADC_START_CONVERSION();
    ADC_WaitConversion();
    return ADC_READ_VALUE();
}

// ======== ADC INTERRUPT FUNCTIONS ========

// Enable ADC conversion complete interrupt
void ADC_InterruptEnable(void) {
    ADCSRA |= (1 << ADIE);
}

// Disable ADC conversion complete interrupt
void ADC_InterruptDisable(void) {
    ADCSRA &= ~(1 << ADIE);
}

// Start ADC conversion with interrupt
#define ADC_START_CONVERSION_IT() (ADCSRA |= (1 << ADSC))

// ======== EXAMPLE IMPLEMENTATION ========

// Example 1: Polling Method
void example_polling(void) {
    // Initialize ADC
    ADC_Init();
    
    // Serial setup (assuming Arduino environment)
    Serial.begin(9600);
    
    while(1) {
        // Read ADC value on channel 0 (PC0)
        uint16_t reading = ADC_Read(0);
        
        // Print the result
        Serial.println(reading);
        
        // Delay for better readability
        delay(500);
    }
}

// Example 2: Interrupt Method
volatile uint16_t adc_result = 0;
volatile bool adc_ready = false;

// ADC Conversion Complete ISR
ISR(ADC_vect) {
    // Read the ADC result
    adc_result = ADC;
    adc_ready = true;
}

void example_interrupt(void) {
    // Initialize ADC
    ADC_Init();
    
    // Enable ADC interrupt
    ADC_InterruptEnable();
    
    // Select channel 0 (PC0)
    ADC_SelectChannel(0);
    
    // Serial setup
    Serial.begin(9600);
    
    // Start first conversion
    ADC_START_CONVERSION_IT();
    
    // Main loop
    while(1) {
        if(adc_ready) {
            // Print the result
            Serial.println(adc_result);
            
            // Reset flag
            adc_ready = false;
            
            // Start next conversion
            ADC_START_CONVERSION_IT();
            
            // Delay for better readability
            delay(500);
        }
    }
}
