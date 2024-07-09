#pragma once

// El cliente debe incluir el fichero gameserver/protocol.h
// AVISO: Todo lo del siguiente include es compartido por cliente y servidor.
#include "gameserver/protocol.h"

// Si esta definido USE_TEXT_PROTOCOL se utilizara el protocolo en texto en vez de en binario.
// El protocolo en texto es util para debug.
//#define USE_TEXT_PROTOCOL

// Aqui se selecciona la version del protocolo que utiliza el cliente.
#define CLIENT_PROTOCOL_VERSION 1

#if CLIENT_PROTOCOL_VERSION == 1
    #define INTERNAL_TOKEN PROTOCOL_INTERNAL_TOKEN(1)
    #define MESSAGE_FLAGS PROTOCOL_MESSAGE_FLAGS(1)

#ifdef JAVASCRIPT_ENABLED
    #define BUILDER_TOKENS_ENUM_STR PROTOCOL_IN_TOKEN_STR(1)
    #define PARSER_TOKENS_ENUM_STR PROTOCOL_OUT_TOKEN_STR(1)
#else
    #define BUILDER_TOKENS_ENUM_STR PROTOCOL_IN_TOKEN(1)##_str
    #define PARSER_TOKENS_ENUM_STR PROTOCOL_OUT_TOKEN(1)##_str
#endif

    #define BUILDER_TOKENS_ENUM PROTOCOL_IN_TOKEN(1)
    #define PARSER_TOKENS_ENUM PROTOCOL_OUT_TOKEN(1)

#endif

// Los ficheros, del game server, gameland/game-server/src/gameserver/engine/i*.h son compartidos
// por cliente y servidor.
