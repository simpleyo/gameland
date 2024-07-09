#pragma once

#include <sstream>
#include <string>
#include <vector>

#include "core/types.h"

// Asume que la variable bot esta definida.
#define PKB_SEND_PACKET(token, ...) {                    \
    PacketBuilder* pkb = PacketBuilder::get_singleton(); \
    RTCHECK(pkb);                                        \
    _PKB_BUILD_PACKET(token, __VA_ARGS__);               \
    PacketBuilder::Packet pk = pkb->get_packet();        \
    bot.send(pk.data, pk.size);                          \
}

// Detalles de implementacion
// [
#define _PKB_BUILD_PACKET(token, ...)                                         \
    const Bot::TransmissionConfig& tc = bot.get_transmission_config();        \
    RTCHECK(tc.version);                                                      \
    pkb->build_##token (tc.version, tc.mode, __VA_ARGS__);

#define _PKB_IMPLEMENT_SELECT_VERSION(token, vers, ...)                                      \
    if (version == vers)                                                                     \
        if      (mode == Mode::Text)   _build_packet_##token <1, Mode::Text>(__VA_ARGS__);   \
        else if (mode == Mode::Binary) _build_packet_##token <1, Mode::Binary>(__VA_ARGS__);          

#define _PKB_IMPLEMENT_BUILD_CALL(token, ...)            \
    RTCHECK(version);                                    \
    _PKB_IMPLEMENT_SELECT_VERSION(token, 1, __VA_ARGS__)
// ]

namespace _namespace_packet_builder {

    class PacketBuilderImplBase;

    struct Packet {
        Packet(const ubyte* d, uint s) : data(d), size(s) {}
        const ubyte* data;
        uint         size;
    };

    struct CurrentBuild
    {
        CurrentBuild() {}
        void clear() { buffer.clear(); }

        std::vector<ubyte>     buffer;
    };
}

class PacketBuilder
{
    using ImplBase = _namespace_packet_builder::PacketBuilderImplBase;

public:
    using Packet   = _namespace_packet_builder::Packet;
    using Mode = TransmissionMode::_;
    using CurrentBuild = _namespace_packet_builder::CurrentBuild;

public:
    static PacketBuilder* get_singleton() { return _singleton; }    

    PacketBuilder(); 
    virtual ~PacketBuilder();

    Packet get_packet() const { return Packet(_cb.buffer.data(), (uint)_cb.buffer.size()); }
    
    void reset() { _cb.clear(); }

    void build_CLIENT_HANDSHAKE (uint version, Mode mode)                                                                                  { _PKB_IMPLEMENT_BUILD_CALL(CLIENT_HANDSHAKE); }     
    void build_GAME_PING        (uint version, Mode mode, uint p_game_ping_id)                                                             { _PKB_IMPLEMENT_BUILD_CALL(GAME_PING        , p_game_ping_id); }
    void build_START_GAME       (uint version, Mode mode, const std::string& p_start_game_request_data)                                    { _PKB_IMPLEMENT_BUILD_CALL(START_GAME       , p_start_game_request_data); }
    void build_RESOURCES_REQUEST(uint version, Mode mode)                                                                                  { _PKB_IMPLEMENT_BUILD_CALL(RESOURCES_REQUEST,); }
    void build_GAME_CONFIG_OK   (uint version, Mode mode)                                                                                  { _PKB_IMPLEMENT_BUILD_CALL(GAME_CONFIG_OK   ,); }
    void build_INPUT_STATE      (uint version, Mode mode, uint64 p_client_time, uint p_changes, const Point2& p_input_pos, uint p_actions) { _PKB_IMPLEMENT_BUILD_CALL(INPUT_STATE      , p_client_time, p_changes, p_input_pos, p_actions); }

private:
    template <uint version, Mode mode> void _build_packet_CLIENT_HANDSHAKE ();
    template <uint version, Mode mode> void _build_packet_GAME_PING        (uint p_game_ping_id);
    template <uint version, Mode mode> void _build_packet_START_GAME       (const std::string& p_start_game_request_data);
    template <uint version, Mode mode> void _build_packet_RESOURCES_REQUEST();
    template <uint version, Mode mode> void _build_packet_GAME_CONFIG_OK   ();
    template <uint version, Mode mode> void _build_packet_INPUT_STATE      (uint64 p_client_time, uint p_changes, const Point2& p_input_pos, uint p_actions);
   
private:
    static PacketBuilder*   _singleton;

    CurrentBuild            _cb;
    
    static const uint MAX_VERSION_NUMBER = 1;
    std::unique_ptr<ImplBase>   _impl[MAX_VERSION_NUMBER][Mode::MaxNumModes];

};

