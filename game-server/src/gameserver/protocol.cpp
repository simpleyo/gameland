#ifdef GAME_SERVER
    #include "protocol.h"
#endif

#define STRINGIFY(x) #x

const char HANDSHAKE_MAGIC_STRING[] = "BT88";
const unsigned int HANDSHAKE_HEADER_SIZE = 8;

const char* PROTOCOL_IN_TOKEN(1_str)[PROTOCOL_IN_TOKEN(1)::MAX_TOKENS] = {    
    STRINGIFY(_RESERVED        ),
    STRINGIFY(START_GAME       ),
    STRINGIFY(RESOURCES_REQUEST),
    STRINGIFY(GAME_CONFIG_OK   ),
    STRINGIFY(INPUT_STATE      ),
    STRINGIFY(USER_VOTE        ),
    STRINGIFY(END              )
};

const char* PROTOCOL_OUT_TOKEN(1_str)[PROTOCOL_OUT_TOKEN(1)::MAX_TOKENS] = {
    STRINGIFY(_RESERVED        ),
    STRINGIFY(GAME_CONFIG      ),
    STRINGIFY(RESOURCES_BEGIN  ),
    STRINGIFY(RESOURCE         ),
    STRINGIFY(RESOURCES_END    ),
    STRINGIFY(GAME_START_OK    ),
    STRINGIFY(GAME_START_FAILED),
    STRINGIFY(VIEW_RESULTS     ),
    STRINGIFY(TRACKER          ),
    STRINGIFY(RADAR            ),
    STRINGIFY(RANKING          ),
    STRINGIFY(RACE             ),
    STRINGIFY(GMAP             ),
    STRINGIFY(CURRENT          ),
    STRINGIFY(CELL             ),
    STRINGIFY(PLAYERS          ),
    STRINGIFY(PLAYER           ),
    STRINGIFY(SNAKES           ),
    STRINGIFY(SNAKE            ),
    STRINGIFY(TANKS            ),
    STRINGIFY(TANK             ),
    STRINGIFY(BOMBS            ),
    STRINGIFY(BOMB             ),
    STRINGIFY(BUBBS            ),
    STRINGIFY(BUBB             ),
    STRINGIFY(HEAD             ),
    STRINGIFY(BODY             ),
    STRINGIFY(MEALS            ),
    STRINGIFY(MEAL             ),
    STRINGIFY(BONUSES          ),
    STRINGIFY(BONUS            ),
    STRINGIFY(HUTS             ),
    STRINGIFY(HUT              ),
    STRINGIFY(GAME_FINISHED    ),
    STRINGIFY(END              )
};

