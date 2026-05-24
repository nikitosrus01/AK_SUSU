#include "config.h"
#include "sensors.h"

#include <Wire.h>
#include <Adafruit_BMP280.h>

Adafruit_BMP280 bmp;

float groundAltitude = 0;
float altitude = 0;
float filteredAltitude = 0;

void initSensors()
{
    #ifdef ESP32
        Wire.begin(SDA_PIN, SCL_PIN);
    #else
        Wire.begin();
    #endif

    if (!bmp.begin(0x76))
    {
        Serial.println("BMP280 ERROR");

        while(1);
    }

    Serial.println("CALIBRATING ALTITUDE...");

    float sum = 0;

    for(int i = 0; i < 100; i++)
    {
        sum += bmp.readAltitude(1013.25);

        delay(50);
    }

    groundAltitude = sum / 100.0;

    Serial.print("GROUND ALTITUDE: ");
    Serial.println(groundAltitude);
}

void updateSensors()
{
    altitude =
        bmp.readAltitude(1013.25) -
        groundAltitude;

    filteredAltitude =
        ALTITUDE_FILTER_ALPHA * altitude +
        (1.0 - ALTITUDE_FILTER_ALPHA) * filteredAltitude;
}

float getAltitude()
{
    return altitude;
}

float getFilteredAltitude()
{
    return filteredAltitude;
}