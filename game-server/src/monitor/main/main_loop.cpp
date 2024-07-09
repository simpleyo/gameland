#include <cinttypes>
#include <sstream>
#include <iomanip>
#include <iostream>
#include <algorithm>
#include <functional>

#include "core/defs.h"
#include "core/timers.h"
#include "main/main_loop.h"
#include "bots_controller.h"

using namespace std;

MainLoop* MainLoop::_singleton = NULL;

MainLoop::MainLoop() :
    _timers(new Timers)
{
    _singleton = this;
}

MainLoop::~MainLoop() 
{
    _singleton = NULL;
}

void MainLoop::init() 
{
}

void MainLoop::finish() 
{
}

void MainLoop::quit()
{
}

void MainLoop::idle(double p_delta)
{
    //TRACE("IDLE Delta: " << p_delta);
    _timers->process_timers();

    SINGLETON(BotsController)->idle(p_delta);
}

bool MainLoop::iteration(double p_delta)
{
    //TRACE("ITERATION Delta: " << p_delta);
    SINGLETON(BotsController)->process(p_delta);

    return false;
}

