#include "client_protocol.h"
#include "config/config.h"
#include "core/defs.h"
#include "gameserver/protocol.h"
#include "gameserver/engine/iinput_state.h"
#include "packet_builder.h"

using Mode   = PacketBuilder::Mode;

#define CLEAR_BUILD \
    DECLARE_BUILDER \
    bdr.reset();

#define BUILD(x) _build_##x<version,mode>()

#define BUILD_TOKEN(x) bdr.build_token(_cb.buffer, Token::x)

#define BUILD_RAW_BYTES(x, num_bytes) bdr.build_bytes(_cb.buffer, x, num_bytes)
#define BUILD_RAW_BYTE(x) { const ubyte data[1] = { (ubyte)x }; BUILD_RAW_BYTES((ubyte*)data, 1); }
#define _BUILD_BYTES(size_type, x, num_bytes) bdr.build_sized_bytes<size_type>(_cb.buffer, x, (size_type)num_bytes)

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

            virtual void build_sized_bytes(std::vector<ubyte>& p_buffer, const ubyte* p_data, uint p_data_size) = 0;  // Template <size_type>
            virtual void build_bytes(std::vector<ubyte>& p_buffer, const ubyte* p_data, uint p_data_size) = 0;
            
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
        void build_sized_bytes(std::vector<ubyte>& p_buffer, const ubyte* p_data, uint p_data_size);
        void build_bytes(std::vector<ubyte>& p_buffer, const ubyte* p_data, uint p_data_size);

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
        const ubyte* p_token = (const ubyte*)tokenV1_str[p_token_id];
        build_bytes(p_buffer, p_token, (uint)strlen((const char*)p_token));

        p_buffer.push_back(' ');    // Add space.
    }

    void PacketBuilderImpl<1, Mode::Text>::build_bytes(std::vector<ubyte>& p_buffer, const ubyte* p_data, uint p_data_size)
    {
        p_buffer.insert(p_buffer.end(), p_data, p_data + p_data_size);
    }

    template <typename size_type>
    void PacketBuilderImpl<1, Mode::Text>::build_sized_bytes(std::vector<ubyte>& p_buffer, const ubyte* p_data, uint p_data_size)
    {
        _build_value<size_type>(p_buffer, p_data_size);
        build_bytes(p_buffer, p_data, p_data_size);
        p_buffer.push_back(' ');    // Add space.
    }

    template <typename T>
    void PacketBuilderImpl<1, Mode::Text>::_build_value(std::vector<ubyte>& p_buffer, T v)
    {
        std::string s = std::to_string(v);
        build_bytes(p_buffer, (const ubyte*)s.c_str(), (uint)s.length());
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

        void build_bytes(std::vector<ubyte>& p_buffer, const ubyte* p_data, uint p_data_size);
        template <typename size_type>
        void build_sized_bytes(std::vector<ubyte>& p_buffer, const ubyte* p_data, uint p_data_size);

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

    void PacketBuilderImpl<1, Mode::Binary>::build_bytes(std::vector<ubyte>& p_buffer, const ubyte* p_data, uint p_data_size)
    {
        p_buffer.insert(p_buffer.end(), p_data, p_data + p_data_size);
    }

    template <typename size_type>
    void PacketBuilderImpl<1, Mode::Binary>::build_sized_bytes(std::vector<ubyte>& p_buffer, const ubyte* p_data, uint p_data_size)
    {
        _build_value<size_type>(p_buffer, p_data_size);
        build_bytes(p_buffer, p_data, p_data_size);
    }

    template <typename T>
    void PacketBuilderImpl<1, Mode::Binary>::_build_value(std::vector<ubyte>& p_buffer, T v)
    {
        const T* ptr = &v;
        build_bytes(p_buffer, (ubyte*)ptr, sizeof(T));        
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

template <uint version, Mode mode>
void PacketBuilder::_build_packet_CLIENT_HANDSHAKE()
{
    // Los parametros version y mode del template se ignoran en este caso puesto que el paquete CLIENT_HANDSHAKE es el que decide la version y el modo.
    CLEAR_BUILD;                                           
                                                             
    BUILD_RAW_BYTE(0);    // Flags del mensaje.
    BUILD_RAW_BYTES((const ubyte*)HANDSHAKE_MAGIC_STRING, 4);

#if CLIENT_PROTOCOL_VERSION == 1
    const ubyte p_version[] = "001";
#endif

    BUILD_RAW_BYTES(p_version, 3);

#ifdef USE_TEXT_PROTOCOL
    const ubyte p_mode[] = "0";   /* '0'=Text, '1'=Binary */   
#else
    const ubyte p_mode[] = "1";
#endif

    BUILD_RAW_BYTES(p_mode, 1);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_GAME_PING(uint p_game_ping_id)
{        
    CLEAR_BUILD;                              
    
    BUILD_RAW_BYTE(MESSAGE_FLAGS::MSG_INTERNAL);    // Flags del mensaje.
    BUILD_U8(INTERNAL_TOKEN::PING);

    BUILD_RAW_BYTES((const ubyte*)&p_game_ping_id, 4);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_START_GAME(const std::string& p_start_game_request_data)
{
    CLEAR_BUILD;                                         
                              
    BUILD_RAW_BYTE(0);    // Flags del mensaje.
    BUILD_TOKEN(START_GAME);                             
    BUILD_BYTES_32((const ubyte*)p_start_game_request_data.c_str(), p_start_game_request_data.size());
    BUILD_TOKEN(END);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_RESOURCES_REQUEST()
{
    CLEAR_BUILD;                   
                                   
    BUILD_RAW_BYTE(0);    // Flags del mensaje.
    BUILD_TOKEN(RESOURCES_REQUEST);
    BUILD_TOKEN(END);                
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_GAME_CONFIG_OK()
{
    CLEAR_BUILD;                
                              
    BUILD_RAW_BYTE(0);    // Flags del mensaje.
    BUILD_TOKEN(GAME_CONFIG_OK);
    BUILD_BYTES_32((ubyte*)"BOT_DOMAIN", 10);
    BUILD_TOKEN(END);
}

template <uint version, Mode mode>
void PacketBuilder::_build_packet_INPUT_STATE(uint64 p_client_time, uint p_changes, const Point2& p_input_pos, uint p_actions)
{
    CLEAR_BUILD;             
                       
    BUILD_RAW_BYTE(0);    // Flags del mensaje.
    BUILD_TOKEN(INPUT_STATE);

    BUILD_U64(p_client_time);
    BUILD_U8(p_changes);

    using Change = GameInputChange;
    if (p_changes & Change::InputPositionChanged)
    {
        BUILD_I32((uint)p_input_pos.x);         
        BUILD_I32((uint)p_input_pos.y);         
    }
    if (p_changes & Change::ActionsChanged)
    {
        BUILD_U32(p_actions);
    }
   
    BUILD_TOKEN(END);
}

// Explicit template instanciation para (version, mode)
#define INSTATIATE_PACKET_BUILDER_METHODS(version, mode)                                                                                                          \
    template void PacketBuilder::_build_packet_CLIENT_HANDSHAKE <version, mode>();                                                                                \
    template void PacketBuilder::_build_packet_GAME_PING        <version, mode>(uint p_game_ping_id);                                                             \
    template void PacketBuilder::_build_packet_START_GAME       <version, mode>(const std::string& p_start_game_request_data);                                    \
    template void PacketBuilder::_build_packet_RESOURCES_REQUEST<version, mode>();                                                                                \
    template void PacketBuilder::_build_packet_GAME_CONFIG_OK   <version, mode>();                                                                                \
    template void PacketBuilder::_build_packet_INPUT_STATE      <version, mode>(uint64 p_client_time, uint p_changes, const Point2& p_input_pos, uint p_actions);


INSTATIATE_PACKET_BUILDER_METHODS(1, Mode::Text)
INSTATIATE_PACKET_BUILDER_METHODS(1, Mode::Binary)