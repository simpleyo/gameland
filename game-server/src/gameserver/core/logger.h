#pragma once

#include <string>

#include "core/types.h"

void logger_init();
void logger_term();
void logger_configure();
void logger_log(const std::string& msg);
void logger_disable_console_output();