package launchers

import (
	"sync"
	"time"
)

// Tiempo maximo que puede pasar hasta recibir un REFRESH_LAUNCHER_INSTANCE_STATE.
// Si se pasa entonces el launcher instance sera eliminado del map.
const launcherRefreshTimeout = time.Minute * 1 // Un minuto.
const taskRemoveLostLaunchersInterval = time.Second * 6

var g_launchersInfo = launchersInfo{
	Instances: map[string]*LauncherInfoEntry{}, // Mapa de launcher instances. Estan indexadas por launcher_id.
}

func taskRemoveLostLaunchers() {
	for {
		// Elimina los launchers que no han recibido REFRESH_LAUNCHER_INSTANCE_STATE.
		// Cuidado: Se eliminan elementos de <g_launchersInfo.Instances> mientras se recorre. Es necesario hacerlo en dos pasos.
		removed_launchers := make([]*LauncherInfoEntry, 0, 128)

		launchers := GetLaunchers()
		for _, lrie := range launchers {
			lrie.RLock()
			expireTime, err := time.Parse(time.RFC3339, lrie.Expire_time)
			if err != nil {
				panic(0)
			}
			lrie.RUnlock()
			if time.Now().After(expireTime) {
				removed_launchers = append(removed_launchers, lrie)
			}
		}

		g_launchersInfo.Lock()
		for _, lrie := range removed_launchers {
			delete(g_launchersInfo.Instances, lrie.Launcher_id)
		}
		g_launchersInfo.Unlock()

		time.Sleep(taskRemoveLostLaunchersInterval)
	}
}

func init() {
	go taskRemoveLostLaunchers()
}

func GetLauncher(launcherId string) *LauncherInfoEntry {
	var result *LauncherInfoEntry

	g_launchersInfo.RLock()

	if lrie, ok := g_launchersInfo.Instances[launcherId]; ok {
		result = lrie
	}

	g_launchersInfo.RUnlock()

	return result
}

func GetLaunchers() []*LauncherInfoEntry {
	result := make([]*LauncherInfoEntry, 0, 64)

	g_launchersInfo.RLock()
	for _, lrie := range g_launchersInfo.Instances {
		result = append(result, lrie)
	}
	g_launchersInfo.RUnlock()

	return result
}

func AddLauncher(lri *LauncherInfo) *LauncherInfoEntry {
	lrie := &LauncherInfoEntry{LauncherInfo: *lri}
	lrie.Expire_time = time.Now().Add(launcherRefreshTimeout).Format(time.RFC3339)

	g_launchersInfo.Lock()
	g_launchersInfo.Instances[lri.Launcher_id] = lrie
	g_launchersInfo.Unlock()

	return lrie
}

// RefreshLauncher actualiza el refresh expire time del launcher.
func RefreshLauncher(launcherId string) *LauncherInfoEntry {
	lrie := GetLauncher(launcherId)
	if lrie != nil {
		lrie.RLock()
		expireTime, err := time.Parse(time.RFC3339, lrie.Expire_time)
		if err != nil {
			panic(0)
		}
		lrie.RUnlock()

		if expireTime.After(time.Now()) {
			lrie.Lock()
			lrie.Expire_time = time.Now().Add(launcherRefreshTimeout).Format(time.RFC3339)
			lrie.Unlock()
		}
	}
	return lrie
}

func RemoveLauncher(launcherId string) {
	g_launchersInfo.Lock()
	delete(g_launchersInfo.Instances, launcherId)
	g_launchersInfo.Unlock()
}

func RemoveLaunchersByAddressAndPort(ipv4_address string, port uint) {
	launchers := GetLaunchers()
	for _, lrie := range launchers {
		lrie.RLock()
		if lrie.Ipv4_address == ipv4_address && lrie.Port == port {
			delete(g_launchersInfo.Instances, lrie.Launcher_id)
		}
		lrie.RUnlock()
	}
}

type dict = map[string]any

type LauncherInfo struct {
	Launcher_id          string
	Ipv4_address         string
	Port                 uint
	Max_gameserver_count uint
	Expire_time          string
}

type LauncherInfoEntry struct {
	LauncherInfo
	sync.RWMutex
}

type launchersInfo struct {
	Instances map[string]*LauncherInfoEntry // Mapa de launcher instances. Estan indexadas por launcher_id.

	sync.RWMutex
}
