#pragma once

#include <string>
#include <iostream>
#include <sstream>
#include <vector>
#include <cstdint>

#include "core/json_types.h"
#include "core/json/include/json.hpp"

// Permiten el acceso a las propiedades de configuracion hardcoded, cargadas mediante _load_config. 
// Las cuales estan declaradas en la clase Config.
#define  SRVCONFIG (*::Config::get_singleton())
#define  GAMCONFIG (*::Config::get_singleton()).game
#define  ENGCONFIG (*::Config::get_singleton()).game.engine

// Obtiene o define (en caso de que no exista ya) un path de configuracion asignandole un valor.
// Si el path ya existe, porque ya se definio con GET_OR_DEF_CONFIG_VALUE o porque
// se ha cargado desde el fichero de configuracion, entonces su valor no se modifica.
#define  GET_OR_DEF_CONFIG_VALUE(type, path, value) (*Config::get_singleton()).def_config<type>(path, value)
#define  GET_OR_DEF_CONFIG_STR(path, value) GET_OR_DEF_CONFIG_VALUE(std::string, path, value)

#define  EXISTS_CONFIG_PATH(path) (*Config::get_singleton()).exists_config_path(path)
// Devuelve el objeto json asociado al path. Retorna NULL en caso de que el path no exista.
#define  GET_CONFIG_JSON(path) (*Config::get_singleton()).get_config_json(path)

#define  GET_CONFIG_VALUE(type, path) (*Config::get_singleton()).get_config<type>(path)
#define  GET_CONFIG_STR(path) GET_CONFIG_VALUE(std::string, path) 

// Permite sobrescribir una variable de configuracion ya cargada. La variable debe estar declarada en la clase Config (debe ser accesible mediante (*Config::get_singleton()).VAR_NAME)
// Se utiliza para sobrescribir variables de configuracion cuando se pasan argumentos al gameserver desde la linea de comandos.
#define  OVERWRITE_CONFIG_VALUE(type, root_var, value) {(*Config::get_singleton()).def_config<type>(#root_var, value, true); (*Config::get_singleton()).root_var = value; }
#define  OVERWRITE_CONFIG_STR(root_var, value) OVERWRITE_CONFIG_VALUE(std::string, root_var, value)

using nlohmann::json;

//
// Las propiedades de configuracion NO deben ser modificadas durante la ejecucion del programa.
//
// Existen dos tipos de propiedades de configuracion (con respecto a su velocidad de acceso):
//  - Hardcoded: Son las que estan definidas en Config y se cargan, desde la configuracion en json,
//      mediante la funcion _load_config. Estas propiedades, una vez cargadas, son accesibles 
//      durante toda la duracion del programa. Su acceso es inmediato. El coste es solo el de una indireccion (Config::get_singleton()).
//  - Softcoded: No se definen en Config pero pueden ser accedidas. Aunque de una manera mas lenta que
//      las propiedades hardcoded. Se acceden mediante las macros GET_CONFIG_... Es posible definir propiedades softcoded mediante las macros GET_OR_DEF_CONFIG_...
//
class Config
{
public:
    static Config* get_singleton() { return _singleton; }    
    
    // @param config Configuracion en formato json.
    Config(const std::string& config);
    ~Config();

    const json* get_config_json(const std::string& path) const;

    template <typename T> T def_config(const std::string& path, const T& value, bool overwrite=false);
    template <typename T> T get_config(const std::string& path);
    bool exists_config_path(const std::string& path, const nlohmann::json** ob=NULL) const;

private:
    static Config* _singleton;

    void _load_config(const std::string& config);

    using intvector_t = std::vector<int>;
    using strvector_t = std::vector<std::string>;

public:
    json cfg;

    // ATENCION: Los comentarios deben ponerse en config.cpp

    uint32_t        GAME_SERVER_ID          ;
    std::string     GAME_SERVER_ID_STR      ;

    std::string     GAME_SERVER_BUILD_ID    ;
    std::string     GAME_SERVER_NAME_PREFIX ;
    std::string     GAME_SERVER_ADDRESS     ;
    uint32_t        GAME_SERVER_PORT        ;
    std::string     GAME_SERVER_REGION      ;
    std::string     ROOT_PATH               ;
    std::string     RESOURCES_PATH          ;

    bool            DISABLE_PACKETS_COMPRESSION;

    uint32_t        MAX_NUMBER_OF_USERS_PER_ROOM  ; 
    uint32_t        MAX_NUMBER_OF_PLAYERS_PER_ROOM; 
    uint32_t        MAX_NUMBER_OF_ROOMS           ; 

    bool            USE_BOTS                ; 

    struct Game
    {
        std::string     GAME_NAME                  ;
        std::string     MAP_SELECTION_METHOD       ;
        std::string     DEFAULT_MAP                ;
        uint32_t        PLAYER_ID_BITS             ;

        struct Engine
        {
            uint32_t        BOX2D_PIXELS_PER_METER     ;
            uint32_t        BOX2D_VEL_ITERATIONS       ;
            uint32_t        BOX2D_POS_ITERATIONS       ;

            uint32_t        GRAVITY_FACTOR      ;
            uint32_t        JUMP_VELOCITY_FACTOR;
        } engine;

    } game;

};

