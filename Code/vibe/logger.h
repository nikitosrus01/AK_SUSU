#ifndef LOGGER_H
#define LOGGER_H

void initLogger();

void logData(
    unsigned long timeMs,
    float altitude,
    int state
);

#endif