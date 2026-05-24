#include "flight_logic.h"
#include "config.h"
#include "sensors.h"
#include "servos.h"

#include <Arduino.h>

enum FlightState
{
    WAIT_FOR_DROP,
    DROGUE_PHASE,
    MAIN_PHASE,
    LEGS_PHASE,
    LANDED
};

FlightState state = WAIT_FOR_DROP;

unsigned long stateTimer = 0;

bool drogueOpened = false;
bool mainOpened = false;
bool legsOpened = false;

void updateFlightLogic()
{
    float altitude = getFilteredAltitude();

    switch(state)
    {
        // =========================================
        // WAIT FOR DROP
        // =========================================
        case WAIT_FOR_DROP:

            if (altitude > DROP_DETECTION_ALTITUDE)
            {
                openDrogue();

                drogueOpened = true;

                state = DROGUE_PHASE;

                stateTimer = millis();

                Serial.println("DROP DETECTED");
            }

        break;

        // =========================================
        // DROGUE
        // =========================================
        case DROGUE_PHASE:

            if (
                millis() - stateTimer >
                MAIN_OPEN_DELAY
            )
            {
                openMain();

                mainOpened = true;

                state = MAIN_PHASE;
            }

        break;

        // =========================================
        // MAIN
        // =========================================
        case MAIN_PHASE:

            if (altitude < LEGS_OPEN_ALTITUDE)
            {
                openLegs();

                legsOpened = true;

                state = LEGS_PHASE;
            }

        break;

        // =========================================
        // LEGS
        // =========================================
        case LEGS_PHASE:

            if (altitude < LAND_DETECTION_ALT)
            {
                state = LANDED;

                Serial.println("LANDED");
            }

        break;

        // =========================================
        // LANDED
        // =========================================
        case LANDED:

        break;
    }
}