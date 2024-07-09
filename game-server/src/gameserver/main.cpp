#include <iostream>
#include <string>

#include "core/signals.h"
#include "core/logger.h"
#include "main/cmain.h"
#include "test/workers.h"
#include "modules/event/event_manager.h"

namespace app
{
 // app private data

    static bool _must_exit = false;
    static const uint _MAX_RESTART_COUNT = 1000; 
    static uint _restart_count = 0;

// app public interface

    void init() 
    {
        srand(uint(time(0)));

        logger_init();
        signals_hook(); // Debe ejecutarse despues de logger_init ya que el manejador de las signals asume que el logger ya esta inicializado.
    }
    void term() { logger_term(); }
    void set_must_exit(bool v) { _must_exit = v; }
    bool must_exit() { return _must_exit; }
    void exit() 
    {
        set_must_exit(true);
        SINGLETON(EventManager)->exec<Event::GAME_SERVER_RESET>({});    
    }
    void fatal_error() 
    {
        logger_term();
        ::exit(1);
    }
    void check_restart_limit()
    {
        // Pone un limite a las veces que se puede recomenzar el gameserver.
        // Esto evita un posible crecimiento sin limite de la memoria en uso
        // provocado por posibles memory leaks.
        ++_restart_count;
        if (_restart_count > _MAX_RESTART_COUNT)
        {
            TRACE("MAX_RESTART_COUNT superado.");
            set_must_exit(true);
        }
    }
}

int main(int argc, char **argv)
{	
    //workers_test();
    //return 0;

    app::init();

    while (!app::must_exit())
    {        
        Main::configure(argc, argv);

        Main::setup();        
    
        if (Main::initialize())
            Main::run();

        Main::finalize();
        
        Main::cleanup();   

        app::check_restart_limit(); // Pone un limite a las veces que se puede recomenzar el gameserver.
    }

    app::term();
}
