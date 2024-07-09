#pragma once

#include <algorithm>

#include "timers.h"

// If timeout is zero, the callback fires on the next event loop iteration. 
// If repeat is non-zero, the callback fires first after timeout milliseconds and then repeatedly after repeat milliseconds.
Timer* Timers::add_timer(Timer* timer)
{
    _timers.push_back(std::unique_ptr<Timer>(timer));    
    return timer;
}

void Timers::remove_timer(Timer* timer)
{
     _timers.erase(remove_if(_timers.begin(), _timers.end(), 
         [&](const std::unique_ptr<Timer>& a) { return a.get() == timer; }), _timers.end()); // erase-remove idiom
}

void Timers::process_timers()
{
    for (std::unique_ptr<Timer>& t : _timers)
    {        
        if (t->_start_ticks > 0)
        {
            if (t->_last_execution_ticks == 0)
            {
                const uint64 current_ticks = get_ticks_usec();
                const uint64 ellapsed_ticks = current_ticks - t->_start_ticks; // microsegundos
                if (ellapsed_ticks >= t->_timeout)
                {
                    const double delta = t->_timeout / 1000000.0;
                    t->_last_execution_ticks = current_ticks;
                    t->_callback(t.get(), delta);
                }
            }
            else
            {
                const uint64 current_ticks = get_ticks_usec();
                const uint64 ellapsed_ticks = get_ticks_usec() - t->_last_execution_ticks; // microsegundos                

                if (ellapsed_ticks >= t->_repeat)
                {
                    const double delta = t->_repeat / 1000000.0;
                    t->_last_execution_ticks = current_ticks;
                    t->_callback(t.get(), delta);
                }
            }
        }
    }
}