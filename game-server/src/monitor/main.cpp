#include <iostream>
#include "core/signals.h"
#include "core/logger.h"
#include "main/cmain.h"

using namespace std;

void testBroadcast();

namespace app
{
    static bool _must_exit = false; // private

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
    }

    void fatal_error() 
    {
        logger_term();
        ::exit(1);
    }
}

int main(int argc, char **argv)
{	
    //testBroadcast();

    app::init();

    while (!app::must_exit())
    {        
        Main::configure(argc, argv);

        Main::setup();  
    
        if (Main::initialize())
            Main::run();

        Main::finalize();
        
        Main::cleanup();   
    }

    app::term();
}
