#include "config.h"

#include "sensors.h"
#include "servos.h"
#include "telemetry.h"
#include "logger.h"
#include "flight_logic.h"

void setup()
{
    Serial.begin(DEBUG_BAUD);

    delay(1000);

    Serial.println("FLIGHT COMPUTER START");

    initSensors();

    initServos();

    initLogger();

    Serial.println("SYSTEM READY");
}

void loop()
{
    updateSensors();

    float altitude =
        getFilteredAltitude();

    updateFlightLogic();

    sendTelemetry(
        altitude,
        0
    );

    logData(
        millis(),
        altitude,
        0
    );

    delay(50);
}