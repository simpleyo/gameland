#include "core/json/include/json.hpp"

#include "core/defs.h"
#include "core/json_types.h"
#include "core/types.h"
#include "core/utils.h"

#include "config/config.h"

using json = nlohmann::json;

static json cfg;   // GLOBAL 

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

// Monitor
#define MTR_LOAD_CONFIG_VALUE(x)  { x = cfg[#x]; }      
#define MTR_LOAD_CONFIG_STRING(x) { x = cfg[#x].get<std::string>(); }

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

    json* cur = NULL;             
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

    // Monitor
    MTR_LOAD_CONFIG_STRING(GAME_SERVER_ADDRESS   );
    MTR_LOAD_CONFIG_VALUE (GAME_SERVER_PORT      );

    MTR_LOAD_CONFIG_VALUE (MAX_NUMBER_OF_BOTS    );

}


