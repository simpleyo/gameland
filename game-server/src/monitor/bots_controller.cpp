#include <sstream>
#include <algorithm>

#include "uws/uWS.h" // uWS library

#include "core/defs.h"
#include "core/utils.h"
#include "config/config.h"
#include "main/main_loop.h"
#include "client_protocol.h"
#include "packet_builder.h"
#include "bots_controller.h"

#define BOT_TRACE(x) 

using namespace std;
using namespace nlohmann;

BotsController* BotsController::_singleton = NULL;

const uint   MAX_RECONNECT_INTENTS = 1;

BotsController::BotsController(uint max_number_of_bots) :
    _hub(new uWS::Hub(/*uWS::PERMESSAGE_DEFLATE*/0, false, 65536)),
    _update_count(0),
    _bots(max_number_of_bots),
    _connected_bots(0),
    _poll_time_us(0)
{    
    RTCHECK(!_singleton);
    _singleton = this;

    for (uint i=0; i<max_number_of_bots; ++i)
        _bots[i].set_bot_id(i);

    _hub->onConnection([this](uWS::WebSocket<uWS::CLIENT> *ws, uWS::HttpRequest http_req) {
        BOT_TRACE("[BotsController] Bot connected to Game Server:");

        RTCHECK(_connected_bots < _bots.size());
        _on_bot_connected(ws);

        _trying_to_connect_bot = false;

        //BOT_TRACE("[Bot]   |-> Address: " << ws->getAddress().address);
        //BOT_TRACE("[Bot]   |-> Port:    " << ws->getAddress().port   << endl);
    });

    _hub->onDisconnection([this](uWS::WebSocket<uWS::CLIENT> *ws, int code, char *message, size_t length) {
        BOT_TRACE("[BotsController] Bot disconnected from Game Server.");

        RTCHECK(_connected_bots > 0);
        --_connected_bots;

        Bot* bot = (Bot*)ws->getUserData();
        bot->on_disconnection();
    });

    _hub->onError([this](void *user) {
        BOT_TRACE("[BotsController] Error al intentar conectar un nuevo bot con el Game Server.");
        _trying_to_connect_bot = false;
    });

    _hub->onMessage([this](uWS::WebSocket<uWS::CLIENT> *ws, char *message, size_t length, uWS::OpCode opCode) {
        string msg(message, length);
        if (opCode == uWS::OpCode::TEXT)
        {
            //BOT_TRACE("MESSAGE: " << msg.c_str());        
            
        }
        else if (opCode == uWS::OpCode::BINARY)
        {
            Bot* bot = (Bot*)ws->getUserData();
            bot->on_packet_received((const ubyte*)message, (uint)length);
        }
    });

    _hub->onPing([](uWS::WebSocket<uWS::CLIENT> *ws, char *message, size_t length) {
        // No hace falta enviar el Pong conrrespondiente porque la libreria uws ya se encarga de hacer eso automaticamente.
        //BOT_TRACE("PING");        
    });

    _hub->onPong([this](uWS::WebSocket<uWS::CLIENT> *ws, char *message, size_t length) {
        //BOT_TRACE("PONG");
    });
}

BotsController::~BotsController()
{
    RTCHECK(_singleton);
    _singleton = NULL;
}

void BotsController::initialize()
{
    _game_server_address = GET_OR_DEF_CONFIG_STR("GAME_SERVER_ADDRESS", "localhost");
    _game_server_port = GET_OR_DEF_CONFIG_VALUE(int, "GAME_SERVER_PORT", 8002);
}

bool BotsController::start()
{    
    return true;
}

void BotsController::_connect()
{
    //BOT_TRACE("[BotsController] call to _connect...");

    _trying_to_connect_bot = true;

    //BOT_TRACE("[BotsController] Connect: " << _game_server_address << ":" << _game_server_port);

    ostringstream oss;
    oss << "wss://" + _game_server_address + ":" << _game_server_port;

    const uint MAX_CONNECT_TIMEOUT_MS = 2000; // En ms
    _hub->connect(oss.str(), nullptr, {}, MAX_CONNECT_TIMEOUT_MS);
}

void BotsController::idle(double delta)
{
    const uint64 last_poll_time_us = _poll_time_us;
    _poll_time_us = get_ticks_usec();
    _hub->poll();

    //TRACE("POLL TIME INTERVAL: " << (_poll_time_us - last_poll_time_us) / 1000 << " ms");
}

void BotsController::process(double delta) 
{ 
    _time += delta;

    //BOT_TRACE("Time: " << get_time());
    //BOT_TRACE("Delta: " << delta);

#if 1
    // Intenta conectar un bot detras de otro. 
    // Esto hace que siempre se este intentando conectar bots lo cual
    // afecta a la frecuencia a la que se llama a poll en esta funcion.
    {
        if ((rand() % 100) < 100) // % de probabilidad de que se conecte un bot
            if (!_trying_to_connect_bot)
                if (_connected_bots < _bots.size())
                {
                    //TRACE("TRY CONNECT NEW BOT");
                    _connect();
                }
    }
#else
    // Conecta todos los bots de una tacada.
    // ATENCION: Los bots que se desconecten no se vuelven a conectar ya que esto solo
    // se ejecuta una vez.
    {
        static bool one_time = true;
        if (one_time)
        {
            ostringstream oss;
            oss << "ws://" + _game_server_address + ":" << _game_server_port;

            for (uint i=0; i<_bots.size(); ++i)
            {
                if (_bots[i].state() == Bot::State::Disconnected)
                {
                    const uint MAX_CONNECT_TIMEOUT_MS = 2000; // En ms
                    _hub->connect(oss.str(), nullptr, {}, MAX_CONNECT_TIMEOUT_MS);
                }
            }

            one_time = false;
        }
    }
#endif

    // Recorre todos los bots y ejecuta <Bot::process>
    for (Bot& bot : _bots)
    {
        if (bot.state() != Bot::State::Disconnected)
            bot.process(delta);
    }

    //const uint64 last_poll_time_us = _poll_time_us;
    //_poll_time_us = get_ticks_usec();
    //_hub->poll();

    ////TRACE("POLL TIME INTERVAL: " << (_poll_time_us - last_poll_time_us) / 1000 << " ms");
}

Bot::Bot() : 
    _state(State::Disconnected), 
    _ws(NULL), 
    _transmission_config({TransmissionMode::Binary, 1}),
    _last_playing_received_packet_time_us(0),
    _last_ok_playing_received_packet_time_us(0),
    _fast_lprp_count(0)
{
}

void Bot::on_packet_received(const ubyte* data, uint data_size) 
{
    Bot& bot = *this;

    if (_state != Bot::State::Playing)
    {
        _server_update_count = 0;
        _expected_server_update_count = 0;
    }
        
    //BOT_TRACE("MESSAGE: " << msg.c_str());
    switch (_state)
    {
    case Bot::State::WaitForServerHandShake: {        
        // Asume que en <data> esta el packet SERVER_HANDSHAKE

        PKB_SEND_PACKET(CLIENT_HANDSHAKE);

        if ((rand() % 1000) <= 1) // probabilidad de enviar un ticket no valido
        {
            PKB_SEND_PACKET(START_GAME, "abc");
        }
        else // Envia un ticket que el servidor interpretara como un ticket valido de un bot
        {
            PKB_SEND_PACKET(START_GAME, "{\"ticket\": \"BOT\"}");
        }
        _state = Bot::State::WaitForGameConfig;
    } break;
    case Bot::State::WaitForGameConfig: {
        // Asume que en <data> esta el packet GAME_CONFIG

        PKB_SEND_PACKET(GAME_CONFIG_OK);
        _state = Bot::State::WaitForGameStartResponse;
    } break;
    case Bot::State::WaitForGameStartResponse: {
        // Detecta el packet GAME_START_OK
        if ((data_size >= 2) && (data[0] == 0) &&
            (data[1] == PROTOCOL_OUT_TOKEN(1)::GAME_START_OK))
        {            
            //PKB_SEND_PACKET(START_GAME, "{\"ticket\": \"BOT\"}");
            _state = Bot::State::Playing;
        }
    } break;
    case Bot::State::Playing: {
        // Detecta el packet VIEW_RESULT
        if ((data_size >= 2) && (data[0] == 0) &&
            (data[1] == PROTOCOL_OUT_TOKEN(1)::VIEW_RESULTS))
        {            
            if (_server_update_count == 0)
                _first_server_update_time_us = get_ticks_usec();

            ++_server_update_count;

            const double ellapsed_time = (get_ticks_usec() - _first_server_update_time_us) / 1000000.0;
            const double server_delta = 1 / 20.0;
            _expected_server_update_count = uint64(ellapsed_time / server_delta);

            if ((int64(_expected_server_update_count) > int64(_server_update_count)) && ((int64(_expected_server_update_count) - int64(_server_update_count)) > 4))
            {
                TRACE("---> WARNING: BOT[" << get_bot_id() << "]" <<
                    "\tServer packets [" << _server_update_count << "]" <<
                    "\tSPD: " << int64(_expected_server_update_count) - int64(_server_update_count));
            }

            if ((get_ticks_usec() - _last_playing_received_packet_time_us) < 10000)
            {
                //TRACE("---> WARNING: BOT[" << get_bot_id() << "] Playing packet received time diff: " << (get_ticks_usec() - _last_playing_received_packet_time_us) / 1000 << " ms");
                ++_fast_lprp_count;
            }
            else
            {
                GET_SINGLETON(BotsController, bc);

                if (_fast_lprp_count >= 8)
                {
                    TRACE("---> WARNING: BOT[" << get_bot_id() << "][" << _fast_lprp_count << 
                        "]\tTime diff: " << (get_ticks_usec() - _last_ok_playing_received_packet_time_us) / 1000 << " ms" <<
                        "\tServer packets [" << _server_update_count << "]" <<
                        "\tSPD: " << int64(_expected_server_update_count) - int64(_server_update_count));
                }
                _fast_lprp_count = 0;
                _last_ok_playing_received_packet_time_us = get_ticks_usec();
            }

            _last_playing_received_packet_time_us = get_ticks_usec();
        }

        // Detecta el packet GAME_FINISHED
        if ((data_size >= 2) && (data[0] == 0) &&
            (data[1] == PROTOCOL_OUT_TOKEN(1)::GAME_FINISHED))
        {            
            PKB_SEND_PACKET(START_GAME, "{\"ticket\": \"BOT\"}");
            _state = Bot::State::WaitForGameConfig;
        }
    } break;
    case Bot::State::PlayFinished: {
    } break;
    }
}

void Bot::on_connection(uWS::WebSocket<uWS::CLIENT>* ws) 
{ 
    _state = State::Connected; 
    _ws = ws; 
    ws->setUserData(this); 

    ubyte data[2] = {
        MESSAGE_FLAGS::MSG_INTERNAL,
        INTERNAL_TOKEN::BIND_REQUEST
    };
    send(data, 2);
    _state = Bot::State::WaitForServerHandShake;

    _bot_process_count = 0;

    _bot_process_count_from_first_server_update = 0;

    _server_update_count = 0;
    _first_server_update_time_us = 0;

    _expected_server_update_count = 0;

    _last_playing_received_packet_time_us = 0;
    _last_ok_playing_received_packet_time_us = 0;
    _fast_lprp_count = 0;
}

void Bot::on_disconnection() 
{ 
    _state = State::Disconnected; 
    _ws = NULL; 
}

void Bot::process(double delta) 
{
    ++_bot_process_count;

    Bot& bot = *this;

    if ((rand() % 100000) <= 1) // Probabilidad de desconectarse
    {
        //_ws->close();
    } 
    else
    {
        if (bot._state == Bot::State::Playing)
        {
#if 0
            // Para comprobar la diferencia de tiempo real que hay entre los mensajes enviados.
            {
                {
                    static uint64_t counter = 0;
                    static uint64_t last_ticks = 0;
                    const uint64_t ticks = get_ticks_usec();
                    const double diff = (double(ticks - last_ticks) / 1000000);
                    TRACE("Sending INPUT_STATE[" << counter << "]... Diff: " << std::fixed << std::setprecision(3) << diff << " seg.");
                    ++counter;
                    last_ticks = ticks;
                }        
            }
#endif
            // Envia el packet INPUT_STATE
            {
                static uint64_t counter = 0;
                ++counter;
                if ((counter % 60) == 0) // ATENCION: Envia solo un INPUT_STATE por segundo porque si se envian 60 por segundo se satura antes la interface de red.
                    PKB_SEND_PACKET(INPUT_STATE, 0, 0, Point2(), 0);
            }
        }
    }
}

void BotsController::_on_bot_connected(uWS::WebSocket<uWS::CLIENT>* ws)
{
    // Recorre todos los bots y conecta el primero que este desconectado.
    for (Bot& bot : _bots)
    {
        if (bot.state() == Bot::State::Disconnected)
        {
            RTCHECK(_connected_bots < _bots.size());
            bot.on_connection(ws);
            ++_connected_bots;
            break;
        }
    }
}

void BotsController::finalize() 
{ 
    _hub->poll(); // Necesario para enviar el comando unreg... ya que sino el websocket se cierra en _hub->getDefaultGroup<uWS::CLIENT>().terminate() y nunca se envia el comando unreg...

    _hub->getDefaultGroup<uWS::CLIENT>().terminate();
    _hub->getLoop()->stop();
    while (_hub->getLoop()->isAlive()) _hub->poll();
}

void testBroadcast() {
    uWS::Hub h;

    const char *broadcastMessage = "This will be broadcasted!";
    size_t broadcastMessageLength = strlen(broadcastMessage);

    int connections = 2;
    h.onConnection([&h, &connections, broadcastMessage, broadcastMessageLength](uWS::WebSocket<uWS::SERVER> *ws, uWS::HttpRequest req) {
        if (!--connections) {
            std::cout << "Broadcasting & closing now!" << std::endl;
            h.getDefaultGroup<uWS::SERVER>().broadcast(broadcastMessage, broadcastMessageLength, uWS::OpCode::TEXT);
            h.getDefaultGroup<uWS::SERVER>().close();
        }
    });

    int broadcasts = connections;
    h.onMessage([&broadcasts, broadcastMessage, broadcastMessageLength](uWS::WebSocket<uWS::CLIENT> *ws, char *message, size_t length, uWS::OpCode opCode) {
        if (length != broadcastMessageLength || strncmp(message, broadcastMessage, broadcastMessageLength)) {
            std::cout << "FAILURE: bad broadcast message!" << std::endl;
            exit(-1);
        } else {
            broadcasts--;
        }
    });

    h.onDisconnection([](uWS::WebSocket<uWS::CLIENT> *ws, int code, char *message, size_t length) {
        if (code != 1000) {
            std::cout << "FAILURE: Invalid close code!" << std::endl;
            //exit(-1);
        }
    });

    h.onConnection([&h, &connections, broadcastMessage, broadcastMessageLength](uWS::WebSocket<uWS::CLIENT> *ws, uWS::HttpRequest req) {
        std::cout << ws << " " << ws->getAddress().address << ":" << ws->getAddress().port << std::endl;
        h.getDefaultGroup<uWS::CLIENT>().close(1000);
    });

    h.onError([](void *user) {
        BOT_TRACE("Error al intentar conectar: " << *((int*)user));
    });


    //h.onCancelledHttpRequest(std::function<void(HttpResponse *)> handler);


    //h.listen(3000);
    int data[14] = {0, 1};
    const uint MAX_CONNECT_TIMEOUT_MS = 0; // En ms
    for (int i = 0; i < connections; i++) {
        h.connect("ws://127.0.0.1:8000", ((int*)data)+i, {}, MAX_CONNECT_TIMEOUT_MS);
    }

    h.run();

    if (broadcasts != 0) {
        std::cout << "FAILURE: Invalid amount of broadcasts received!" << std::endl;
        exit(-1);
    }

    std::cout << "Falling through now!" << std::endl;
}
