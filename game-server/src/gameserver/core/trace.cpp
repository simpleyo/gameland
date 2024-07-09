#pragma once

#include <string>
#include <iostream>
#include <sstream>
#include <thread>
#include <mutex>

#include "trace.h"

std::mutex _trace_mut;