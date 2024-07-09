#pragma once

#include <memory>
#include <functional>
#include <vector>

#include "core/types.h"
#include "core/utils.h"

class Timer;


class Timers
{
public:
    Timers() {}
    virtual ~Timers() {}

    void process_timers();
    Timer* add_timer(Timer* timer); // ATENCION: La frecuencia de llamada del timer nunca podra ser mayor que la frecuencia a la que se llame a process_timers.
    void remove_timer(Timer* timer);

private:        
    std::vector<std::unique_ptr<Timer>> _timers;
};

class Timer
{
    friend class Timers;

public:
    using callback_t = std::function<void(Timer*, double)>;

    // If timeout is zero, the callback fires on the next call to process_timers. 
    // If repeat is non-zero, the callback fires first after timeout milliseconds and then repeatedly after repeat milliseconds.
    Timer(callback_t callback, int64_t timeout, int64_t repeat) : // En milisegundos
        _callback(callback), _timeout(timeout * 1000), _repeat(repeat * 1000) 
    {
        _start_ticks = 0;
        _last_execution_ticks = 0;
    }

    void start() { _start_ticks = get_ticks_usec(); }
    void stop() { _start_ticks = 0; }

private:
    callback_t _callback;
    uint64_t _start_ticks;   // En microsegundos. Tiempo en el que fue creado este timer.
    uint64_t _last_execution_ticks;   // En microsegundos. Tiempo en el que se ejecuto por ultima vez.
    uint64_t _timeout;      // En microsegundos. 
    uint64_t _repeat ;      // En microsegundos.
};