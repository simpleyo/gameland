#include "protocol.h"
#include "config/config.h"
#include "core/defs.h"
#include "core/utils.h"
#include "engine/simple/gmap_config.h"
#include "engine/simple/gmap_manager.h"
#include "engine/simple/ranking.h"
#include "engine/simple/radar.h"
#include "engine/simple/race.h"
#include "engine/simple/hut_manager.h"
#include "engine/simple/chap_manager.h"
#include "engine/simple/tank_manager.h"
#include "engine/simple/player_manager.h"
#include "engine/simple/view.h"
#include "engine/simple/view_manager.h"
#include "engine/simple/view_renderer.h"
#include "engine/simple/tracker_manager.h"
#include "engine/simple/time.h"
#include "engine/itracker.h"
#include "engine/iview.h"
#include "engine/irace.h"
#include "engine/iavatar.h"
#include "modules/main_server_client/resource_manager.h"
#include "modules/game_context/game_context.h"
#include "modules/game_context/game_session.h"
#include "modules/user/user_manager.h"
#include "packet_builder.h"

using Mode   = PacketBuilder::Mode;
using Output = engine::simple::ViewRendererOutput;

#define RADAR_INTEGRATE_IN_VIEW_RESULTS
#define GMAP_INTEGRATE_IN_VIEW_RESULTS

#define BUILD(x) _build_##x<version,mode>()

#define BUILD_TOKEN(x) bdr.build_token(_cb.buffer, Token::x)

#define BUILD_RAW_BYTES(x, num_bytes) bdr.build_bytes(_cb.buffer, x, num_bytes)
#define BUILD_RAW_BYTE(x) { const ubyte data[1] = { (ubyte)x }; BUILD_RAW_BYTES((char*)data, 1); }
#define _BUILD_BYTES(size_type, x, num_bytes) bdr.template build_sized_bytes<size_type>(_cb.buffer, x, (size_type)num_bytes)

#define BUILD_BYTES_8( x, num_bytes) _BUILD_BYTES(uint8_t , x, num_bytes)
#define BUILD_BYTES_16(x, num_bytes) _BUILD_BYTES(uint16_t, x, num_bytes)
#define BUILD_BYTES_32(x, num_bytes) _BUILD_BYTES(uint32_t, x, num_bytes)

#define BUILD_I8(x ) bdr.build_i8 (_cb.buffer, x)
#define BUILD_I16(x) bdr.build_i16(_cb.buffer, x)
#define BUILD_I32(x) bdr.build_i32(_cb.buffer, x)
#define BUILD_I64(x) bdr.build_i64(_cb.buffer, x)

#define BUILD_U8(x ) bdr.build_u8 (_cb.buffer, x)
#define BUILD_U16(x) bdr.build_u16(_cb.buffer, x)
#define BUILD_U32(x) bdr.build_u32(_cb.buffer, x)
#define BUILD_U64(x) bdr.build_u64(_cb.buffer, x)

#define BUILD_FLOAT(x)  bdr.build_f32(_cb.buffer, x)
#define BUILD_DOUBLE(x) bdr.build_f64(_cb.buffer, x)

#define _DEFINE_BUILDER(version, mode) _impl[version-1][Mode::mode].reset(new _namespace_packet_builder::PacketBuilderImpl<version, Mode::mode>(this));
#define DEFINE_BUILDERS(version) \
    _DEFINE_BUILDER(version, Text)       \
    _DEFINE_BUILDER(version, Binary)

#define DECLARE_BUILDER                                  \
    using Builder = _namespace_packet_builder::PacketBuilderImpl<version, mode>;     \
    using Token = typename Builder::Token;                        \
    Builder& bdr = *(_impl[version-1][mode]->as<Builder>());

#define CLEAR_BUILD \
    DECLARE_BUILDER \
    bdr.reset();

#ifdef PKB_MEASURE_TIME
    static uint64 pkb_tc_build_accum_time_us = 0;
    static uint64 pkb_tc_send_accum_time_us = 0;
    void pkb_tc_add_to_accum_time(uint64 build_us, uint64 send_us)
    {
        pkb_tc_build_accum_time_us += build_us;
        pkb_tc_send_accum_time_us += send_us;
    }
    void pkb_tc_clear_accum_time()
    {
        pkb_tc_build_accum_time_us = 0;
        pkb_tc_send_accum_time_us = 0;
    }
    void pkb_tc_get_accum_time(uint64& build_us, uint64& send_us)
    {
        build_us = pkb_tc_build_accum_time_us;
        send_us = pkb_tc_send_accum_time_us;
    }
#endif

namespace _namespace_packet_builder {

    class PacketBuilderImplBase
    {
        template<class T> struct item_return{ using Type = T; };

    public:
        PacketBuilderImplBase(PacketBuilder* instance) : _instance(instance) { RTCHECK(instance); }

        void reset() { _instance->reset(); }

        template<class T>
        typename item_return<T>::Type* as() { return static_cast<T*>(this); }

    private:
        // Las template clases derivadas de PacketBuilderImplBase deben definir estos metodos como funciones no virtuales.
        // Este interface esta solo como mera referencia.
        struct _interface {

            virtual void build_token(std::vector<ubyte>& p_buffer, uint p_token_id) = 0;

            virtual void build_sized_bytes(std::vector<ubyte>& p_buffer, const char* p_data, uint p_data_size) = 0;  // Template <size_type>
            virtual void build_bytes(std::vector<ubyte>& p_buffer, const char* p_data, uint p_data_size) = 0;
            
            virtual void build_i8 (std::vector<ubyte>& p_buffer, int8_t  v) = 0;
            virtual void build_i16(std::vector<ubyte>& p_buffer, int16_t v) = 0;
            virtual void build_i32(std::vector<ubyte>& p_buffer, int32_t v) = 0;
            virtual void build_i64(std::vector<ubyte>& p_buffer, int64_t v) = 0;
            
            virtual void build_u8 (std::vector<ubyte>& p_buffer, uint8_t  v) = 0;
            virtual void build_u16(std::vector<ubyte>& p_buffer, uint16_t v) = 0;
            virtual void build_u32(std::vector<ubyte>& p_buffer, uint32_t v) = 0;
            virtual void build_u64(std::vector<ubyte>& p_buffer, uint64_t v) = 0;
            
            virtual float  build_f32(std::vector<ubyte>& p_buffer, float  v) = 0;
            virtual double build_f64(std::vector<ubyte>& p_buffer, double v) = 0;
        };
        
    private:
        PacketBuilder* _instance;
    };

    template <uint version, Mode mode>
    class PacketBuilderImpl : public PacketBuilderImplBase
    {};
    
    template <uint version> struct Token {};

    template <> 
    struct Token<1> : public BuilderTokenV1 {};
            
    #define tokenV1_str BuilderTokenV1_str

    template <>
    class PacketBuilderImpl<1, Mode::Text> : public PacketBuilderImplBase
    {
    public:
        using Token = Token<1>;

    public:
        PacketBuilderImpl(PacketBuilder* instance) : PacketBuilderImplBase(instance) {}

        void build_token(std::vector<ubyte>& p_buffer, uint p_token_id);

        template <typename size_type>
        void build_sized_bytes(std::vector<ubyte>& p_buffer, const char* p_data, uint p_data_size);
        void build_bytes(std::vector<ubyte>& p_buffer, const char* p_data, uint p_data_size);

        void build_i8 (std::vector<ubyte>& p_buffer, int8_t  v) { _build_value<int8_t >(p_buffer, v); }
        void build_i16(std::vector<ubyte>& p_buffer, int16_t v) { _build_value<int16_t>(p_buffer, v); }
        void build_i32(std::vector<ubyte>& p_buffer, int32_t v) { _build_value<int32_t>(p_buffer, v); }
        void build_i64(std::vector<ubyte>& p_buffer, int64_t v) { _build_value<int64_t>(p_buffer, v); }

        void build_u8 (std::vector<ubyte>& p_buffer, uint8_t  v) { _build_value<uint8_t >(p_buffer, v); }
        void build_u16(std::vector<ubyte>& p_buffer, uint16_t v) { _build_value<uint16_t>(p_buffer, v); }
        void build_u32(std::vector<ubyte>& p_buffer, uint32_t v) { _build_value<uint32_t>(p_buffer, v); }
        void build_u64(std::vector<ubyte>& p_buffer, uint64_t v) { _build_value<uint64_t>(p_buffer, v); }

        void build_f32(std::vector<ubyte>& p_buffer, float  v)  { _build_value<float >(p_buffer, v); }
        void build_f64(std::vector<ubyte>& p_buffer, double v)  { _build_value<double>(p_buffer, v); }
    
    private:
        template <typename T> void _build_value(std::vector<ubyte>& p_buffer, T v);
    };

    void PacketBuilderImpl<1, Mode::Text>::build_token(std::vector<ubyte>& p_buffer, uint p_token_id)
    {
        RTCHECK(p_token_id < Token::MAX_TOKENS);
        const char* p_token = tokenV1_str[p_token_id];
        build_bytes(p_buffer, p_token, (uint)strlen(p_token));

        p_buffer.push_back(' ');    // Add space.
    }

    void PacketBuilderImpl<1, Mode::Text>::build_bytes(std::vector<ubyte>& p_buffer, const char* p_data, uint p_data_size)
    {
        p_buffer.insert(p_buffer.end(), p_data, p_data + p_data_size);
    }

    template <typename size_type>
    void PacketBuilderImpl<1, Mode::Text>::build_sized_bytes(std::vector<ubyte>& p_buffer, const char* p_data, uint p_data_size)
    {
        _build_value<size_type>(p_buffer, p_data_size);
        build_bytes(p_buffer, p_data, p_data_size);
        p_buffer.push_back(' ');    // Add space.
    }

    template <typename T>
    void PacketBuilderImpl<1, Mode::Text>::_build_value(std::vector<ubyte>& p_buffer, T v)
    {
        std::string s = std::to_string(v);
        build_bytes(p_buffer, s.c_str(), (uint)s.length());
        p_buffer.push_back(' ');    // Add space.
    }
    
    template <>
    class PacketBuilderImpl<1, Mode::Binary> : public PacketBuilderImplBase
    {
    public:
        using Token = Token<1>;

    public:
        PacketBuilderImpl(PacketBuilder* instance) : PacketBuilderImplBase(instance) {}

        void build_token(std::vector<ubyte>& p_buffer, uint p_token_id);

        void build_bytes(std::vector<ubyte>& p_buffer, const char* p_data, uint p_data_size);
        template <typename size_type>
        void build_sized_bytes(std::vector<ubyte>& p_buffer, const char* p_data, uint p_data_size);

        void build_i8 (std::vector<ubyte>& p_buffer, int8_t  v) { _build_value<int8_t >(p_buffer, v); }
        void build_i16(std::vector<ubyte>& p_buffer, int16_t v) { _build_value<int16_t>(p_buffer, v); }
        void build_i32(std::vector<ubyte>& p_buffer, int32_t v) { _build_value<int32_t>(p_buffer, v); }
        void build_i64(std::vector<ubyte>& p_buffer, int64_t v) { _build_value<int64_t>(p_buffer, v); }

        void build_u8 (std::vector<ubyte>& p_buffer, uint8_t  v) { _build_value<uint8_t >(p_buffer, v); }
        void build_u16(std::vector<ubyte>& p_buffer, uint16_t v) { _build_value<uint16_t>(p_buffer, v); }
        void build_u32(std::vector<ubyte>& p_buffer, uint32_t v) { _build_value<uint32_t>(p_buffer, v); }
        void build_u64(std::vector<ubyte>& p_buffer, uint64_t v) { _build_value<uint64_t>(p_buffer, v); }

        void build_f32(std::vector<ubyte>& p_buffer, float  v)  { _build_value<float >(p_buffer, v); }
        void build_f64(std::vector<ubyte>& p_buffer, double v)  { _build_value<double>(p_buffer, v); }
    
    private:
        template <typename T> void _build_value(std::vector<ubyte>& p_buffer, T v);
    };

    void PacketBuilderImpl<1, Mode::Binary>::build_token(std::vector<ubyte>& p_buffer, uint p_token_id)
    {
        RTCHECK(p_token_id < Token::MAX_TOKENS);        
        build_u8(p_buffer, p_token_id);
    }

    void PacketBuilderImpl<1, Mode::Binary>::build_bytes(std::vector<ubyte>& p_buffer, const char* p_data, uint p_data_size)
    {
        p_buffer.insert(p_buffer.end(), p_data, p_data + p_data_size);
    }

    template <typename size_type>
    void PacketBuilderImpl<1, Mode::Binary>::build_sized_bytes(std::vector<ubyte>& p_buffer, const char* p_data, uint p_data_size)
    {
        _build_value<size_type>(p_buffer, p_data_size);
        build_bytes(p_buffer, p_data, p_data_size);
    }

    template <typename T>
    void PacketBuilderImpl<1, Mode::Binary>::_build_value(std::vector<ubyte>& p_buffer, T v)
    {
        const T* ptr = &v;
        build_bytes(p_buffer, (char*)ptr, sizeof(T));        
    }
}

using Mode         = PacketBuilder::Mode;
using CurrentBuild = PacketBuilder::CurrentBuild;

PacketBuilder* PacketBuilder::_singleton = NULL;

PacketBuilder::PacketBuilder()
{    
    RTCHECK(!_singleton);
    _singleton = this;

    DEFINE_BUILDERS(1);   // Builders version 1
}

PacketBuilder::~PacketBuilder()
{
    RTCHECK(_singleton);
    _singleton = NULL;
}

void PacketBuilder::build_SERVER_HANDSHAKE()
{
    reset();
    RTCHECK(_cb.buffer.empty());

    _cb.buffer.push_back(0);    // Flags del mensaje.

    const char* magic = HANDSHAKE_MAGIC_STRING;
    const uint magic_size = (uint)strlen(magic);
    RTCHECK(magic_size == 4);
    for (uint i=0; i<magic_size; ++i)
    {
        _cb.buffer.push_back(magic[i]);
    }

    _cb.buffer.push_back(0);
    _cb.buffer.push_back(0);
    _cb.buffer.push_back(0);
    _cb.buffer.push_back(0);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_RESOURCES_BEGIN(uint max_resource_count)
{
    CLEAR_BUILD;
    BUILD_U8(0);    // Flags del mensaje.
    BUILD_TOKEN(RESOURCES_BEGIN);
    BUILD_U32(max_resource_count);
    BUILD_TOKEN(END);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_RESOURCE(const std::string& resource_path)
{
    CLEAR_BUILD;
    BUILD_RAW_BYTE((((mode == Mode::Binary) && (!SRVCONFIG.DISABLE_PACKETS_COMPRESSION)) ? PROTOCOL_MESSAGE_FLAGS(1)::MSG_COMPRESSED : 0)) // Flags del mensaje.
    BUILD_TOKEN(RESOURCE);
    
    BUILD_BYTES_32(resource_path.c_str(), (uint)resource_path.length());

    const std::string str = GameContext::get_game_resource(resource_path);
    //const std::string str = GameContext::get_game_resourceLOAD_GAME_RESOURCE(resource_path);

    TRACE("Build packet: RESOURCE(" << resource_path << ") Size: " << str.length());

    BUILD_BYTES_32(str.c_str(), str.length());

    BUILD_TOKEN(END);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_RESOURCES_END()
{
    CLEAR_BUILD;
    BUILD_U8(0);    // Flags del mensaje.
    BUILD_TOKEN(RESOURCES_END);
    BUILD_TOKEN(END);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_GAME_CONFIG(IDR gmap_id)
{
    GET_SINGLETON(engine::simple::GMapManager, mm);
    RTCHECK(mm->contains_gmap(gmap_id));
    
    _cb.gmap = &(mm->get_gmap(gmap_id));
        
    CLEAR_BUILD;
    BUILD_RAW_BYTE((((mode == Mode::Binary) && (!SRVCONFIG.DISABLE_PACKETS_COMPRESSION)) ? PROTOCOL_MESSAGE_FLAGS(1)::MSG_COMPRESSED : 0)) // Flags del mensaje.
    BUILD_TOKEN(GAME_CONFIG);

    GET_SINGLETON(GameContext, gc);
    GameSession* gs = gc->get_room(_cb.gmap->get_room_id()).get_game_session();
    BUILD_U16(gs->get_room().get_room_id());
    const std::string game_session_config = gs->get_client_config(); //game->build_game_session_config(get_gmap()->get_game_session_id());
    BUILD_BYTES_32(game_session_config.c_str(), (uint)game_session_config.size());

    BUILD_TOKEN(END);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_GAME_START_OK()
{
    CLEAR_BUILD;
    BUILD_U8(0);    // Flags del mensaje.
    BUILD_TOKEN(GAME_START_OK);
    BUILD_TOKEN(END);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_GAME_START_FAILED()
{
    CLEAR_BUILD;
    BUILD_U8(0);    // Flags del mensaje.
    BUILD_TOKEN(GAME_START_FAILED);
    BUILD_TOKEN(END);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_GAME_FINISHED()
{
    CLEAR_BUILD;
    BUILD_U8(0);    // Flags del mensaje.
    BUILD_TOKEN(GAME_FINISHED);
    BUILD_TOKEN(END);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_VOTEMAP(const std::vector<uint>& vote_map)
{
    CLEAR_BUILD;
    BUILD_U8(0);    // Flags del mensaje.
    BUILD_TOKEN(VOTEMAP);
    BUILD_U8((uint)vote_map.size());
    const uint ei = (uint)vote_map.size();
    for (uint i = 0; i < ei; ++i)
    {
        BUILD_U8(vote_map[i]);
    }
    BUILD_TOKEN(END);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_RANKING(GMap* gmap, IDR view_id)
{
    using namespace engine;
    using namespace engine::simple;

    RTCHECK(gmap);
    _cb.gmap = gmap;

    GET_GMAP_COMPONENT(PlayerManager,pm );
    GET_GMAP_COMPONENT(Ranking, ranking);

    CLEAR_BUILD;
    BUILD_RAW_BYTE((((mode == Mode::Binary) && (!SRVCONFIG.DISABLE_PACKETS_COMPRESSION)) ? PROTOCOL_MESSAGE_FLAGS(1)::MSG_COMPRESSED : 0)) // Flags del mensaje.
    BUILD_TOKEN(RANKING);

    IDR main_player_id;
    {
        GET_GMAP_COMPONENT(ViewManager, vm);
        const View& view = vm->get_view(view_id);
        main_player_id = view.get_player().get_id();
    }
        
    const uint top_list_size = (ranking->get_brute_force_ranking_list().size() < MAPCONFIG.RANKING_MAX_TOP_LIST_SIZE) ? 
        uint(ranking->get_brute_force_ranking_list().size()) : MAPCONFIG.RANKING_MAX_TOP_LIST_SIZE;

    const std::vector<Ranking::Entry>& ranking_list = ranking->get_brute_force_ranking_list();

    BUILD_U16(pm->get_player_count());
    BUILD_U8(top_list_size);

    for (uint i=0; i<top_list_size; ++i)
    {
        const Ranking::Entry& entry = ranking_list[i]; //ranking->get_entry(i);
        const IDR player_id = entry.player.id();
        BUILD_U16(player_id); // Se asume que player_id es valido.

        BUILD_U32(entry.score);
    }

    if (main_player_id.is_valid())
    {
        const std::vector<uint>& player_indices = ranking->get_brute_force_ranking_player_index();

        const uint index = player_indices[main_player_id];

        if (index != Ranking::INVALID_INDEX)
        {
            const Ranking::Entry& entry = ranking_list[index];

            BUILD_TOKEN(CURRENT);

            BUILD_U16(index);

            if (index >= top_list_size)
            {
                const IDR player_id = entry.player.id();
                RTCHECK(player_id == main_player_id);                    
                BUILD_U16(player_id); // Se asume que player_id es valido.

                BUILD_U32(entry.score);
            }
        }
    }

    BUILD_TOKEN(END);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_RADAR(GMap* gmap)
{
    using namespace engine;
    using namespace engine::simple;

    RTCHECK(gmap);
    _cb.gmap = gmap;

    GET_GMAP_COMPONENT(Radar, radar);

#ifdef RADAR_INTEGRATE_IN_VIEW_RESULTS
    // FIXME: El paquete RADAR se deberia construir en Context::on_render_begined() y se deberia enviar aqui.
    if (radar->get_radar_list_changed())
    {

    DECLARE_BUILDER;
#else
    CLEAR_BUILD;
    BUILD_RAW_BYTE((((mode == Mode::Binary) && (!SRVCONFIG.DISABLE_PACKETS_COMPRESSION)) ? PROTOCOL_MESSAGE_FLAGS(1)::MSG_COMPRESSED : 0)) // Flags del mensaje.
#endif
    BUILD_TOKEN(RADAR);

    const uint entry_count = radar->get_entry_count();
    BUILD_U16(entry_count);

    GET_GMAP_COMPONENT(ViewManager, vm);
    IDR main_player_id;
    {
        const View& view = vm->get_view(_cb.rendered_view_id);
        main_player_id = view.get_player().get_id();
    }

    uint players_count = 0;

    bool main_player_found = false;
    for (uint i=0; i<entry_count; ++i)
    {
        const Radar::Entry& entry = radar->get_entry(i);
        const IDR player_id = entry.player.id();
        if (player_id == main_player_id)
        {
            // No se envia el identificador de player porque no es necesario para dibujar el radar.
            //BUILD_U16(player_id); // Se asume que player_id es valido.
            BUILD_U8(entry.position.x());
            BUILD_U8(entry.position.y());
            ++players_count;

            main_player_found = true; // Para comprobrar que se ha encontrado al main_player en la lista de entrys del radar.
            break;
        }
    }

    //RTCHECK(main_player_found || (entry_count == 0));

    for (uint i=0; i<entry_count; ++i)
    {
        const Radar::Entry& entry = radar->get_entry(i);
        const IDR player_id = entry.player.id();
        
        if (player_id != main_player_id)
        {
            // No se envia el identificador de player porque no es necesario para dibujar el radar.
            //BUILD_U16(player_id); // Se asume que player_id es valido.
            BUILD_U8(entry.position.x());
            BUILD_U8(entry.position.y());
            ++players_count;
        }
    }

    RTCHECK(players_count == entry_count);
    
#ifdef RADAR_INTEGRATE_IN_VIEW_RESULTS
    }
#else
    BUILD_TOKEN(END);
#endif
    //TRACE("RADAR packet size: " << _cb.buffer.size());
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_GMAP(GMap* gmap)
{
    using namespace engine;
    using namespace engine::simple;

    RTCHECK(gmap);
    _cb.gmap = gmap;

#ifdef GMAP_INTEGRATE_IN_VIEW_RESULTS
    DECLARE_BUILDER;
    if (gmap->get_changes() != 0)
    {
        if (gmap->get_play_status() != GMapPlayStatus::PlayToBeFinished)
        {
#else
    CLEAR_BUILD;
    BUILD_RAW_BYTE(0) // Flags del mensaje.
#endif
    BUILD_TOKEN(GMAP);

    //TRACE("Sending GMAP packet...")

    const ubyte changes = gmap->get_changes();
    RTCHECK(changes != 0);
    BUILD_U8(changes);

    if (changes & GMapChange::PlayStatusChanged)
    {
        BUILD_U8(ubyte(gmap->get_play_status()));
    }

#ifdef GMAP_INTEGRATE_IN_VIEW_RESULTS
        }
    }
#else
    BUILD_TOKEN(END);
#endif
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_VIEW_RESULTS(GMap* gmap, IDR view_id, const PlaySession& play_session, const engine::simple::ViewRendererOutput& view_results)
{    
    CLEAR_BUILD;
    BUILD_RAW_BYTE((((mode == Mode::Binary) && (!SRVCONFIG.DISABLE_PACKETS_COMPRESSION)) ? PROTOCOL_MESSAGE_FLAGS(1)::MSG_COMPRESSED : 0)) // Flags del mensaje.

    RTCHECK(gmap);
    _cb.gmap = gmap;

    _cb.o = &view_results;
    RTCHECK(view_id.is_valid());
    _cb.rendered_view_id = view_id;

    BUILD_TOKEN(VIEW_RESULTS);

    const uint64_t engine_time = _cb.o->engine_time;
    BUILD_U64(engine_time);
        
    // Build client_time and server_response_time
    {
        const uint64 client_time = play_session.get_next_client_time_after_input_state_readed_by_view();
        const uint server_response_time = uint(get_ticks_usec() - play_session.get_next_client_time_after_input_state_readed_by_view_update_time());

        BUILD_U64(client_time);
        BUILD_U32(server_response_time);
        //TRACE("server_response_time: " << server_response_time);
    }

    BUILD(PLAYERS);
    BUILD(RACE);
    BUILD(TRACKER);
    //if (!_cb.o->output_huts.empty())
    //    BUILD(HUTS);
    BUILD(TANKS);
    if (!_cb.o->output_chaps.empty())
        BUILD(CHAPS);

#ifdef RADAR_INTEGRATE_IN_VIEW_RESULTS
    _build_packet_RADAR<version, mode>(gmap);
#endif

#ifdef GMAP_INTEGRATE_IN_VIEW_RESULTS
    _build_packet_GMAP<version, mode>(gmap);
#endif

    BUILD_TOKEN(END);
}

template <uint version, Mode mode> 
void PacketBuilder::_build_TRACKER()
{
    using namespace engine;
    using namespace engine::simple;
    GET_GMAP_COMPONENT(TrackerManager, tm);

    DECLARE_BUILDER

    BUILD_TOKEN(TRACKER);
        
    const engine::VREntry& tracker_entry = _cb.o->tracker;
    const ViewResult tracker_result = tracker_entry.result;
    const Tracker& tracker = tm->get_tracker(tracker_entry.entity_id);
        
    BUILD_U8((ubyte)tracker_result);

    using Result = ViewResult;

    if (tracker_result != Result::None)
    {
        if (tracker_result != Result::Exit)
        {
            using PC = TrackerChange;

            const uint changes = tracker.get_changes();
            
            BUILD_U8(changes);

            if ((changes & PC::PositionChanged) || (tracker_result == Result::Enter))
            {
                BUILD_FLOAT(tracker.get_position().x);
                BUILD_FLOAT(tracker.get_position().y);
            }

            if ((changes & PC::RadiusChanged) || (tracker_result == Result::Enter))
            {
                BUILD_FLOAT(tracker.get_radius().x);
                BUILD_FLOAT(tracker.get_radius().y);
            }

            if ((changes & PC::TrackedAvatarChanged) || (tracker_result == Result::Enter))
            {
                AvatarRef avatar_ref;
                {
                    Avatar* tracked_avatar = tracker.get_tracked_avatar();
                    if (tracked_avatar)
                        avatar_ref = tracked_avatar->get_avatar_ref();
                }

                BUILD_U8((uint)avatar_ref.avatar_type);
                const IDR target_avatar_id = avatar_ref.avatar_id;
                BUILD_U16(target_avatar_id.is_valid() ? uint(target_avatar_id) : USHRT_MAX);
            }
        }
    }    
}

template <uint version, Mode mode>
void PacketBuilder::_build_PLAYER()
{
    using namespace engine;
    using namespace engine::simple;
    GET_GMAP_COMPONENT(ViewManager, vm);
    GET_GMAP_COMPONENT(PlayerManager, am);
    
    DECLARE_BUILDER

    RTCHECK(_cb.player_id.is_valid());
    
    const IDR player_id = _cb.player_id;
    const Player& player = am->get_player(player_id);
    
    BUILD_TOKEN(PLAYER);
    // ATENCION: Se esta asumiendo que el player.player_type = Avatar
    BUILD_U16(player_id); // Se asume que player_id es valido.
        
    IDR main_player_id;
    {
        const View& view = vm->get_view(_cb.rendered_view_id);
        main_player_id = view.get_player().get_id();
    }

    // Aqui se indica si es el main player. El cliente, con esta informacion, podra saber cual es el main avatar.
    // El target avatar del tracker no tiene por que ser el main avatar.
    // Por ejemplo, el main avatar puede ser un spectator y entonces el target avatar del tracker sera distinto del main avatar.
    const bool is_main_player = (player_id == main_player_id);
    BUILD_U8(is_main_player ? 1 : 0);   

    const Player::UserData& aud = player.get_user_data();

    const Avatar* avatar = player.get_avatar();
    AvatarRef avatar_ref;
    if (avatar) avatar_ref = avatar->get_avatar_ref();
    BUILD_U8((uint)avatar_ref.avatar_type);
    if (avatar_ref.avatar_type != AvatarType::None)
        BUILD_U16(avatar_ref.avatar_id); // Se asume que avatar_id es valido.
    BUILD_U8(aud.skin_id);
    BUILD_U8(aud.color_id);
    BUILD_U16(aud.flag_id);
    if (avatar_ref.avatar_type == AvatarType::Tank)
    {
        const Tank* tank = (Tank*)(avatar);
        const Size2& radius = tank->get_radius();
        BUILD_U8(ubyte(radius.x));
        BUILD_U8(ubyte(radius.y));
    }
    BUILD_BYTES_8(aud.name.str(), (ubyte)aud.name.length());
}

template <uint version, Mode mode>
void PacketBuilder::_build_PLAYERS()
{
    using namespace engine;

    DECLARE_BUILDER

    BUILD_TOKEN(PLAYERS);
    
    for (IDR player_id : _cb.o->output_players)
    {
        _cb.player_id = player_id;
        BUILD(PLAYER);
    }
}

template <uint version, Mode mode>
void PacketBuilder::_build_RACE()
{
    using namespace engine;
    using namespace engine::simple;
    
    GET_GMAP_COMPONENT(Race, race);

    GET_SINGLETON(Time, time);
    const float engine_time = float(time->get_current_time());

    IDR main_player_id;
    {
        GET_GMAP_COMPONENT(ViewManager, vm);
        const View& view = vm->get_view(_cb.rendered_view_id);
        main_player_id = view.get_player().get_id();
    }

    RTCHECK(race->contains_competitor(main_player_id));

    if (_cb.o->synchronization_lost)
    {
        //TRACE("RACE SYNCHRONIZATION LOST");

        DECLARE_BUILDER

        BUILD_TOKEN(RACE);
    
        // Envia eventos de carrera (son comunes a todos los players).
        {
            BUILD_U8(0);
        }

        // Envia eventos del main player.
        {
            BUILD_U8(1);
            BUILD_U8(RaceEvent::SynchronizationLost);
            BUILD_U8(race->get_status());
            BUILD_FLOAT(engine_time - race->get_race_start_time());
            BUILD_FLOAT(engine_time - race->get_countdown_start_time());            
            BUILD_U16(race->get_competitor_count());
            BUILD_U8(race->get_competitor(main_player_id).lap_count);
            BUILD_U8(race->get_competitor_finished_count());
            BUILD_U8(race->get_competitor(main_player_id).race_position);
        }
    }
    else if ((!race->get_global_events().empty()) || 
             (race->get_competitor(main_player_id).changes != 0))
    {
        DECLARE_BUILDER

        BUILD_TOKEN(RACE);

        // Envia eventos de carrera (son comunes a todos los players).
        {
            //RTCHECK(!race->get_events().empty());
            BUILD_U8(ubyte(race->get_global_events().size()));

            for (const Race::GlobalEvent& ev : race->get_global_events())
            {        
                if (ev.event_id == RaceEvent::StatusChanged)
                {
                    BUILD_U8(ev.event_id);
                    BUILD_U8(ev.race_status);
                }
                else if (ev.event_id == RaceEvent::CompetitorCountChanged)
                {
                    BUILD_U8(ev.event_id);
                    BUILD_U16(race->get_competitor_count());
                }
                else if (ev.event_id == RaceEvent::RaceFinished)
                {
                    BUILD_U8(ev.event_id);
                    //BUILD_U8(ev.player_id);
                }
                else if (ev.event_id == RaceEvent::CompetitorFinished)
                {
                    BUILD_U8(ev.event_id);
                    //BUILD_U8(ev.player_id);
                    BUILD_FLOAT(ev.race_final_time);
                }
                else if (ev.event_id == RaceEvent::RankingChanged)
                {
                    BUILD_U8(ev.event_id);
                    const std::vector<IDR>& ranking = race->get_ranking();
                    const uint ei = (uint)ranking.size();
                    BUILD_U8(ei);
                    for (uint i=0; i<ei; ++i)
                    {
                        const IDR player_id = ranking[i];
                        if (player_id.is_valid())
                            BUILD_U8(player_id);
                        else
                            BUILD_U8(IDR());
                    }
                }
            }
        }

        // Envia eventos del main player.
        {            
            const Race::Competitor& pd = race->get_competitor(main_player_id);

            if (pd.changes)
            {
                BUILD_U8(1);
                BUILD_U8(RaceEvent::CompetitorChanged);
                BUILD_U8(pd.changes);

                if (pd.changes & RaceCompetitorChange::Added)
                {
                    BUILD_U8(race->get_status());
                    BUILD_FLOAT(engine_time - race->get_race_start_time());
                    BUILD_FLOAT(engine_time - race->get_countdown_start_time());            
                    BUILD_U8(race->get_competitor(main_player_id).lap_count);
                    BUILD_U8(race->get_competitor_finished_count());
                }                
                else 
                {
                    if (pd.changes & RaceCompetitorChange::LapCountChanged)
                    {
                        //TRACE("Construye LapCountChanged para player: " << main_player_id);
                        BUILD_U8(race->get_competitor(main_player_id).lap_count);
                        BUILD_FLOAT(race->get_competitor(main_player_id).lap_time);
                    }                    

                    if (pd.changes & RaceCompetitorChange::RacePositionChanged)
                    {
                        BUILD_U16(race->get_competitor(main_player_id).race_position);
                    }                    

                    if (pd.changes & RaceCompetitorChange::RaceCompleted)
                    {
                        BUILD_FLOAT(race->get_competitor(main_player_id).race_final_time);
                    }                    
                }

                race->clear_player_data_changes(main_player_id);
            }
            else
            {
                BUILD_U8(0);
            }
        }
    }
}

template <uint version, Mode mode>
void PacketBuilder::_build_HUT()
{
    using namespace engine;
    using namespace engine::simple;
    GET_GMAP_COMPONENT(HutManager, sm);
    
    DECLARE_BUILDER
    
    RTCHECK(_cb.hut);
    const VREntry& entry = *_cb.hut;
    const ViewResult result = entry.result;
    const Hut& hut = sm->get_hut(entry.entity_id);

    BUILD_TOKEN(HUT);
    BUILD_U8(hut.get_id()); // Se asume que hut_id es valido.

    using Result = ViewResult;

    BUILD_U8((ubyte)result);
    RTCHECK(result != Result::None);

    if (result != Result::Exit)
    {
        using CT = HutChange; // Change type

        if (result == Result::Enter)
        {
            BUILD_U16(hut.get_paint_instance_id());
        }

        //BUILD_U8(hut.get_changes());  // Los cambios se envian siempre porque hut head tambien depende de ellos.

        const uint hut_changes = hut.get_changes();

        if ((hut.has_change(CT::CountChanged)) || 
            (result == Result::Enter))
        {
            BUILD_U8(hut.get_count());
        }  
    }
}

template <uint version, Mode mode>
void PacketBuilder::_build_HUTS()
{
    using namespace engine;
    using namespace engine::simple;

    DECLARE_BUILDER

    BUILD_TOKEN(HUTS);

    for (const VREntry& entry : _cb.o->output_huts)
    {
        _cb.hut = &entry;
        BUILD(HUT);
    }
}

template <uint version, Mode mode>
void PacketBuilder::_build_CHAP()
{
    using namespace engine;
    using namespace engine::simple;
    GET_GMAP_COMPONENT(ChapManager, sm);
    
    DECLARE_BUILDER
    
    RTCHECK(_cb.chap);
    const VREntry& entry = *_cb.chap;
    const ViewResult result = entry.result;
    const Chap& chap = sm->get_chap(entry.entity_id);

    BUILD_TOKEN(CHAP);
    BUILD_U8(chap.get_id()); // Se asume que chap_id es valido.

    using Result = ViewResult;

    BUILD_U8((ubyte)result);
    RTCHECK(result != Result::None);

    if (result != Result::Exit)
    {
        using CT = ChapChange; // Change type

        if (result == Result::Enter)
        {
        }

        BUILD_U8(chap.get_changes());  // Los cambios se envian siempre porque chap head tambien depende de ellos.

        const uint chap_changes = chap.get_changes();

        if ((chap.has_change(CT::PositionChanged)) || 
            (result == Result::Enter))
        {
            
            const IntPoint& btcp = _cb.o->out_chap_tracker_cells_rect.position();

            const uint cell_size = sm->get_cell_size();                    
            const int MAX_RV_COORD = 32767;

            if (cell_size <= 1024)
            {
                const int x = MAX(MIN(int((chap.get_position().x - (btcp.x() * cell_size)) * 10), MAX_RV_COORD), -MAX_RV_COORD);
                const int y = MAX(MIN(int((chap.get_position().y - (btcp.y() * cell_size)) * 10), MAX_RV_COORD), -MAX_RV_COORD);

                // Envia la posicion, en decimas de pixel, relativa al punto topleft de las celdas que define el tracker en ChapManager.
                BUILD_I16(x);
                BUILD_I16(y);
            }
            else
            {
                // ATENCION: Si el tamaño de la celda es mayor de 1024 pixeles entonces se envian pixeles, en vez
                // de decimas de pixel, ya que la resolucion no es suficiente para esos tamaños de celda.

                const int x = MAX(MIN(int((chap.get_position().x - (btcp.x() * cell_size))), MAX_RV_COORD), -MAX_RV_COORD);
                const int y = MAX(MIN(int((chap.get_position().y - (btcp.y() * cell_size))), MAX_RV_COORD), -MAX_RV_COORD);

                // Envia la posicion, en pixeles, relativa al punto topleft de las celdas que define el tracker en ChapManager.
                BUILD_I16(x);
                BUILD_I16(y);
            }
            //TRACE("Pos: " << x << ", " << y);
        }  

        if ((chap.has_change(CT::OrientationChanged)) ||
            (result == Result::Enter))
        {
            BUILD_U16(ushort((chap.get_orientation() / (2*Math_PI)) * 65535.f));
        }
    }
}

template <uint version, Mode mode>
void PacketBuilder::_build_CHAPS()
{
    using namespace engine;
    using namespace engine::simple;

    // Check para las coordenadas de posicion que se pueden enviar al cliente.
    // Como se envian en int16, como decimas de pixel, el maximo sera 32767 y el minimo -32768
    // que se corresponden con las coordenada 3276.7 y -3276.8
    {
        const IntPoint& btcs = _cb.o->out_chap_tracker_cells_rect.size();
        RTCHECK(btcs.x() <= 3276.7f);
        RTCHECK(btcs.y() <= 3276.7f);
    }

    DECLARE_BUILDER

    BUILD_TOKEN(CHAPS);

    const IntPoint& chap_tracker_cells_position = _cb.o->out_chap_tracker_cells_rect.position();
    const IntPoint& chap_tracker_cells_size     = _cb.o->out_chap_tracker_cells_rect.size();
    BUILD_U16(chap_tracker_cells_position.x());
    BUILD_U16(chap_tracker_cells_position.y());
    BUILD_U16(chap_tracker_cells_size.x());
    BUILD_U16(chap_tracker_cells_size.y());

    for (const VREntry& entry : _cb.o->output_chaps)
    {
        _cb.chap = &entry;
        BUILD(CHAP);
    }
}

template <uint version, Mode mode>
void PacketBuilder::_build_TANK()
{
    using namespace engine;
    using namespace engine::simple;
    GET_GMAP_COMPONENT(TankManager, sm);
    
    DECLARE_BUILDER
    
    RTCHECK(_cb.tank);
    const VREntry& entry = *_cb.tank;
    const ViewResult result = entry.result;
    const Tank& tank = sm->get_tank(entry.entity_id);

    BUILD_TOKEN(TANK);
    BUILD_U8(tank.get_id()); // Se asume que tank_id es valido.

    using Result = ViewResult;

    BUILD_U8((ubyte)result);
    RTCHECK(result != Result::None);

    if (result != Result::Exit)
    {
        using CT = TankChange; // Change type

        if (result == Result::Enter)
        {
        }

        BUILD_U8(tank.get_changes());  // Los cambios se envian siempre porque tank head tambien depende de ellos.

        const uint tank_changes = tank.get_changes();

        if ((tank.has_change(CT::PositionChanged)) || 
            (result == Result::Enter))
        {
            
            const IntPoint& btcp = _cb.o->out_tank_tracker_cells_rect.position();

            const uint cell_size = sm->get_cell_size();                    
            const int MAX_RV_COORD = 32767;

            const int x = MAX(MIN(int((tank.get_position().x - (btcp.x() * cell_size)) * 10), MAX_RV_COORD), -MAX_RV_COORD);
            const int y = MAX(MIN(int((tank.get_position().y - (btcp.y() * cell_size)) * 10), MAX_RV_COORD), -MAX_RV_COORD);
                                                                                            
            BUILD_I16(x);  // Envia la posicion, en decimas de pixel, relativa al punto topleft de las celdas que define el tracker en TankManager.
            BUILD_I16(y);
        }  

        if ((tank.has_change(CT::OrientationChanged)) ||
            (result == Result::Enter))
        {
            BUILD_U16(ushort((tank.get_orientation() / (2*Math_PI)) * 65535.f));
        }

        if ((tank.has_change(CT::StateChanged)) ||
            (result == Result::Enter))
        {
            BUILD_U8(tank.get_state());

            if (tank.get_state() == TankState::Fall)
            {
                BUILD_U8(tank.get_fall_steps_end());
                BUILD_U8(tank.get_fall_steps());
                BUILD_U8(tank.get_fall_offset_steps());
            }
        }

        if ((tank.has_change(CT::ModeFlagsChanged)) ||
            (result == Result::Enter))
        {
            BUILD_U8(tank.get_mode_flags());

            if (tank.get_mode_flags() & TankModeFlag::Jumping)
            {
                BUILD_U8(tank.get_jump_steps_end());
                BUILD_U8(tank.get_jump_steps());
            }
            else if (tank.get_mode_flags() & TankModeFlag::Landing)
            {
                BUILD_U8(tank.get_land_steps_end());
                BUILD_U8(tank.get_land_steps());
            }
        }

        if ((tank.has_change(CT::NitroLevelChanged)) ||
            (result == Result::Enter))
        {
            BUILD_U8(tank.get_nitro_level());
        }

        //if ((tank.has_change(CT::JumpChanged)) ||
        //    (result == Result::Enter))
        //{
        //    RTCHECK(tank.get_jump_steps_end() < 256);
        //    RTCHECK(tank.get_jump_steps() <= tank.get_jump_steps_end());

        //    BUILD_U8(tank.get_jump_steps_end());
        //    BUILD_U8(tank.get_jump_steps());
        //}

        //if ((tank.has_change(CT::FallChanged)) ||
        //    (result == Result::Enter))
        //{
        //    BUILD_U8(tank.get_fall_steps());
        //}
    }
}

template <uint version, Mode mode>
void PacketBuilder::_build_TANKS()
{
    using namespace engine;
    using namespace engine::simple;

    // Check para las coordenadas de posicion que se pueden enviar al cliente.
    // Como se envian en int16, como decimas de pixel, el maximo sera 32767 y el minimo -32768
    // que se corresponden con las coordenada 3276.7 y -3276.8
    {
        const IntPoint& btcs = _cb.o->out_tank_tracker_cells_rect.size();
        RTCHECK(btcs.x() <= 3276.7f);
        RTCHECK(btcs.y() <= 3276.7f);
    }

    DECLARE_BUILDER

    BUILD_TOKEN(TANKS);

    const IntPoint& tank_tracker_cells_position = _cb.o->out_tank_tracker_cells_rect.position();
    const IntPoint& tank_tracker_cells_size     = _cb.o->out_tank_tracker_cells_rect.size();
    BUILD_U16(tank_tracker_cells_position.x());
    BUILD_U16(tank_tracker_cells_position.y());
    BUILD_U16(tank_tracker_cells_size.x());
    BUILD_U16(tank_tracker_cells_size.y());

    for (const VREntry& entry : _cb.o->output_tanks)
    {
        _cb.tank = &entry;
        BUILD(TANK);
    }
}

// Explicit template instanciation para (version, mode)
#define INSTATIATE_PACKET_BUILDER_METHODS(version, mode)                                                           \
    template void PacketBuilder::_build_packet_RESOURCES_BEGIN  <version, mode>(uint max_resource_count);          \
    template void PacketBuilder::_build_packet_RESOURCE         <version, mode>(const std::string& resource_path); \
    template void PacketBuilder::_build_packet_RESOURCES_END    <version, mode>();                                 \
    template void PacketBuilder::_build_packet_GAME_CONFIG      <version, mode>(IDR gmap_id);                      \
    template void PacketBuilder::_build_packet_GAME_START_OK    <version, mode>();                                 \
    template void PacketBuilder::_build_packet_GAME_START_FAILED<version, mode>();                                 \
    template void PacketBuilder::_build_packet_GAME_FINISHED    <version, mode>();                                 \
    template void PacketBuilder::_build_packet_VOTEMAP          <version, mode>(const std::vector<uint>& vote_map);\
    template void PacketBuilder::_build_packet_VIEW_RESULTS     <version, mode>(GMap* gmap, IDR view_id, const PlaySession& play_session, const engine::simple::ViewRendererOutput& output); \
    template void PacketBuilder::_build_packet_RANKING          <version, mode>(GMap* gmap, IDR view_id);          \
    template void PacketBuilder::_build_packet_RADAR            <version, mode>(GMap* gmap);                       \
    template void PacketBuilder::_build_packet_GMAP             <version, mode>(GMap* gmap);                       \


INSTATIATE_PACKET_BUILDER_METHODS(1, Mode::Text)
INSTATIATE_PACKET_BUILDER_METHODS(1, Mode::Binary)