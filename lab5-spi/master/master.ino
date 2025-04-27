#include <avr/interrupt.h>
#include <Arduino.h>
#include <util/delay.h>

// SPI PINS
#define MISO PB4
#define MOSI PB3
#define SCK  PB5
#define SS   PB2

void init_spi_master(void) {
  DDRB  |= (1 << MOSI) | (1 << SCK) | (1 << SS);
  DDRB  &= ~(1 << MISO);
  PORTB |= (1 << SS);
  SPCR   = (1 << SPE) | (1 << MSTR) | (1 << SPR0);
}


void spi_write(uint8_t data) {
  SPDR = data;
  while (!(SPSR & (1 << SPIF)));
}


uint8_t spi_read(void) {
  SPDR = 0xFF;
  while (!(SPSR & (1 << SPIF)));
  return SPDR;
}


int main(void) {
  Serial.begin(9600);

  init_spi_master();

  PORTB &= ~(1 << SS);

  _delay_ms(500);

  uint8_t data = 1;
  while (1) {
    spi_write(data);
    data++;
    _delay_ms(10);

    uint8_t received_data = spi_read();
    Serial.print("Received: ");
    Serial.println(received_data, DEC);
  }
}

