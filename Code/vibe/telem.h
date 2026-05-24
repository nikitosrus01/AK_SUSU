#ifndef CONFIG_H
#define CONFIG_H

// =====================================================
// PLATFORM DETECT
// =====================================================

#ifdef ESP32
    #define DEBUG_BAUD 115200
#else
    #define DEBUG_BAUD 9600
#endif

// =====================================================
// SERVO PINS
// =====================================================

#ifdef ESP32

    #define DROGUE_SERVO_PIN 23
    #define MAIN_SERVO_PIN   18
    #define LEGS_SERVO_PIN   19

#else

    #define DROGUE_SERVO_PIN 5
    #define MAIN_SERVO_PIN   6
    #define LEGS_SERVO_PIN   9

#endif

// =====================================================
// I2C PINS
// =====================================================

#ifdef ESP32

    #define SDA_PIN 21
    #define SCL_PIN 22

#endif

// =====================================================
// SERVO POSITIONS
// =====================================================

#define SERVO_LOCKED 0
#define SERVO_OPEN   90

// =====================================================
// FLIGHT PARAMETERS
// =====================================================

#define DROP_DETECTION_ALTITUDE 3.0
#define MAIN_OPEN_DELAY         2000
#define LEGS_OPEN_ALTITUDE      25.0
#define LAND_DETECTION_ALT      1.0

// =====================================================
// FILTER
// =====================================================

#define ALTITUDE_FILTER_ALPHA 0.1

#endif