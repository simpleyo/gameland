#pragma once

#include <string>
#include <iostream>
#include <sstream>
#include <mutex>
#include <thread>
#include <cstdint>

#include "core/logger.h"

//extern std::mutex _trace_mut;

//#define TRACE(msg) { std::ostringstream out; out << "[" << std::this_thread::get_id() << "] " << msg << std::endl; { std::lock_guard<std::mutex> lock(_trace_mut); std::cout << out.str(); }; }
#define TRACE(msg) { std::ostringstream out; out << msg << std::endl; logger_log(out.str()); }

    