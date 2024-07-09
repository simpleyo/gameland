#include <csignal>

#include "core/logger.h"
#include "core/trace.h"

namespace app { void exit(); };

static void _signal_handler(int signal_num)
{
    //TRACE("The interrupt signal is (" << signal_num << "). \n");

    app::exit();

    //logger_term();
    //exit(signal_num); // It terminates the  program
}
 
void signals_hook()
{	    
    signal(SIGINT,  _signal_handler);  // interrupt
    signal(SIGILL,  _signal_handler);  // illegal instruction - invalid function image
    signal(SIGFPE,  _signal_handler);  // floating point exception
    signal(SIGSEGV, _signal_handler);  // segment violation
    signal(SIGTERM, _signal_handler);  // Software termination signal from kill
#ifdef _WIN32
    signal(SIGBREAK,_signal_handler);  // Ctrl-Break sequence
#endif
    signal(SIGABRT, _signal_handler);  // abnormal termination triggered by abort call
}
