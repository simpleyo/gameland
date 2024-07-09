#pragma once

#include <string>
#include <vector>

#include "uws/uWS.h"

#include "core/defs.h"

class Bot
{
public:
    enum class State {
        Disconnected,
        Connected,
        WaitForServerHandShake,
        WaitForGameConfig,
        WaitForGameStartResponse,
        Playing,
        PlayFinished
    };

    struct TransmissionConfig {
        TransmissionMode::_ mode;
        uint                version;
    };

public:
    Bot();
    
    void process(double delta);

    State state() const { return _state; }
    
    const TransmissionConfig& get_transmission_config() const { return _transmission_config; }

    void send(const ubyte* data, uint data_size) { RTCHECK(_ws != NULL); _ws->send((const char*)data, data_size, uWS::OpCode::BINARY); }

    void set_bot_id(IDR id) { _bot_id = id; }
    IDR get_bot_id() const { return _bot_id; }

    void on_connection(uWS::WebSocket<uWS::CLIENT>* ws);
    void on_disconnection();
    void on_packet_received(const ubyte* data, uint data_size);

private:
    State _state;
    uWS::WebSocket<uWS::CLIENT>* _ws;

    TransmissionConfig _transmission_config;

    IDR _bot_id;

    uint64  _server_update_count; // Cuenta de los paquetes VIEW_RESULTS recibidos.

    uint64 _expected_server_update_count;

    // Tiempo de cuando se recibe el primer paquete VIEW_RESULTS.
    // Se utiliza para calcular cuentos paquetes VIEW_RESULTS se deberian haber recibido hasta el momento.
    // Cuando se recibe el primer paquete VIEW_RESULTS, el bot espera que
    // se reciba un nuevo paquete VIEW_RESULTS cada server delta segundos (server delta = (1 / 20) segundos).
    uint64  _first_server_update_time_us; 

    uint64  _bot_process_count = 0; // Las veces que se ha llamado a process desde que el bot se conecto.

    uint64  _bot_process_count_from_first_server_update = 0; // Las veces que se ha llamado a process desde que _server_update_count se incremento desde 0 a 1. Este valor se pone a 0 cada vez que el bot se conecta.

    uint64  _last_playing_received_packet_time_us;
    uint64  _last_ok_playing_received_packet_time_us;
    uint    _fast_lprp_count;
};

class BotsController
{
public:
    static BotsController* get_singleton() { return _singleton; }

    BotsController(uint max_number_of_bots);
    virtual ~BotsController();

    void initialize();
    bool start();
    void idle(double delta);
    void process(double delta);
    void finalize();
        
    Bot::State get_state() const { return _state; }

    double get_time() const { return _time; }

    uint64 get_poll_time_us() const { return _poll_time_us; }

private:    
    void _connect();
    void _on_bot_connected(uWS::WebSocket<uWS::CLIENT>* ws);

private:
    static BotsController* _singleton;

    std::unique_ptr<uWS::Hub>       _hub;
    
    Bot::State  _state;

    double      _time;

    uint64      _update_count;

    bool        _trying_to_connect_bot;

    std::vector<Bot> _bots;
    uint        _connected_bots;    // Numero de bots cuyo estado no es Disconnected

    std::string _game_server_address;
    uint        _game_server_port;

    uint64      _poll_time_us;
};

