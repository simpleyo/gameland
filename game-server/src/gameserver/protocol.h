#pragma once

// AVISO: Todo lo siguiente es compartido por cliente y servidor. Debe ser identico en ambos lados para no romper el protocolo.
//  No usar namespaces porque podria dar problemas con emscripten.

#include "gameserver/handshake.h"

#ifdef GAME_SERVER
    #define PROTOCOL_IN_TOKEN(version) ParserTokenV##version
    #define PROTOCOL_OUT_TOKEN(version) BuilderTokenV##version
#else // GAME_CLIENT
    #define PROTOCOL_IN_TOKEN(version) BuilderTokenV##version
    #define PROTOCOL_OUT_TOKEN(version) ParserTokenV##version

#if defined(JAVASCRIPT_ENABLED) || defined(ANDROID_ENABLED)
    #define PROTOCOL_IN_TOKEN_STR(version) BuilderTokenV##version##_str
    #define PROTOCOL_OUT_TOKEN_STR(version) ParserTokenV##version##_str
#endif

#endif

#define PROTOCOL_MESSAGE_FLAGS(version) ProMessageFlagV##version
#define PROTOCOL_INTERNAL_TOKEN(version) ProInternalTokenV##version

struct PROTOCOL_MESSAGE_FLAGS(1)
{   // Para cada mensaje recibido por el websocket el primer byte del mensaje contiene flags.
    enum _ {
        MSG_COMPRESSED = 0x01,  // Indica que el mensaje esta comprimido. Solo se aplica si el opCode es uWS::BINARY.
        MSG_INTERNAL   = 0x02   // Indica que el mensaje es un mensaje interno. IMPORTANTE: Los mensajes internos nunca se comprimen.
    };
};

struct PROTOCOL_INTERNAL_TOKEN(1)
{
    enum _ {
        NONE = 0        ,
        PING            ,
        PONG            ,
        BIND_REQUEST // Indica que el cliente tiene la intencion de hacer bind en el slot.             
    };        
};

struct PROTOCOL_IN_TOKEN(1)
{
    enum _ {
        _RESERVED = 0    ,
        START_GAME       ,      
        RESOURCES_REQUEST,
        GAME_CONFIG_OK   ,     
        INPUT_STATE      ,
        USER_VOTE        ,
        END              ,
        MAX_TOKENS          
    };        
};

struct PROTOCOL_OUT_TOKEN(1)
{
    enum _ {
        _RESERVED = 0    ,
        GAME_CONFIG      ,
        RESOURCES_BEGIN  ,
        RESOURCE         ,
        RESOURCES_END    ,
        GAME_START_OK    ,
        GAME_START_FAILED,
        VIEW_RESULTS     ,
        TRACKER          ,
        RADAR            ,
        RANKING          ,
        RACE             ,
        GMAP             ,
        CURRENT          ,
        CELL             ,
        PLAYERS          ,
        PLAYER           ,
        SNAKES           ,
        SNAKE            ,
        TANKS            ,
        TANK             ,
        CHAPS            ,
        CHAP             ,
        BOMBS            ,
        BOMB             ,
        BUBBS            ,
        BUBB             ,
        HEAD             ,
        BODY             ,
        MEALS            ,
        MEAL             ,
        BONUSES          ,
        BONUS            ,
        HUTS             ,
        HUT              ,
        VOTEMAP          ,
        GAME_FINISHED    ,
        END              ,
        MAX_TOKENS
    };        
};

extern const char* PROTOCOL_IN_TOKEN(1_str)[PROTOCOL_IN_TOKEN(1)::MAX_TOKENS];
extern const char* PROTOCOL_OUT_TOKEN(1_str)[PROTOCOL_OUT_TOKEN(1)::MAX_TOKENS];



