#pragma once

#include <sstream>
#include <string>
#include <vector>

#include "core/types.h"

#ifdef __linux__
#else
    //#define PKB_MEASURE_TIME
#endif

#ifdef PKB_MEASURE_TIME
    // Asume que la variable user esta definida.
    #define PKB_SEND_PACKET(token, ...) {                    \
        uint64_t get_ticks_usec();                           \
        const uint64 psp_build_begin_time = get_ticks_usec();\
        PacketBuilder* pkb = PacketBuilder::get_singleton(); \
        RTCHECK(pkb);                                        \
        _PKB_BUILD_PACKET(token, ##__VA_ARGS__);             \
        const uint64 psp_build_end_time = get_ticks_usec();  \
        PacketBuilder::Packet pk = pkb->get_packet();        \
        user.send_packet(pk.data, pk.size);                  \
        const uint64 psp_send_end_time = get_ticks_usec();   \
        pkb_tc_add_to_accum_time(psp_build_end_time - psp_build_begin_time, psp_send_end_time - psp_build_end_time); \
    }
#else
    // Asume que la variable user esta definida.
    #define PKB_SEND_PACKET(token, ...) {                    \
        PacketBuilder* pkb = PacketBuilder::get_singleton(); \
        RTCHECK(pkb);                                        \
        _PKB_BUILD_PACKET(token, ##__VA_ARGS__);             \
        PacketBuilder::Packet pk = pkb->get_packet();        \
        user.send_packet(pk.data, pk.size);                  \
    }
#endif

#ifdef PKB_MEASURE_TIME
    void pkb_tc_add_to_accum_time(uint64 built_us, uint64 send_us);
    void pkb_tc_clear_accum_time();
    void pkb_tc_get_accum_time(uint64& built_us, uint64& send_us);
#endif

// Detalles de implementacion
// [
#define _PKB_BUILD_PACKET(token, ...)                                    \
    const User::TransmissionConfig& tc = user.get_transmission_config(); \
    RTCHECK(tc.version);                                                 \
    pkb->build_##token (tc.version, tc.mode, ##__VA_ARGS__);

#define _PKB_IMPLEMENT_SELECT_VERSION(token, vers, ...)                                      \
    if (version == vers)                                                                     \
        if      (mode == Mode::Text)   _build_packet_##token <1, Mode::Text>(__VA_ARGS__);   \
        else if (mode == Mode::Binary) _build_packet_##token <1, Mode::Binary>(__VA_ARGS__);          

#define _PKB_IMPLEMENT_BUILD_CALL(token, ...)            \
    RTCHECK(version);                                    \
    _PKB_IMPLEMENT_SELECT_VERSION(token, 1, ##__VA_ARGS__)

namespace engine {

    struct VREntry;
    struct VRSnake;
    struct VRBubb;

    namespace simple {
        class View;
        class ViewRendererOutput;
        class GMap;
    }
}
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
        CurrentBuild() : o(NULL) {}
        void clear() { buffer.clear(); }

        std::vector<ubyte>     buffer;

        // Variables que son usadas por los paquetes VIEW_RESULTS, RANKING, RADAR.
        // [
        engine::simple::GMap* gmap;
        // ]

        // Variables que son usadas por el paquete VIEW_RESULTS.
        // [
        const engine::simple::ViewRendererOutput* o; // output results
        IDR rendered_view_id;        
        IDR player_id;
        const engine::VREntry* tank; // For sequence build.
        const engine::VREntry* chap; // For sequence build.
        const engine::VREntry* hut; // For sequence build.
        // ]
    };
}

class User;
class PlaySession;

class PacketBuilder
{
    using ImplBase = _namespace_packet_builder::PacketBuilderImplBase;

public:
    using Packet   = _namespace_packet_builder::Packet;
    using Mode = TransmissionMode::_;
    using CurrentBuild = _namespace_packet_builder::CurrentBuild;
    using ViewRendererOutput = engine::simple::ViewRendererOutput;
    using GMap = engine::simple::GMap;

public:
    static PacketBuilder* get_singleton() { return _singleton; }    

    PacketBuilder(); 
    virtual ~PacketBuilder();

    Packet get_packet() const { return Packet(_cb.buffer.data(), (uint)_cb.buffer.size()); }
    
    void reset() { _cb.clear(); }

    GMap* get_gmap() const { RTCHECK(_cb.gmap); return _cb.gmap; }

    void build_SERVER_HANDSHAKE ();
    //void build_GAME_PONG        (const ubyte* msg, uint msg_size);

    void build_RESOURCES_BEGIN  (uint version, Mode mode, uint max_resource_count)                          { _PKB_IMPLEMENT_BUILD_CALL(RESOURCES_BEGIN  , max_resource_count); }
    void build_RESOURCE         (uint version, Mode mode, const std::string& resource_path)                 { _PKB_IMPLEMENT_BUILD_CALL(RESOURCE         , resource_path); }
    void build_RESOURCES_END    (uint version, Mode mode)                                                   { _PKB_IMPLEMENT_BUILD_CALL(RESOURCES_END    ,); }
    void build_GAME_CONFIG      (uint version, Mode mode, IDR gmap_id)                                      { _PKB_IMPLEMENT_BUILD_CALL(GAME_CONFIG      , gmap_id); }
    void build_GAME_START_OK    (uint version, Mode mode)                                                   { _PKB_IMPLEMENT_BUILD_CALL(GAME_START_OK    ,); }
    void build_GAME_START_FAILED(uint version, Mode mode)                                                   { _PKB_IMPLEMENT_BUILD_CALL(GAME_START_FAILED,); }
    void build_GAME_FINISHED    (uint version, Mode mode)                                                   { _PKB_IMPLEMENT_BUILD_CALL(GAME_FINISHED    ,); }
    void build_VOTEMAP          (uint version, Mode mode, const std::vector<uint>& vote_map)                { _PKB_IMPLEMENT_BUILD_CALL(VOTEMAP          , vote_map); }
    void build_VIEW_RESULTS     (uint version, Mode mode, GMap* gmap, IDR view_id, const PlaySession& play_session, const ViewRendererOutput& output){ _PKB_IMPLEMENT_BUILD_CALL(VIEW_RESULTS, gmap, view_id, play_session, output); }
    void build_RANKING          (uint version, Mode mode, GMap* gmap, IDR view_id)                                  { _PKB_IMPLEMENT_BUILD_CALL(RANKING     , gmap, view_id); }
    void build_RADAR            (uint version, Mode mode, GMap* gmap)                                               { _PKB_IMPLEMENT_BUILD_CALL(RADAR       , gmap); }
    void build_GMAP             (uint version, Mode mode, GMap* gmap)                                               { _PKB_IMPLEMENT_BUILD_CALL(GMAP        , gmap); }

private:
    template <uint version, Mode mode> void _build_packet_RESOURCES_BEGIN  (uint max_resource_count);
    template <uint version, Mode mode> void _build_packet_RESOURCE         (const std::string& resource_path);
    template <uint version, Mode mode> void _build_packet_RESOURCES_END    ();
    template <uint version, Mode mode> void _build_packet_GAME_CONFIG      (IDR gmap_id);
    template <uint version, Mode mode> void _build_packet_GAME_START_OK    ();
    template <uint version, Mode mode> void _build_packet_GAME_START_FAILED();
    template <uint version, Mode mode> void _build_packet_GAME_FINISHED    ();
    template <uint version, Mode mode> void _build_packet_VOTEMAP          (const std::vector<uint>& vote_map);
    template <uint version, Mode mode> void _build_packet_VIEW_RESULTS     (GMap* gmap, IDR view_id, const PlaySession& play_session, const ViewRendererOutput& output);
    template <uint version, Mode mode> void _build_packet_RANKING          (GMap* gmap, IDR view_id);
    template <uint version, Mode mode> void _build_packet_RADAR            (GMap* gmap);
    template <uint version, Mode mode> void _build_packet_GMAP             (GMap* gmap);

private:
    
    template <uint version, Mode mode> void _build_TRACKER();

    template <uint version, Mode mode> void _build_PLAYER();
    template <uint version, Mode mode> void _build_PLAYERS();

    template <uint version, Mode mode> void _build_RACE();

    template <uint version, Mode mode> void _build_HUT();
    template <uint version, Mode mode> void _build_HUTS();

    template <uint version, Mode mode> void _build_TANK();
    template <uint version, Mode mode> void _build_TANKS();

    template <uint version, Mode mode> void _build_CHAP();
    template <uint version, Mode mode> void _build_CHAPS();

private:
    static PacketBuilder*   _singleton;

    CurrentBuild            _cb;
    
    static const uint MAX_VERSION_NUMBER = 1;
    std::unique_ptr<ImplBase>   _impl[MAX_VERSION_NUMBER][Mode::MaxNumModes];

};

