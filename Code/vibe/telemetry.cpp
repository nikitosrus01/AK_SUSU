#include "telemetry.h"

#include <Arduino.h>

void sendTelemetry(
    float altitude,
    int state
)
{
    Serial.print("ALT: ");
    Serial.print(altitude);

    Serial.print(" | STATE: ");
    Serial.println(state);
}