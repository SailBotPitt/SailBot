// Feather9x_TX
// -*- mode: C++ -*-
// Example sketch showing how to create a simple messaging client (transmitter)
// with the RH_RF95 class. RH_RF95 class does not provide for addressing or
// reliability, so you should only use RH_RF95 if you do not need the higher
// level messaging abilities.
// It is designed to work with the other example Feather9x_RX
 
#include <SPI.h>
#include <RH_RF95.h>
#include <LiquidCrystal_I2C.h>

#define RUDDER_PIN 0
#define SAIL_PIN 1
 
// for feather32u4 
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 7

 
/* for feather m0  
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 3
*/
 
/* for shield 
#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 7
*/
 
/* Feather 32u4 w/wing
#define RFM95_RST     11   // "A"
#define RFM95_CS      10   // "B"
#define RFM95_INT     2    // "SDA" (only SDA/SCL/RX/TX have IRQ!)
*/
 
/* Feather m0 w/wing 
#define RFM95_RST     11   // "A"
#define RFM95_CS      10   // "B"
#define RFM95_INT     6    // "D"
*/
 
#if defined(ESP8266)
  /* for ESP w/featherwing */ 
  #define RFM95_CS  2    // "E"
  #define RFM95_RST 16   // "D"
  #define RFM95_INT 15   // "B"
 
#elif defined(ESP32)  
  /* ESP32 feather w/wing */
  #define RFM95_RST     27   // "A"
  #define RFM95_CS      33   // "B"
  #define RFM95_INT     12   //  next to A
 
#elif defined(NRF52)  
  /* nRF52832 feather w/wing */
  #define RFM95_RST     7   // "A"
  #define RFM95_CS      11   // "B"
  #define RFM95_INT     31   // "C"
  
#elif defined(TEENSYDUINO)
  /* Teensy 3.x w/wing */
  #define RFM95_RST     9   // "A"
  #define RFM95_CS      10   // "B"
  #define RFM95_INT     4    // "C"
#endif
 
// Change to 434.0 or other frequency, must match RX's freq!
#define RF95_FREQ 915.0
 
// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

LiquidCrystal_I2C lcd(0x27,16,2);
int rudder_val = 0;
int read_rudder_val = 999;
int sail_val = 0;
int read_sail_val = 999;
int loopsSinceSent = 0;
const int loopsBetweenSends = 10;
char buf[16];

byte PWM_PIN_1 = 6;
byte PWM_PIN_2 = 9;
 
int pwm_value1, pwm_value2;
 
void setup() 
{
  pinMode(RFM95_RST, OUTPUT);
  pinMode(PWM_PIN_1, INPUT);
  pinMode(PWM_PIN_2, INPUT);
  digitalWrite(RFM95_RST, HIGH);
 
  Serial.begin(115200);
  //while (!Serial) {
    //delay(1);
  //}
 
  delay(100);
 
  Serial.println("Feather LoRa TX Test!");
 
  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);
 
  while (!rf95.init()) {
    Serial.println("LoRa radio init failed");
    Serial.println("Uncomment '#define SERIAL_DEBUG' in RH_RF95.cpp for detailed debug info");
    while (1);
  }
  Serial.println("LoRa radio init OK!");
 
  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);
  
  // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on
 
  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then 
  // you can set transmitter powers from 5 to 23 dBm:
  rf95.setTxPower(23, false);

  
  lcd.init();
  lcd.backlight();

  sprintf(buf, "Rudder %d", rudder_val);
  lcd_message(buf, 0); 
  
}
 
int16_t packetnum = 0;  // packet counter, we increment per xmission
 
void loop()
{
  delay(5); // Wait 1 second between transmits, could also 'sleep' here!
  loopsSinceSent++;
  //Serial.println("Transmitting..."); // Send a message to rf95_server  
  
  
  if (loopsBetweenSends <= loopsSinceSent){
    int readRudderVal = map(pulseIn(PWM_PIN_1, HIGH), 990, 1965, 0, 90);
    int readSailVal = map(pulseIn(PWM_PIN_2, HIGH), 980, 1910, 0, 90);     
    if (abs(readRudderVal - rudder_val) > 1){
      rudder_val = readRudderVal;  
      update_lcd_rudder();
    }
    if (abs(readSailVal - sail_val) > 1){
      sail_val = readSailVal;
      update_lcd_sail();
      
    }
    loopsSinceSent = 0;
    char radiopacket[20] = "";
    radiopacket[0] = 'R';    
    if (rudder_val < 10){
      radiopacket[1] = 48; // ascii 0
    }
    else{
      radiopacket[1] = (rudder_val / 10) + 48;
    }
    radiopacket[2] = (rudder_val % 10) + 48;
    //Serial.print("Sending "); Serial.println(radiopacket);
    //rf95.send((uint8_t *)radiopacket, 20);
  }  
       
  
  char radiopacket[20] = "";
  bool msg = false;  
  int availableBytes = Serial.available();
  for(int i=0; i<availableBytes && i<20; i++)
  {
     radiopacket[i] = Serial.read();
     msg = true;
  }
  if (msg){
    if (radiopacket[0] == '?'){
      returnData();
    }
    else{
      Serial.print("Sending "); Serial.println(radiopacket);
      //radiopacket[19] = 0;
      
      //Serial.println("Sending...");
      delay(10);
      rf95.send((uint8_t *)radiopacket, 20);
    }
    
  }
  //itoa(packetnum++, radiopacket+13, 10);
  
  
  //Serial.println("Waiting for packet to complete..."); 
  delay(10);
  rf95.waitPacketSent();
  // Now wait for a reply
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  uint8_t len = sizeof(buf);
 
  /*Serial.println("Waiting for reply...");
  if (rf95.waitAvailableTimeout(1000))
  { 
    // Should be a reply message for us now  */
     
  if (rf95.recv(buf, &len))
   {
      //Serial.print("Got reply: ");
      //Serial.println((char*)buf);
      if (buf[0] == 'R'){  
        read_rudder_val = (buf[1] - 48)*10 + (buf[2] - 48);
        update_lcd_rudder();
      }
      else if (buf[0] == 'S'){  
        read_sail_val = (buf[1] - 48)*10 + (buf[2] - 48);
        update_lcd_sail();
      }
      //Serial.print("RSSI: ");
      //Serial.println(rf95.lastRssi(), DEC);    
    }
  else
    {
      //Serial.println("Receive failed");
    }
  /*}
  else
  {
    Serial.println("No reply, is there a listener around?");
  }*/
 
}

void update_lcd_rudder(){
  char buffer[16];
  int val = rudder_val;
  val = val - 45;
  sprintf(buffer, " Rudder %d (%d) ", val, read_rudder_val);
  lcd_message(buffer, 0);
}

void update_lcd_sail(){
  char buffer[16];
  int val = sail_val;
  val = val;
  sprintf(buffer, " Sail %d (%d) ", val, read_sail_val);
  lcd_message(buffer, 1);
}

void lcd_message(String message, int row){
  
  int start = 0;
  if (message.length() < 16){
    start = (16 - message.length())/2;
  }
  lcd.setCursor(start,row);
  
  for (int i = 0; i < message.length() && i <= 16; i++){
    lcd.print(message[i]);
  }
  //Serial.println("lcd message:" + message);
}

void reset_display(){
  lcd_message("                ", 0);
  lcd_message("                ", 1);
}

int map(int x, int min1, int max1, int min2, int max2){
  x = min(max(x, min1), max1);
  float fx = x;
  float fmin1 = min1;
  float fmin2 = min2;
  float fmax1 = max1;
  float fmax2 = max2;
  float val = fmin2 + (fmax2-fmin2)*((fx-fmin1)/(fmax1-fmin1));
  return int(val);
}
  
void returnData(){
  Serial.print("R "); Serial.print(rudder_val);
  Serial.print(" S "); Serial.println(sail_val);
  Serial.flush();
  
}