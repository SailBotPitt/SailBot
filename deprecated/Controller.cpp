#include <PS2X_lib.h>   
PS2X ps2x; 

int LstickPosY = 127;
int LstickPosX = 127;
int RstickPosY = 127;
int RstickPosX = 127;

int error = 0; 
int mapX = 0;
byte type = 0;
byte vibrate = 0;

void setup(){

error = ps2x.config_gamepad(13,11,10,12, true, true);   //GamePad(clock, command, attention, data, Pressures?, Rumble?) 
if(error == 0){
 Serial.println("Found Controller, configured successful");
 Serial.println("Try out all the buttons, X will vibrate the controller, faster as you press harder;");
 Serial.println("holding L1 or R1 will print out the analog stick values.");
 Serial.println("Go to www.billporter.info for updates and to report bugs.");
}
 else if(error == 1)
  Serial.println("No controller found, check wiring, see readme.txt to enable debug. visit www.billporter.info for troubleshooting tips");
 else if(error == 2)
  Serial.println("Controller found but not accepting commands. see readme.txt to enable debug. Visit www.billporter.info for troubleshooting tips");
 else if(error == 3)
  Serial.println("Controller refusing to enter Pressures mode, may not support it. ");
  type = ps2x.readType(); 
    switch(type) {
      case 0:
       Serial.println("Unknown Controller type");
      break;
      case 1:
       Serial.println("DualShock Controller Found");
      break;
      case 2:
        Serial.println("GuitarHero Controller Found");
      break;
    }
}

bool LStickVal_V(int &val){ 
  if (abs(ps2x.Analog(PSS_LY) - LStickPosY) > 5){
    LStickPosY = ps2x.Analog(PSS_LY);
    val = map(LStickPosY, 0, 255, 0, 90);
    return true;
  }
  return false;
}

bool LStickVal_H(int &val){ 
  if (abs(ps2x.Analog(PSS_LX) - LStickPosX) > 5){
    LStickPosX = ps2x.Analog(PSS_LX);
    val = map(LStickPosX, 0, 255, 0, 90);
    return true;
  }
  return false;
}

bool RStickVal_V(int &val){ 
  if (abs(ps2x.Analog(PSS_RY) - RStickPosY) > 5){
    RStickPosY = ps2x.Analog(PSS_RY);

    if (RStickPosY < 50)
      val -= 1;

    else if(RStickPosY > 205)
      val += 1;
    
    return true;
  }
  return false;
}

bool RStickVal_H(int &val){ 
  if (abs(ps2x.Analog(PSS_RX) - RStickPosX) > 5){
    LStickPosX = ps2x.Analog(PSS_RX);
    
    if (RStickPosY < 50)
      val -= 1;

    else if(RStickPosY > 205)
      val += 1;
      
    return true;
  }
  return false;
}
