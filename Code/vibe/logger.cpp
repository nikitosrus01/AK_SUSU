#include "logger.h"

#include <Arduino.h>
#include <SPI.h>
#include <SD.h>

// =====================================================
// SD CONFIG
// =====================================================

#define SD_CS_PIN 5

File logFile;

// =====================================================
// INIT LOGGER
// =====================================================

void initLogger()
{
    Serial.println("INIT SD CARD...");

    if (!SD.begin(SD_CS_PIN))
    {
        Serial.println("SD INIT FAILED");

        while (1);
    }

    Serial.println("SD INIT OK");

    // =============================================
    // CREATE FILE
    // =============================================

    logFile = SD.open("/flight.csv", FILE_WRITE);

    if (!logFile)
    {
        Serial.println("FILE CREATE FAILED");

        while (1);
    }

    // =============================================
    // CSV HEADER
    // =============================================

    logFile.println("TIME_MS,ALTITUDE_M,STATE");

    logFile.flush();

    Serial.println("CSV FILE READY");
}

// =====================================================
// LOG DATA
// =====================================================

void logData(
    unsigned long timeMs,
    float altitude,
    int state
)
{
    logFile.print(timeMs);

    logFile.print(",");

    logFile.print(altitude);

    logFile.print(",");

    logFile.println(state);

    // =============================================
    // SAVE TO SD
    // =============================================

    logFile.flush();
}