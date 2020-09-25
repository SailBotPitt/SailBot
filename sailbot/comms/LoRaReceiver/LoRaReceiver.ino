#include <SPI.h>
#include <RH_RF95.h>
#include <pb_encode.h>
#include <pb_decode.h>

#include "messages.pb.h"
#include "transceiver.h"

//static Transceiver radio;
RH_RF95 _rf95(RFM95_CS, RFM95_INT);

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(1);
  }
  
  radio_init();
}

void loop() {
  size_t bytesReceived = 0;
  if((bytesReceived = tryReceive()) > 0){
    
    //Serial.println(bytesReceived);
    digitalWrite(LED_BUILTIN, HIGH);
    //Serial.write(&radio.inBuffer[0], bytesReceived);
    
    Serial.print((char*)inBuffer);
    digitalWrite(LED_BUILTIN, LOW);
  }

}
