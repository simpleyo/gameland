#pragma once

// Todo esto es compartido por cliente y servidor.
// El cliente debe incluir protocol.h el cual incluye este fichero.

extern const char HANDSHAKE_MAGIC_STRING[];
extern const unsigned int HANDSHAKE_HEADER_SIZE;

struct TransmissionMode { enum _ { Text =0, Binary, MaxNumModes }; };
