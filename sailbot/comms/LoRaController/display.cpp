#include <Arduino.h>

#include "display.h"

  //LiquidCrystal _lcd(DISP_RS, DISP_EN, DISP_D4, DISP_D5, DISP_D6, DISP_D7);
  char _buffer[DISP_BUFFER_SIZE];
  DisplayState _state;
  bool _changed;

/*Display::Display() : _lcd(DISP_RS, DISP_EN, DISP_D4, DISP_D5, DISP_D6, DISP_D7){
  _state = DISCONNECTED;
  _clearBuffer();
}*/

bool disp_init(){

  //pinMode(DISP_BL, OUTPUT);
  _clearBuffer();
  _lcd.begin(DISP_LENGTH, DISP_HEIGHT);

  //digitalWrite(DISP_BL, LOW);
  _lcd.clear();
  _lcd.display();
  return false;
}

void setBacklight(int level){
  //TODO will be set to a pwm level eventually

  //digitalWrite(DISP_BL, level);
}

void setState(DisplayState state){
  if(_state != state){
  _state = state;
  _changed = true;
  }
}

void refresh(){
  if(!_changed)
    return;
  
  switch(_state){
    case DisplayState::SHOW_MESSAGE:
      _showMessage();
      break;
    case DisplayState::DISCONNECTED:
      _showDisconnected();
      break;
    case DisplayState::VIEW_STATUS:
      _showStatus();
      break;
  }
  //_lcd.clear();
  //_lcd.print(&_buffer[0]);
  _changed = false;
}

void showMessage(String message){
  _lcd.clear();
  _lcd.print(message);
}

void _showMessage(){
  
}

void _showDisconnected(){
  //_clearBuffer();
  //strcpy(&_buffer[0], "Disconnected");
  _lcd.clear();
  _lcd.print("Standby");
}

void _showStatus(){
  
}

void _clearBuffer(){
  memset(&_buffer[0], 0, DISP_BUFFER_SIZE);
}

/* eof */
