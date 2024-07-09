#include "core/json/include/json.hpp"

#include "core/defs.h"
#include "core/json_types.h"
#include "core/types.h"
#include "core/utils.h"

#include "config/config.h"

using json = nlohmann::json;

#define DEFINE_DEF_CONFIG(type)                        \
template <>                                            \
type Config::def_config<type>(const std::string& path, const type& value, bool overwrite) \
{                                                      \
    using namespace std;                               \
                                                       \
    istringstream is(path);                            \
    string part;                                       \
    size_t pos = path.rfind("/");                      \
    string name = (pos != string::npos) ? path.substr(pos+1) : path; \
                                                       \
    json* cur = NULL;                                  \
    while (getline(is, part, '/'))                     \
    {                                                  \
        if (!cur)                                      \
        {                                              \
            if (cfg.find(part) == cfg.end()) {         \
                if (part == name) cfg[part] = value;   \
                else cfg[part] = json();               \
            }                                          \
            else if (overwrite && (part == name))      \
                cfg[part] = value;                     \
            cur = &(cfg[part]);                        \
        }                                              \
        else                                           \
        {                                              \
            if (cur->find(part) == cur->end()) {       \
                if (part == name) (*cur)[part] = value;\
                else (*cur)[part] = json();            \
            }                                          \
            else if (overwrite && (part == name))      \
                cfg[part] = value;                     \
            cur = &((*cur)[part]);                     \
        }                                              \
                                                       \
        /*cout << part << endl;*/                      \
    }                                                  \
                                                       \
    RTCHECK(cur);                                      \
    return cur->get<type>();                           \
}

#define DEFINE_GET_CONFIG(type)                        \
template <>                                            \
type Config::get_config<type>(const std::string& path) \
{                                                      \
    using namespace std;                               \
                                                       \
    istringstream is(path);                            \
    string part;                                       \
                                                       \
    json* cur = NULL;                                  \
    while (getline(is, part, '/'))                     \
    {                                                  \
        if (!cur)                                      \
        {                                              \
            if (cfg.find(part) == cfg.end()) { cerr << "Config value not found: " << path << endl; RTCHECK(false); return type(); } \
            cur = &(cfg[part]);                        \
        }                                              \
        else                                           \
        {                                              \
            if (cur->find(part) == cur->end()) { cerr << "Config value not found: " << path << endl; RTCHECK(false);  return type(); } \
            cur = &((*cur)[part]);                     \
        }                                              \
                                                       \
        /*cout << part << endl;*/                      \
    }                                                  \
                                                       \
    RTCHECK(cur);                                      \
    return cur->get<type>();                           \
}

#define DEFINE_CONFIG_FUNCTIONS_FOR_TYPE(type) \
    DEFINE_DEF_CONFIG(type) \
    DEFINE_GET_CONFIG(type)

DEFINE_CONFIG_FUNCTIONS_FOR_TYPE(bool)
DEFINE_CONFIG_FUNCTIONS_FOR_TYPE(int)
DEFINE_CONFIG_FUNCTIONS_FOR_TYPE(uint)
DEFINE_CONFIG_FUNCTIONS_FOR_TYPE(float)
DEFINE_CONFIG_FUNCTIONS_FOR_TYPE(std::string)

// Server
#define SRV_LOAD_CONFIG_VALUE(x)  { x = cfg[#x]; }      
#define SRV_LOAD_CONFIG_STRING(x) { x = cfg[#x].get<std::string>(); }
#define SRV_INIT_CONFIG_VALUE(x, v) { x = v; } 

// Game
#define GAM_LOAD_CONFIG_VALUE(x)  { game.x = cfg["game"][#x]; } 
#define GAM_LOAD_CONFIG_STRING(x) { game.x = cfg["game"][#x].get<std::string>(); }
#define GAM_LOAD_CONFIG_STRVEC(x) { game.x = cfg["game"][#x].get<std::vector<std::string>>(); }
#define GAM_INIT_CONFIG_VALUE(x, v) { game.x = v; } 
// Engine
#define ENG_LOAD_CONFIG_VALUE(x)  { game.engine.x = cfg["game"]["engine"][#x]; } 
#define ENG_LOAD_CONFIG_STRING(x) { game.engine.x = cfg["game"]["engine"][#x].get<std::string>(); }
#define ENG_LOAD_CONFIG_INTVEC(x) { game.engine.x = cfg["game"]["engine"][#x].get<std::vector<int>>(); }
#define ENG_LOAD_CONFIG_STRVEC(x) { game.engine.x = cfg["game"]["engine"][#x].get<std::vector<std::string>>(); }
#define ENG_INIT_CONFIG_VALUE(x, v)  { game.engine.x = v; } 

Config* Config::_singleton = NULL;

Config::Config(const std::string& config)
{    
    RTCHECK(!_singleton);
    _singleton = this;

    _load_config(config);

    //std::cout << GET_CONFIG_STR("game/GAME_NAME");
    //std::cout << GET_CONFIG_VALUE(bool, "game/HOLA");
}

Config::~Config()
{
    RTCHECK(_singleton);
    _singleton = NULL;
}

bool Config::exists_config_path(const std::string& path, const nlohmann::json** ob) const
{
    using namespace std;    

    const json* cur = NULL;             
    if (path.empty()) 
    {
        cur = &cfg;
    }
    else
    {
        istringstream is(path);       
        string part;                                                    
        
        while (getline(is, part, '/'))
        {                             
            if (!cur)                 
            {                         
                if (cfg.find(part) == cfg.end()) return false;
                cur = &(cfg[part]);
            }                      
            else                   
            {                      
                if (cur->find(part) == cur->end()) return false;
                cur = &((*cur)[part]);
            }                         
        }  
    }

    if (ob)
        *ob = cur;

    return true;
}

const nlohmann::json* Config::get_config_json(const std::string& path) const
{
    const json* ob;
    if (exists_config_path(path, &ob))
        return ob;
    else
        return NULL;
}

void Config::_load_config(const std::string& config)
{
    cfg = json::parse(config.c_str()); 

    // Server
    SRV_INIT_CONFIG_VALUE (GAME_SERVER_ID        , 0);
    SRV_INIT_CONFIG_VALUE (GAME_SERVER_ID_STR    , "0");

    SRV_LOAD_CONFIG_STRING(GAME_SERVER_BUILD_ID  );
    SRV_LOAD_CONFIG_STRING(GAME_SERVER_NAME_PREFIX);
    SRV_LOAD_CONFIG_STRING(GAME_SERVER_ADDRESS   );
    SRV_LOAD_CONFIG_VALUE (GAME_SERVER_PORT      );
    SRV_LOAD_CONFIG_STRING(GAME_SERVER_REGION    );
    SRV_LOAD_CONFIG_STRING(ROOT_PATH             );
    SRV_LOAD_CONFIG_STRING(RESOURCES_PATH        );

    SRV_LOAD_CONFIG_VALUE (DISABLE_PACKETS_COMPRESSION   ); // Desactiva la compresion de los paquetes enviados a los clientes.

    SRV_LOAD_CONFIG_VALUE (MAX_NUMBER_OF_USERS_PER_ROOM  ); // Es el numero maximo de instancias de User. Tambien especifica el numero de slots del servidor de websockets.
    SRV_LOAD_CONFIG_VALUE (MAX_NUMBER_OF_PLAYERS_PER_ROOM); // El numero maximo de players. Limita el numero maximo de instancias de PlaySession que puede haber al mismo tiempo.
    SRV_LOAD_CONFIG_VALUE (MAX_NUMBER_OF_ROOMS           );

    SRV_LOAD_CONFIG_VALUE (USE_BOTS              ); // El gameserver creara bots si no hay usuarios reales suficientes.   

    // Game

    GAM_LOAD_CONFIG_STRING(GAME_NAME             );
    GAM_LOAD_CONFIG_STRING(MAP_SELECTION_METHOD  ); // Valores validos: ["fixed", "votemap", "random"]
    GAM_LOAD_CONFIG_STRING(DEFAULT_MAP           );
    GAM_INIT_CONFIG_VALUE (PLAYER_ID_BITS, required_bits(MAX_NUMBER_OF_PLAYERS_PER_ROOM-1));

    // Engine

    ENG_LOAD_CONFIG_VALUE(BOX2D_PIXELS_PER_METER );
    ENG_LOAD_CONFIG_VALUE(BOX2D_VEL_ITERATIONS   );
    ENG_LOAD_CONFIG_VALUE(BOX2D_POS_ITERATIONS   );

    ENG_LOAD_CONFIG_VALUE(GRAVITY_FACTOR         ); // [Client/Server] Constante multiplicadora para ajustar gravity (g *= GRAVITY_FACTOR/100.f, si es 100 no tiene efecto). 
    ENG_LOAD_CONFIG_VALUE(JUMP_VELOCITY_FACTOR   ); // [Server] Constante multiplicadora para ajustar la contribucion que la velocidad tiene en la duracion del salto (v *= JUMP_VELOCITY_FACTOR/100.f, si es 100 no tiene efecto). 
    
}


