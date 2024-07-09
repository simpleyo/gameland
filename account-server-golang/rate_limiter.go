package main

import (
	"strings"
	"sync"
	"time"

	"github.com/gofiber/websocket/v2"
)

// Map is like a Go map[interface{}]interface{} but is safe for concurrent use by multiple goroutines without additional locking or coordination.
// Loads, stores, and deletes run in amortized constant time.
// The Map type is optimized for two common use cases:
// (1) when the entry for a given key is only ever written once but read many times, as in caches that only grow, or
// (2) when multiple goroutines read, write, and overwrite entries for disjoint sets of keys. In these two cases,
// 	use of a Map may significantly reduce lock contention compared to a Go map paired with a separate Mutex or RWMutex.
//
var rateLimitsMap = sync.Map{}

var RATE_LIMITS_PER_COMMAND_DEFAULT_CONFIG = RateLimitsConfig{
	MaxCallsPerMinute: 100,
	MaxCallsPerHour:   10000,
}

var RATE_LIMITS_PER_COMMAND_OVERRIDE_CONFIG = []RateLimitedCommandOverrideConfig{
	{"LOGIN_AS_GUEST", -1, -1},
	{"LOGIN", -1, -1},
	{"REGISTER_ACCOUNT", 10, 100},
	{"AUTHENTICATE_SESSION_TICKET", -1, -1},
	{"UPDATE_PLAYER_DATA", -1, -1},
	{"MATCHMAKE", -1, -1},
	{"READ_RANKING", -1, -1},
	{"READ_GAME_SERVERS", -1, -1},
	{"GET_GAME_RESOURCE", -1, -1},
	{"BUY_WITH_GOLD", -1, -1},
	{"PUT_COMMENT", 1, 12},
}

type CommandRateLimits struct {
	MinuteTimeEnd   time.Time // Timestamp con el final del tramo para contabilizar el numero maximo de llamadas por minuto.
	MinuteCallCount uint
	HourTimeEnd     time.Time // Timestamp con el final del tramo para contabilizar el numero maximo de llamadas por hora.
	HourCallCount   uint
}

type RateLimits struct {
	Commands map[string]*CommandRateLimits
}

type RateLimitsConfig struct {
	MaxCallsPerMinute uint
	MaxCallsPerHour   uint
}

type RateLimitedCommandOverrideConfig struct {
	Command           string
	MaxCallsPerMinute int
	MaxCallsPerHour   int
}

type RateLimitedCommandConfig struct {
	Command           string
	MaxCallsPerMinute uint
	MaxCallsPerHour   uint
}

var RATE_LIMITS_PER_COMMAND_CONFIG = func() []RateLimitedCommandConfig {
	r := make([]RateLimitedCommandConfig, len(RATE_LIMITS_PER_COMMAND_OVERRIDE_CONFIG))
	for i, oc := range RATE_LIMITS_PER_COMMAND_OVERRIDE_CONFIG {
		cminute := RATE_LIMITS_PER_COMMAND_DEFAULT_CONFIG.MaxCallsPerMinute
		chour := RATE_LIMITS_PER_COMMAND_DEFAULT_CONFIG.MaxCallsPerHour
		if oc.MaxCallsPerMinute >= 0 {
			cminute = uint(oc.MaxCallsPerMinute)
		}
		if oc.MaxCallsPerHour >= 0 {
			chour = uint(oc.MaxCallsPerHour)
		}
		r[i] = RateLimitedCommandConfig{oc.Command, cminute, chour}
	}
	return r
}()

// Dado un comando devuelve su indice en RATE_LIMITS_PER_COMMAND_CONFIG
var RATE_LIMITED_COMMAND_INDEX = func() map[string]uint {
	r := map[string]uint{}
	for i, cm := range RATE_LIMITS_PER_COMMAND_CONFIG {
		r[cm.Command] = uint(i)
	}
	return r
}()

func rateLimiterPerCommand(command *string, c *websocket.Conn) bool {
	//
	// rateLimitsMap es un mapa que se debe ir actualizando con cada llamada a rateLimiterPerCommand.
	//
	// Valores de configuracion:
	//	- Para cada comando se debe configurar:
	//		- Numero maximo de llamadas por minuto.
	//		- Numero maximo de llamadas por hora.
	//
	// Para cada IP se debe guardar:
	//	- para cada comando:
	//		- Timestamp con el final del tramo para contabilizar el numero maximo de llamadas por minuto.
	//		- Timestamp con el final del tramo para contabilizar el numero maximo de llamadas por hora.
	//		- Numero de llamadas acumuladas en el tramo minuto.
	//		- Numero de llamadas acumuladas en el tramo hora.
	//

	var ip string

	remoteAddr := c.Conn.RemoteAddr().String()
	// fmt.Println("remoteAddr: ", remoteAddr)
	if accountServerConfig.IS_TEST_INSTANCE {
		// Si el account server es una instancia para test entonces las ips de los clientes de test incluyen tambien el puerto.
		// Esto permite que los clientes de test ejecutados desde una misma ip (normalmente localhost)
		// se vean como clientes diferentes para el rate limiter.
		ip = remoteAddr
	} else {
		ip = remoteAddr[:strings.Index(remoteAddr, ":")]
	}

	now := time.Now()

	if commandIndex, ok := RATE_LIMITED_COMMAND_INDEX[*command]; ok {

		if v, loaded := rateLimitsMap.Load(ip); loaded {
			iprt := v.(*RateLimits)
			if crt, ok := iprt.Commands[*command]; ok {
				// Minute
				if now.Before(crt.MinuteTimeEnd) {
					crt.MinuteCallCount++
					if crt.MinuteCallCount > RATE_LIMITS_PER_COMMAND_CONFIG[commandIndex].MaxCallsPerMinute {
						return true
					}
				} else {
					crt.MinuteTimeEnd = now.Add(time.Minute)
					crt.MinuteCallCount = 0
				}
				// Hour
				if now.Before(crt.HourTimeEnd) {
					crt.HourCallCount++
					if crt.HourCallCount > RATE_LIMITS_PER_COMMAND_CONFIG[commandIndex].MaxCallsPerHour {
						return true
					}
				} else {
					crt.HourTimeEnd = now.Add(time.Hour)
					crt.HourCallCount = 0
				}
			}
		} else {
			rate_limits := RateLimits{
				Commands: map[string]*CommandRateLimits{},
			}

			for _, cm := range RATE_LIMITS_PER_COMMAND_CONFIG {
				rate_limits.Commands[cm.Command] =
					&CommandRateLimits{MinuteTimeEnd: now.Add(time.Minute), MinuteCallCount: 0, HourTimeEnd: now.Add(time.Hour), HourCallCount: 0}
			}

			rateLimitsMap.Store(ip, &rate_limits)

			return rateLimiterPerCommand(command, c)
		}
	}

	return false
}
