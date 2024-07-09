#include <cinttypes>
#include <fstream>
#include <mutex>
#include <algorithm>
#include <random>
#include <chrono> 

#include "core/defs.h"
#include "core/utils.h"
#include "core/timers.h"
#include "config/config.h"
#include "bots_controller.h"
#include "packet_builder.h"
#include "main/main_loop.h"
#include "main/cmain.h"

using namespace std;

////////////////////////////////////////////
// MAIN DATA
//

static Config* config;
static MainLoop* main_loop;
static PacketBuilder* packet_builder;
static BotsController* bots_controller;

static Timers* timers; // Se utilizan para timeouts superiores a (1 / IPS) segundos. Si son inferiores entonces llamar en <Main::idle> directamente.

//static uint   tc_iterations_per_second;  // IPS: Numero deseado de iteraciones, por segundo. Cada iteracion es una llamada a <Main::iteration>
static uint64 tc_first_iteration_us;     // Tiempo de la primera llamada a <Main::iteration>

//
////////////////////////////////////////////

void Main::configure(int argc, char **argv)
{ 
    // Crea el objeto <config> y lo inicializa a partir del fichero de configuracion monitor.cfg.
    {
//#ifdef _DEBUG
#ifdef __linux__
        //std::ifstream ifs("/mnt/g/DEV/Projects/gameland/game-server/monitor.cfg");
        std::ifstream ifs("./monitor.cfg");
#else
        std::ifstream ifs("G:/DEV/Projects/gameland/game-server/monitor.cfg");
#endif
//#else
//        std::ifstream ifs("./gameserver.cfg");
//#endif
        RTCHECK(ifs.is_open());
        const std::string str((std::istreambuf_iterator<char>(ifs)), std::istreambuf_iterator<char>());
    
        config = new Config(str);
    }

    // Lee los argumentos de la linea de comandos y define las variables de configuracion que sean necesarias.
    {
        // Argumento[0]: Ruta completa del programa.
        // Argumento[1]: [Opcional] Game server address.
        // Argumento[2]: [Opcional] Game server port. Es obligatorio si existe el argumento 1.
        // Argumento[3]: [Opcional] Maximo numero de bots. Es obligatorio si existe el argumento 2.

        if (argc > 1)
        {
            RTCHECK(argc == 4);

#ifdef _WIN32
            // Mediante esto se consigue que el monitor este asociado a una consola propia en lugar de la
            // consola del proceso que lo lanzo.
            {
                FreeConsole();
                AllocConsole();
            }
#endif

            for (int i=0; i<argc; ++i)
            {
                TRACE("Argument[" << i << "]: " << argv[i]);
            }

            TRACE("[Main] Args: " << argc);
            OVERWRITE_CONFIG_STR(GAME_SERVER_ADDRESS, std::string(argv[1]));
            OVERWRITE_CONFIG_VALUE(uint, GAME_SERVER_PORT, atoi(argv[2]));
            OVERWRITE_CONFIG_VALUE(uint, MAX_NUMBER_OF_BOTS, atoi(argv[3]));
        }
        else
        {
        }
    }

    TRACE("[Main] Monitor configured.");
}

// setup:
//  - Se lee la configuracion del servidor.
//  - Se crean los objetos globales del servidor.
//
void Main::setup()
{
    TRACE("[Main] Starting monitor...");

#if 0
    SetConsoleCtrlHandler(HandlerRoutine, TRUE);
#endif

    srand(uint(time(0)));

    // Time control variables.
    {
        //tc_iterations_per_second = GET_CONFIG_VALUE(uint, "IPS");
        tc_first_iteration_us = 0;
    }

    //event_manager = new EventManager;

    //resource_manager = new ResourceManager;
    packet_builder = new PacketBuilder;
    //ws_server = new ws::WSServer;
    //   
    //const string controller_type = GET_CONFIG_STR("CONTROLLER_TYPE");
    //if (controller_type == "default")
    //    controller = new Controller;
    //else
    //    RTCHECK(false);

    //request_coder = new RequestCoder;

    //user_manager = new UserManager(SRVCONFIG.MAX_NUMBER_OF_USERS);

    //engine_context = new EngineContext;
    //engine_instance = new engine::simple::Engine;
    //RTCHECK(SRVCONFIG.MAX_NUMBER_OF_PLAYERS <= SRVCONFIG.MAX_NUMBER_OF_USERS);
    //game_context = new TanksGameContext(SRVCONFIG.MAX_NUMBER_OF_USERS, SRVCONFIG.MAX_NUMBER_OF_PLAYERS);
        
    bots_controller = new BotsController(MNRCONFIG.MAX_NUMBER_OF_BOTS);
    main_loop = new MainLoop;

    TRACE("[Main] Max number of bots: " << MNRCONFIG.MAX_NUMBER_OF_BOTS);

    timers = new Timers;
}

struct TimerFunctions
{
    //static void user_manager_free_expired_users(Timer* timer, double delta) { SINGLETON(UserManager)->free_expired_users(); }
    //static void controller_update(Timer* timer, double delta) { SINGLETON(IController)->process(delta); }
    //static void game_context_update(Timer* timer, double delta) { SINGLETON(GameContext)->process(delta); }
};

// initialize:
//  - Inicializa los objetos globales del servidor.
//
bool Main::initialize()
{
    //timers->add_timer(new Timer(TimerFunctions::user_manager_free_expired_users, 0, 2100))->start();
    //timers->add_timer(new Timer(TimerFunctions::controller_update,  0, 500))->start();    
    //timers->add_timer(new Timer(TimerFunctions::game_context_update,  0, 1000))->start();    
    //
    //event_manager->initialize();

    //resource_manager->initialize();

    //game_context->initialize();

    //user_manager->initialize();

    //ws_server->start_listening(ws::WSServerListenParams().
    //    set_max_peer_count(SRVCONFIG.MAX_NUMBER_OF_USERS).
    //    set_listen_port(SRVCONFIG.GAME_SERVER_PORT)
    //);

    bots_controller->initialize();

    return bots_controller->start();
}

void Main::finalize()
{
    bots_controller->finalize();

    //if (SINGLETON(ws::WSServer)->is_listening())
    //    SINGLETON(ws::WSServer)->stop_listening();
    //
    //user_manager->finalize();

    //game_context->finalize();
    //
    //resource_manager->finalize();

    //event_manager->finalize();
}

// cleanup:
//  - Destruye los objetos creados en <setup>.
//
void Main::cleanup()
{
    delete timers;
    delete main_loop;
    //delete game_context;
    //delete engine_instance;
    //delete engine_context;
    //delete user_manager;
    //delete request_coder;
    delete bots_controller;
    //delete ws_server;
    delete packet_builder;
    //delete resource_manager;
    //delete event_manager;
    delete config;
}

uint Main::IPS() { return 60; }
uint Main::UPS() { return 20; }

void Main::run()
{
    main_loop->init();

	while (true) 
    {
		if (iteration() == true)
			break;
	}

    main_loop->finish();

    this_thread::sleep_for(chrono::milliseconds(500));
}

// iteration:
//  - Retorna true si hay que terminar el loop principal.
//
//bool Main::iteration()
//{ 
//    static uint64 tc_last_iteration_us;      // Tiempo de la ultima llamada a <Main::iteration>
//    static double tc_real_time;              // Tiempo real, en segundos, acumulado desde la primera llamada a <Main::iteration>
//    static double tc_logic_time;             // Tiempo logico del servidor, en segundos. Se va incrementando en (1 / tc_iterations_per_second) segundos desde la primera llamada a <Main::iteration>
//    static uint64 tc_accum_time_us;          // Se utiliza para detectar que ha pasado un segundo de tiempo.
//    static uint   tc_accum_real_iterations ; // Acumula el numero de llamadas a <Main::iteration> que se han producido en un segundo.
//    static uint   tc_accum_logic_iterations; // Acumula el numero de llamadas a <MainLoop::iteration> que se han producido en un segundo.
//    static double tc_accum_load;
//    static uint64 tc_last_idle_us;           // Tiempo de la ultima llamada a <idle>
//    
//    const uint64 current_iteration_us = get_ticks_usec();        
//
//    if (tc_first_iteration_us == 0)
//    {
//        tc_first_iteration_us = current_iteration_us;
//
//        tc_last_iteration_us  = current_iteration_us;
//        tc_real_time  = 0;
//        tc_logic_time = 0;
//        tc_accum_time_us = 0;
//        tc_accum_real_iterations  = 0;
//        tc_accum_logic_iterations = 0;
//        tc_accum_load = 0;    
//
//        tc_last_idle_us = current_iteration_us;
//    }
//    else
//    {
//        tc_real_time = (current_iteration_us - tc_first_iteration_us) / 1000000.0;
//
//        const uint64 delta = (current_iteration_us - tc_last_iteration_us); 
//
//        tc_accum_time_us += delta;
//
//        tc_last_iteration_us = current_iteration_us;
//    }       
//    
//    ++tc_accum_real_iterations;
//
//    const double logic_step = (1.0 / tc_iterations_per_second);
//
//    bool exit = false;
//
//    uint main_loop_iter_count = 0;
//    while ((tc_real_time >= tc_logic_time) && !exit)
//    {
//        ++tc_accum_logic_iterations;
//
//        if (main_loop->iteration(logic_step)) // MainLoop::iteration
//            exit = true;
//
//        const double elapsed_time = ((get_ticks_usec() - tc_first_iteration_us) / 1000000.0) - tc_real_time;
//
//        tc_accum_load += elapsed_time;
//
//        tc_real_time += elapsed_time;
//        tc_logic_time += logic_step;        
//
//        //TRACE("Real: " << tc_real_time << "     Logic: " << tc_logic_time);
//        ++main_loop_iter_count;
//
//        if (main_loop_iter_count > 8)
//            break;
//    }
//
//    if (tc_accum_time_us > 1000000)
//    {
//        const double accum_load = (tc_accum_logic_iterations != 0) ? ((tc_accum_load / tc_accum_logic_iterations) / logic_step) : 1.0;
//
//        if (accum_load > 0.8) {
//            TRACE("[Main] WARNING: Real IPS: " << tc_accum_real_iterations << "\tLogic IPS: " << tc_accum_logic_iterations << "\tLoad: " << uint(accum_load * 100) << "%");
//        }
//        else {        
//            //TRACE("[Main] IPS: " << tc_accum_real_iterations << "\tLoad: " << uint(accum_load * 100) << "%");
//        }
//
//        tc_accum_time_us %= 1000000;
//        tc_accum_real_iterations = 0;
//        tc_accum_logic_iterations = 0;
//        tc_accum_load = 0;
//    }
//
//    // idle
//    {
//        const uint64 ct = get_ticks_usec();
//        const double delta = ((ct - tc_last_idle_us) / 1000000.0);
//        tc_last_idle_us = ct;
//
//        main_loop->idle(delta);
//
//        tc_real_time = ((get_ticks_usec() - tc_first_iteration_us) / 1000000.0);
//    }
//
//    if (tc_real_time < tc_logic_time)
//    {
//        this_thread::sleep_for(chrono::microseconds(uint64((tc_logic_time - tc_real_time) * 1000000.0)));
//    }
//    
//    return exit;
//}
//
//


bool Main::iteration()
{ 
    bool exit = false;
    
    const uint64 desired_delta_us = 1000000 / IPS();

    static uint64 last_iteration_time_us = 0;
    const uint64 current_iteration_time_us = get_ticks_usec();
    const double delta = (current_iteration_time_us - last_iteration_time_us) / 1000000.0;
    
    main_loop->iteration(delta);

    const uint64 IDLE_MAX_DURATION = 5000; // Maxima duracion que deberia tener una llamada a main_loop->idle, en us, para no afectar a las veces por segundo que se llama a main_loop->iteration. 
    static uint64 last_idle_time_us = 0;
    uint64 time_us = get_ticks_usec();
    while ((time_us + IDLE_MAX_DURATION) < (current_iteration_time_us + desired_delta_us))
    {        
        const double idle_delta = (last_idle_time_us == 0) ? 0 : ((time_us - last_idle_time_us) / 1000000.0);
        last_idle_time_us = time_us;

        const uint64 begin_idle_us = time_us;

        main_loop->idle(idle_delta);

        time_us = get_ticks_usec();

        if ((time_us - begin_idle_us) >= IDLE_MAX_DURATION)
        {
            TRACE("WARNING: Idle ha durado mas de " << IDLE_MAX_DURATION << " us.");
        }
    }

    while (get_ticks_usec() < (current_iteration_time_us + desired_delta_us));

    last_iteration_time_us = current_iteration_time_us;

    return exit;
}


