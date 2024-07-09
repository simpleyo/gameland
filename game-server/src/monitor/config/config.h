#pragma once

#include <string>
#include <iostream>
#include <sstream>
#include <vector>
#include <cstdint>

#include "core/types.h"
#include "core/json_types.h"
#include "core/json/include/json.hpp"

// Permiten el acceso a las propiedades de configuracion hardcoded, cargadas mediante _load_config. 
// Las cuales estan declaradas en la clase Config.
#define  MNRCONFIG (*Config::get_singleton())

// Define una path de configuracion asignandole un valor.
// Si el path ya existe, porque ya se definio con GET_OR_DEF_CONFIG_VALUE o porque
// se ha cargado desde el fichero de configuracion, entonces su valor no se modifica.
#define  GET_OR_DEF_CONFIG_VALUE(type, path, value) (*Config::get_singleton()).def_config<type>(path, value)
#define  GET_OR_DEF_CONFIG_STR(path, value) GET_OR_DEF_CONFIG_VALUE(std::string, path, value)

#define  EXISTS_CONFIG_PATH(path) (*Config::get_singleton()).exists_config_path(path)
// Devuelve el objeto json asociado al path. Retorna NULL en caso de que el path no exista.
#define  GET_CONFIG_JSON(path) (*Config::get_singleton()).get_config_json(path)

#define  GET_CONFIG_VALUE(type, path) (*Config::get_singleton()).get_config<type>(path)
#define  GET_CONFIG_STR(path) GET_CONFIG_VALUE(std::string, path) 

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
//      las propiedades hardcoded. 
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

    std::string     GAME_SERVER_ADDRESS   ;
    uint            GAME_SERVER_PORT      ;

    uint            MAX_NUMBER_OF_BOTS    ;

};

