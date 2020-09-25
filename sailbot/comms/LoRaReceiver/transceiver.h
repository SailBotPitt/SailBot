#ifndef TRANSCEIVER_H
#define TRANSCEIVER_H

#include <RH_RF95.h>

// for feather32u4 
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 7

// Change to 434.0 or other frequency, must match RX's freq!
#define RF95_FREQ 915.0

#define OUT_BUFFER_SIZE (RH_RF95_MAX_MESSAGE_LEN)
#define IN_BUFFER_SIZE  (RH_RF95_MAX_MESSAGE_LEN)


/*class Transceiver {
  public:
  Transceiver(): _rf95(RFM95_CS, RFM95_INT) {};
  ~Transceiver(){};*/

  extern uint8_t outBuffer[OUT_BUFFER_SIZE];
  extern uint8_t inBuffer[IN_BUFFER_SIZE];

  bool radio_init();

  bool transmit(size_t amount);

  size_t tryReceive();

  //private:
  extern RH_RF95 _rf95;
//};

#endif
