
#ifndef DISPLAY_H
#define DISPLAY_H

#include <LiquidCrystal.h>

#define DISP_RS A0 //18
#define DISP_EN A1 //19
#define DISP_D4 A2 //20
#define DISP_D5 A3 //21
#define DISP_D6 A4 //22
#define DISP_D7 A5 //23
#define DISP_BL 3 //3

#define DISP_LENGTH 16
#define DISP_HEIGHT 2

#define DISP_BUFFER_SIZE  ((DISP_LENGTH*DISP_HEIGHT)+1)

enum DisplayState {
  SHOW_MESSAGE = 0,
  DISCONNECTED,
  VIEW_STATUS,
};

/*class Display {
  public:
  Display();
  ~Display() {};*/

  bool disp_init();

  void setBacklight(int level);
  void setState(DisplayState state);
  void refresh();
  void showMessage(String message);
    
  //private:
  extern LiquidCrystal _lcd;
  extern char _buffer[DISP_BUFFER_SIZE];
  extern DisplayState _state;
  extern bool _changed;

  void _showMessage();
  void _showDisconnected();
  void _showStatus();

  void _clearBuffer();
  
//};

#endif
