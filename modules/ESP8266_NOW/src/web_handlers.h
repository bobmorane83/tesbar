#ifndef WEB_HANDLERS_H
#define WEB_HANDLERS_H

#include <ESP8266WebServer.h>
#include <LittleFS.h>
#include "config.h"

extern ESP8266WebServer server;

void handleRoot();
void handleUpload();
void handleSimulate();

#endif
