#include <SPI.h>
#include <pb_encode.h>
#include <pb_decode.h>
#include <LiquidCrystal.h>
#include <PS2X_lib.h>

#include "messages.pb.h"
#include "display.h"
#include "transceiver.h"

LiquidCrystal _lcd(DISP_RS, DISP_EN, DISP_D4, DISP_D5, DISP_D6, DISP_D7);
RH_RF95 _rf95(RFM95_CS, RFM95_INT);

enum Commands {
  SAIL_POSITION,
  RUDDER_POSITION,
  BOTH_POSITION,
  AUTONOMY_MODE,
};

// Singleton instance of the radio driver
//static RH_RF95 rf95(RFM95_CS, RFM95_INT);
//static Transceiver radio;

//static Display disp;

BaseToBoat messageOut = BaseToBoat_init_zero;
SkipperCommand skipper = SkipperCommand_init_zero;
SailCommand sail = SailCommand_init_zero;
RudderCommand rudder = RudderCommand_init_zero;
Mode autonomyMode = Mode_init_zero;


pb_ostream_t stream;

void setup() {
  disp_init();
  radio_init();
  
  Serial.begin(115200);
  while (!Serial) {
    delay(1);
  }

  
  showMessage("Initializing...");
  stream = pb_ostream_from_buffer(outBuffer, OUT_BUFFER_SIZE);

  delay(1000);
}

bool transmitBuffer(){
  //rf95.send(outBuffer, stream.bytes_written);
  //Serial.println(stream.bytes_written);
  return transmit(stream.bytes_written);
}

/* Sets sail position in degrees. Transmits immediately */
void sailPos(int value){
  sail.position = value;
  messageOut.command.sail = sail;
  messageOut.which_command = BaseToBoat_sail_tag;

  //memset(outBuffer, 0, sizeof(outBuffer));
  pb_encode(&stream, BaseToBoat_fields, &messageOut);
  transmitBuffer();
}

/* Set rudder position in degrees. Transmits immediately */
void rudderPos(int value){
  rudder.position = value;
  messageOut.command.rudder = rudder;
  messageOut.which_command = BaseToBoat_rudder_tag;
  
  //memset(&stream, 0, sizeof(outBuffer));
  pb_encode(&stream, BaseToBoat_fields, &messageOut);
  transmitBuffer();
}

/* Set sail and rudder positions in degrees. Transmits immediately */
void sailRudderPos(int sail, int rudder) {
  skipper.sailPosition = sail;
  skipper.rudderPosition = rudder;

  messageOut.command.skipper = skipper;
  messageOut.which_command = BaseToBoat_skipper_tag;

  //memset(&stream, 0, sizeof(outBuffer));
  pb_encode(&stream, BaseToBoat_fields, &messageOut);
  transmitBuffer();
}

int led_state = 0;

void loop() {
  setState(DisplayState::DISCONNECTED);
  refresh();

  size_t bytesReceived = 0;
  memset(outBuffer, 0, OUT_BUFFER_SIZE);
  while(Serial.available()){
    digitalWrite(LED_BUILTIN, led_state);
    //size_t num = Serial.readBytes(&radio.outBuffer[bytesReceived], (OUT_BUFFER_SIZE - bytesReceived));
    outBuffer[bytesReceived] = Serial.read();
    //bytesReceived += num;
    bytesReceived++;
    if(bytesReceived >= OUT_BUFFER_SIZE){
      transmit(bytesReceived);
      bytesReceived = 0;
    }
    led_state = (led_state+1)%2;
  }
  if(bytesReceived > 0)
    transmit(bytesReceived);

  if((bytesReceived = tryReceive()) > 0){
    
    //Serial.println(bytesReceived);
    digitalWrite(LED_BUILTIN, HIGH);
    //Serial.write(&radio.inBuffer[0], bytesReceived);
    
    Serial.print((char*)inBuffer);
    digitalWrite(LED_BUILTIN, LOW);
  }

 

}
