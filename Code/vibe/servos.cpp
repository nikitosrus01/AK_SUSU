#include "config.h"
#include "servos.h"

#ifdef ESP32
    #include <ESP32Servo.h>
#else
    #include <Servo.h>
#endif

Servo drogueServo;
Servo mainServo;
Servo legsServo;

void initServos()
{
    drogueServo.attach(DROGUE_SERVO_PIN);
    mainServo.attach(MAIN_SERVO_PIN);
    legsServo.attach(LEGS_SERVO_PIN);

    drogueServo.write(SERVO_LOCKED);
    mainServo.write(SERVO_LOCKED);
    legsServo.write(SERVO_LOCKED);
}

void openDrogue()
{
    drogueServo.write(SERVO_OPEN);

    Serial.println("DROGUE OPEN");
}

void openMain()
{
    mainServo.write(SERVO_OPEN);

    Serial.println("MAIN OPEN");
}

void openLegs()
{
    legsServo.write(SERVO_OPEN);

    Serial.println("LEGS OPEN");
}