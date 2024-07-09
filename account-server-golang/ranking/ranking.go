package ranking

import (
	"account-server/database"
	"account-server/utils"
	"encoding/json"
	"fmt"
	"sort"
	"strconv"
	"sync"
	"time"

	"golang.org/x/exp/slices"
)

const RANKING_UPDATE_INTERVAL = 10 * time.Second // Tiempo entre actualizaciones del ranking.
const RANKING_MAXIMUM_SIZE = 100                 // Numero maximo de entradas en cada uno de los rankings.
const RANKING_UPDATES_CHANNEL_SIZE = 128

var rankingManager RankingManager = RankingManager{}

type RankingManager struct {
	LastUpdateTime time.Time
	GameMaps       []string

	// RankingDataIndex uint64 // Contiene el indice en [2]RankingData que se utilizara para las operaciones de lectura (por la funciones publicas). [2]RankingData funciona como un doble buffer.
	CurrRankingData *RankingData
	PrevRankingData *RankingData

	// Indexado por <account_name | guest_account_id>. Contiene todas las cuentas que no sean guest.
	// Ninguna funcion publica debe acceder a Accounts, excepto Initialize, ya que es actualizada, en update, sin ningun mecanismo que permita
	// el acceso compartido.
	// Cada dict en Accounts contiene las siguientes keys (is_guest, account_id, display_name, player_data, player_readonly_data)
	Accounts         dict
	UpdatesChannel   chan dict  // Canal donde se reciben los updates a Accounts.
	UpdatesList      []dict     // Lista en la que se insertan los updates a Accounts, de la informacion relacionada con el ranking.
	UpdatesListMutex sync.Mutex // Mutex para sincronizar el acceso a UpdatesList
}

type RankingData struct {
	RankingVersion            string
	Content                   string
	RankingPerExperience      []RankingEntry
	MapRankingPerScore        map[string][]MapRankingEntry
	MapRankingPerBestRaceTime map[string][]MapRankingEntry
	MapRankingPerBestLapTime  map[string][]MapRankingEntry
}

type dict = map[string]any

type RankingEntry struct {
	IsGuest     bool
	AccountId   string // account_name o guest_account_id
	FlagId      uint16
	DisplayName string
	Experience  uint
}

type MapRankingEntry struct {
	IsGuest         bool
	AccountId       string // account_name o guest_account_id
	FlagId          uint16 // Si es 0xFFFF indica id no valido.
	DisplayName     string
	MapScore        uint
	MapBestRaceTime uint
	MapBestLapTime  uint
}

func Initialize(gameMaps []any) {
	rankingManager.GameMaps = make([]string, 0, len(gameMaps))
	for _, m := range gameMaps {
		rankingManager.GameMaps = append(rankingManager.GameMaps, m.(string))
	}

	allAccounts, err := database.ReadAllAccounts()
	if err != nil {
		panic(err)
	}

	// Inserta en rankingManager.Accounts todas las cuentas de allAccounts.
	{
		rankingManager.Accounts = make(dict)
		for _, v := range allAccounts {
			entry := dict{
				"display_name":         v["display_name"],
				"player_data":          v["player_data"],
				"player_readonly_data": v["player_readonly_data"],
			}

			var account_id string
			if ac, ok := v["account_name"]; ok {
				account_id = ac.(string)
				entry["is_guest"] = false
			} else {
				account_id = v["guest_account_id"].(string)
				entry["is_guest"] = true
			}

			entry["account_id"] = account_id

			rankingManager.Accounts[account_id] = entry
		}
	}

	// Inicializa rankingManager.RankingData
	{
		// rankingManager.RankingDataIndex = 0

		// for k := 0; k < 2; k++ {
		// 	v := [3]map[string][]*MapRankingEntry{{}, {}, {}}
		// 	for _, mapName := range rankingManager.GameMaps {
		// 		v[0][mapName] = make([]*MapRankingEntry, 0)
		// 		v[1][mapName] = make([]*MapRankingEntry, 0)
		// 		v[2][mapName] = make([]*MapRankingEntry, 0)
		// 	}

		// 	rankingManager.RankingData[k] = &RankingData{
		// 		RankingPerExperience:      make([]*RankingEntry, 0),
		// 		MapRankingPerScore:        v[0],
		// 		MapRankingPerBestRaceTime: v[1],
		// 		MapRankingPerBestLapTime:  v[2],
		// 	}
		// }

		var rkpex = make([]RankingEntry, 0)                 // Ranking per experience
		rkpm := [3]map[string][]MapRankingEntry{{}, {}, {}} // Rankings per map
		for _, mapName := range rankingManager.GameMaps {
			rkpm[0][mapName] = make([]MapRankingEntry, 0) // per score
			rkpm[1][mapName] = make([]MapRankingEntry, 0) // per best_race_time
			rkpm[2][mapName] = make([]MapRankingEntry, 0) // per best_lap_time
		}

		for _, ac := range rankingManager.Accounts {
			acd := ac.(dict)

			rod := dict{}
			if err := json.Unmarshal([]byte(acd["player_readonly_data"].(string)), &rod); err != nil {
				fmt.Println(acd["player_readonly_data"].(string))
				panic(err)
			}

			is_guest := acd["is_guest"].(bool)
			account_id := acd["account_id"].(string)

			var flag_id uint16
			{
				pd := dict{}
				if err := json.Unmarshal([]byte(acd["player_data"].(string)), &pd); err != nil {
					panic(err)
				}

				flag_index := int(pd["flag_index"].(float64))
				if flag_index < 0 {
					flag_id = 0xFFFF
				} else {
					flag_id = uint16(rod["flag_ids"].([]any)[flag_index].(float64))
				}
			}

			display_name := acd["display_name"].(string)

			experience := uint(0)

			if md, ok := rod["maps_data"]; ok {
				for m := range md.(dict) { // Para cada map que este en la cuenta
					if index := slices.IndexFunc(rankingManager.GameMaps, func(name string) bool { return name == m }); index >= 0 {
						// Si entra aqui es porque el map esta en rankingManager.GameMaps
						h := md.(dict)[m].([]any)
						for len(h) < 3 {
							h = append(h, 0)
						}

						experience += uint(h[0].(float64))

						mrke := MapRankingEntry{is_guest, account_id, flag_id, display_name, uint(h[0].(float64)), uint(h[1].(float64)), uint(h[2].(float64))}
						rkpm[0][m] = append(rkpm[0][m], mrke) // per score
						if mrke.MapBestRaceTime > 0 {
							rkpm[1][m] = append(rkpm[1][m], mrke) // per best_race_time
						}
						if mrke.MapBestLapTime > 0 {
							rkpm[2][m] = append(rkpm[2][m], mrke) // per best_lap_time
						}
					}
				}
			}

			rke := RankingEntry{is_guest, account_id, flag_id, display_name, experience}

			rkpex = append(rkpex, rke)
		}

		// Ordena todos los rankings
		{
			sort.SliceStable(rkpex, func(i, j int) bool { // Ordena por Experience
				return rkpex[i].Experience >= rkpex[j].Experience
			})

			for _, m := range rkpm[0] { // Para cada mapa, ordena por Score
				sort.SliceStable(m, func(i, j int) bool { return m[i].MapScore >= m[j].MapScore })
			}
			for _, m := range rkpm[1] { // Para cada mapa, ordena por BestRaceTime
				sort.SliceStable(m, func(i, j int) bool { return m[i].MapBestRaceTime < m[j].MapBestRaceTime })
			}
			for _, m := range rkpm[2] { // Para cada mapa, ordena por BestLapTime
				sort.SliceStable(m, func(i, j int) bool { return m[i].MapBestLapTime < m[j].MapBestLapTime })
			}
		}

		// Inicializa rankingManager.RankingData
		// Utiliza los arrays construidos en el paso anterior limitando su tamaño a RANKING_MAXIMUM_SIZE.
		{
			rankingManager.CurrRankingData = &RankingData{}
			rankingManager.PrevRankingData = rankingManager.CurrRankingData

			rrd := rankingManager.CurrRankingData
			rrd.RankingVersion = ""
			rrd.Content = ""
			if len(rkpex) > RANKING_MAXIMUM_SIZE {
				rrd.RankingPerExperience = rkpex[:RANKING_MAXIMUM_SIZE]
			} else {
				rrd.RankingPerExperience = rkpex
			}

			for _, mapName := range rankingManager.GameMaps {
				rrd.MapRankingPerScore = map[string][]MapRankingEntry{}
				if len(rkpm[0][mapName]) > RANKING_MAXIMUM_SIZE {
					rrd.MapRankingPerScore[mapName] = rkpm[0][mapName][:RANKING_MAXIMUM_SIZE]
				} else {
					rrd.MapRankingPerScore[mapName] = rkpm[0][mapName]
				}
				rrd.MapRankingPerBestRaceTime = map[string][]MapRankingEntry{}
				if len(rkpm[0][mapName]) > RANKING_MAXIMUM_SIZE {
					rrd.MapRankingPerBestRaceTime[mapName] = rkpm[0][mapName][:RANKING_MAXIMUM_SIZE]
				} else {
					rrd.MapRankingPerBestRaceTime[mapName] = rkpm[0][mapName]
				}
				rrd.MapRankingPerBestLapTime = map[string][]MapRankingEntry{}
				if len(rkpm[0][mapName]) > RANKING_MAXIMUM_SIZE {
					rrd.MapRankingPerBestLapTime[mapName] = rkpm[0][mapName][:RANKING_MAXIMUM_SIZE]
				} else {
					rrd.MapRankingPerBestLapTime[mapName] = rkpm[0][mapName]
				}
			}
		}

		// // Inicializa el buffer de escritura rankingManager.RankingData[1]
		// {
		// 	wrd := &rankingManager.RankingData[1]
		// 	wrd.RankingPerExperience = make([]RankingEntry, 0)
		// 	wrd.MapRankingPerScore = map[string][]MapRankingEntry{}
		// 	wrd.MapRankingPerBestRaceTime = map[string][]MapRankingEntry{}
		// 	wrd.MapRankingPerBestLapTime = map[string][]MapRankingEntry{}
		// 	for _, mapName := range rankingManager.GameMaps {
		// 		wrd.MapRankingPerScore[mapName] = make([]MapRankingEntry, 0)
		// 		wrd.MapRankingPerBestRaceTime[mapName] = make([]MapRankingEntry, 0)
		// 		wrd.MapRankingPerBestLapTime[mapName] = make([]MapRankingEntry, 0)
		// 	}
		// }
	}

	rankingManager.update()

	rankingManager.UpdatesChannel = make(chan dict, RANKING_UPDATES_CHANNEL_SIZE)

	go rankingManager.appendUpdatesTask()
	go rankingManager.updateRankingTask()
}

// Obtiene las posiciones, en los rankings, de la cuenta <accountId>.
// Se devuelve un slice de la forma [pos by experience, {"map_name0": [pos by score, pos by best_race_time, pos by best_lap_time], "map_name1": ...}]
// Las posiciones validas comienzan en 1. Si es 0 significa que no esta en el ranking. Esto sucede cuando su posicion es mayor que RANKING_MAXIMUM_SIZE
// o con las cuentas que no tiene datos de un mapa, por ejemplo, por no haber jugado nunca.
func getAccountPositions(rd *RankingData, accountId string) []any {

	account_positions := []any{0, map[string][]uint{}}

	for _, m := range rankingManager.GameMaps {
		d := account_positions[1].(map[string][]uint)
		d[m] = make([]uint, 3) // [position by score, position by best_race_time, position by best_lap_time], se inicializa a [0, 0, 0]
	}

	position := uint(1)
	for _, x := range rd.RankingPerExperience {
		if x.AccountId == accountId {
			account_positions[0] = position
			break
		}
		position += 1
	}

	for _, m := range rankingManager.GameMaps {
		d := account_positions[1].(map[string][]uint)
		v := d[m]

		position = 1
		for _, x := range rd.MapRankingPerScore[m] {
			if x.AccountId == accountId {
				v[0] = position
				break
			}
			position += 1
		}

		position = 1
		for _, x := range rd.MapRankingPerBestRaceTime[m] {
			if x.AccountId == accountId {
				v[1] = position
				break
			}
			position += 1
		}

		position = 1
		for _, x := range rd.MapRankingPerBestLapTime[m] {
			if x.AccountId == accountId {
				v[2] = position
				break
			}
			position += 1
		}

		d[m] = v
	}

	return account_positions
}

func GetCurrentRanking(accountId string) (string, string, []any) {
	rd := rankingManager.CurrRankingData
	return rd.RankingVersion, rd.Content, getAccountPositions(rd, accountId)
}

// func GetVersion() string {
// 	rd := rankingManager.RankingData[atomic.LoadUint64(&rankingManager.RankingDataIndex)]
// 	return rd.RankingVersion
// }

// func GetContent() string {
// 	rd := rankingManager.RankingData[atomic.LoadUint64(&rankingManager.RankingDataIndex)]
// 	return rd.Content
// }

func OnAccountUpdated(data dict) {
	rankingManager.UpdatesChannel <- data
}

func (rm *RankingManager) appendUpdatesTask() {
	for {
		result := <-rm.UpdatesChannel
		rm.UpdatesListMutex.Lock()
		rm.UpdatesList = append(rm.UpdatesList, result)
		rm.UpdatesListMutex.Unlock()
	}
}

func (rm *RankingManager) updateRankingTask() {
	for {
		rankingManager.update()
		time.Sleep(RANKING_UPDATE_INTERVAL)
	}
}

// Actualiza todo el ranking.
func (rm *RankingManager) update() {

	rm.LastUpdateTime = time.Now()

	rd := rm.CurrRankingData
	rdw := &RankingData{}

	// Inicializa rdw
	{
		rdw.RankingPerExperience = make([]RankingEntry, 0)
		rdw.MapRankingPerScore = map[string][]MapRankingEntry{}
		rdw.MapRankingPerBestRaceTime = map[string][]MapRankingEntry{}
		rdw.MapRankingPerBestLapTime = map[string][]MapRankingEntry{}
		for _, mapName := range rankingManager.GameMaps {
			rdw.MapRankingPerScore[mapName] = make([]MapRankingEntry, 0)
			rdw.MapRankingPerBestRaceTime[mapName] = make([]MapRankingEntry, 0)
			rdw.MapRankingPerBestLapTime[mapName] = make([]MapRankingEntry, 0)
		}
	}

	// rd := &rm.RankingData[rm.RankingDataIndex]        // Buffer de lectura
	// rdw := &rm.RankingData[(rm.RankingDataIndex+1)%2] // Buffer de escritura

	rdw.RankingVersion = utils.GenerateRandomString(8)
	// // Limpia el buffer de escritura, donde se estableceran los datos de actualizacion del ranking.
	// {
	// 	rdw.RankingPerExperience = rdw.RankingPerExperience[:0]
	// 	for _, m := range rm.GameMaps {
	// 		rdw.MapRankingPerScore[m] = rdw.MapRankingPerScore[m][:0]
	// 		rdw.MapRankingPerBestRaceTime[m] = rdw.MapRankingPerBestRaceTime[m][:0]
	// 		rdw.MapRankingPerBestLapTime[m] = rdw.MapRankingPerBestLapTime[m][:0]
	// 	}
	// }

	// for k := 0; k < 2; k++ {
	// 	v := [3]map[string][]*MapRankingEntry{{}, {}, {}}
	// 	for _, mapName := range rankingManager.GameMaps {
	// 		v[0][mapName] = make([]*MapRankingEntry, 0)
	// 		v[1][mapName] = make([]*MapRankingEntry, 0)
	// 		v[2][mapName] = make([]*MapRankingEntry, 0)
	// 	}

	// 	rankingManager.RankingData[k] = &RankingData{
	// 		RankingPerExperience:      make([]*RankingEntry, 0),
	// 		MapRankingPerScore:        v[0],
	// 		MapRankingPerBestRaceTime: v[1],
	// 		MapRankingPerBestLapTime:  v[2],
	// 	}
	// }

	// Aplica las actualizaciones a rm.Accounts
	{
		rm.UpdatesListMutex.Lock()
		updatesList := rm.UpdatesList
		rm.UpdatesList = []dict{}
		rm.UpdatesListMutex.Unlock()

		for _, u := range updatesList {
			rm.Accounts[u["account_id"].(string)] = u
		}
	}

	// // Inicializa todos los arrays
	// rdw.RankingPerExperience = rdw.RankingPerExperience[:0]
	// for _, m := range rm.GameMaps {
	// 	rdw.MapRankingPerScore[m] = rdw.MapRankingPerScore[m][:0]
	// 	rdw.MapRankingPerBestRaceTime[m] = rdw.MapRankingPerBestRaceTime[m][:0]
	// 	rdw.MapRankingPerBestLapTime[m] = rdw.MapRankingPerBestLapTime[m][:0]
	// }

	// rdw.RankingPerExperience = make([]*RankingEntry, 0, RankingMaximumSize)
	// rdw.MapRankingPerScore = make(map[string][]*MapRankingEntry)
	// rdw.MapRankingPerBestRaceTime = make(map[string][]*MapRankingEntry)
	// rdw.MapRankingPerBestLapTime = make(map[string][]*MapRankingEntry)

	// for _, m := range rm.GameMaps {
	// 	rdw.MapRankingPerScore[m] = make([]*MapRankingEntry, 0, RankingMaximumSize)
	// 	rdw.MapRankingPerBestRaceTime[m] = make([]*MapRankingEntry, 0, RankingMaximumSize)
	// 	rdw.MapRankingPerBestLapTime[m] = make([]*MapRankingEntry, 0, RankingMaximumSize)
	// }

	// Recorre todas las cuentas y rellena los rankings
	for _, ac := range rm.Accounts {
		acd := ac.(dict)
		rod := dict{}
		if err := json.Unmarshal([]byte(acd["player_readonly_data"].(string)), &rod); err != nil {
			panic(err)
		}

		is_guest := acd["is_guest"].(bool)
		account_id := acd["account_id"].(string)

		var flag_id uint16
		{
			pd := dict{}
			if err := json.Unmarshal([]byte(acd["player_data"].(string)), &pd); err != nil {
				panic(err)
			}

			flag_index := int(pd["flag_index"].(float64))
			if flag_index < 0 {
				flag_id = 0xFFFF
			} else {
				flag_id = uint16(rod["flag_ids"].([]any)[flag_index].(float64))
			}
		}

		display_name := acd["display_name"].(string)

		experience := uint(0)

		if md, ok := rod["maps_data"]; ok {
			for m := range md.(dict) { // Para cada map que este en la cuenta
				if index := slices.IndexFunc(rm.GameMaps, func(name string) bool { return name == m }); index >= 0 { // Si el map esta en rm.GameMaps
					h := md.(dict)[m].([]any)
					for len(h) < 3 {
						h = append(h, 0)
					}

					experience += uint(h[0].(float64))

					mrke := MapRankingEntry{is_guest, account_id, flag_id, display_name, uint(h[0].(float64)), uint(h[1].(float64)), uint(h[2].(float64))}

					// Se inserta en el ranking si tiene mas o igual score que el ultimo que hay en el ranking o si no habia nadie en el ranking.
					if len(rd.MapRankingPerScore[m]) > 0 {
						if experience >= rd.MapRankingPerScore[m][len(rd.MapRankingPerScore[m])-1].MapScore {
							rdw.MapRankingPerScore[m] = append(rdw.MapRankingPerScore[m], mrke)
						}
					} else {
						rdw.MapRankingPerScore[m] = append(rdw.MapRankingPerScore[m], mrke)
					}
					// Se inserta en el ranking si tiene menos o igual BestRaceTime que el ultimo que hay en el ranking o si no habia nadie en el ranking.
					if mrke.MapBestRaceTime > 0 {
						if len(rd.MapRankingPerBestRaceTime[m]) > 0 {
							if mrke.MapBestRaceTime <= rd.MapRankingPerBestRaceTime[m][len(rd.MapRankingPerBestRaceTime[m])-1].MapBestRaceTime {
								rdw.MapRankingPerBestRaceTime[m] = append(rdw.MapRankingPerBestRaceTime[m], mrke)
							}
						} else {
							rdw.MapRankingPerBestRaceTime[m] = append(rdw.MapRankingPerBestRaceTime[m], mrke)
						}
					}
					// Se inserta en el ranking si tiene menos o igual BestLapTime que el ultimo que hay en el ranking o si no habia nadie en el ranking.
					if mrke.MapBestLapTime > 0 {
						if len(rd.MapRankingPerBestLapTime[m]) > 0 {
							if mrke.MapBestLapTime <= rd.MapRankingPerBestLapTime[m][len(rd.MapRankingPerBestLapTime[m])-1].MapBestLapTime {
								rdw.MapRankingPerBestLapTime[m] = append(rdw.MapRankingPerBestLapTime[m], mrke)
							}
						} else {
							rdw.MapRankingPerBestLapTime[m] = append(rdw.MapRankingPerBestLapTime[m], mrke)
						}
					}
				}
			}
		}

		// Se inserta en el ranking si tiene mas o igual experience que el ultimo que hay en el ranking o si no habia nadie en el ranking.
		if len(rd.RankingPerExperience) > 0 {
			if experience >= rd.RankingPerExperience[len(rd.RankingPerExperience)-1].Experience {
				rke := RankingEntry{is_guest, account_id, flag_id, display_name, experience}
				rdw.RankingPerExperience = append(rdw.RankingPerExperience, rke)
			}
		} else {
			rke := RankingEntry{is_guest, account_id, flag_id, display_name, experience}
			rdw.RankingPerExperience = append(rdw.RankingPerExperience, rke)
		}
	}

	// Ordena los rankings
	{
		sort.SliceStable(rdw.RankingPerExperience, func(i, j int) bool { // Ordena por Experience
			return rdw.RankingPerExperience[i].Experience >= rdw.RankingPerExperience[j].Experience
		})

		for _, m := range rdw.MapRankingPerScore { // Para cada mapa, ordena por Score
			sort.SliceStable(m, func(i, j int) bool { return m[i].MapScore >= m[j].MapScore })
		}
		for _, m := range rdw.MapRankingPerBestRaceTime { // Para cada mapa, ordena por BestRaceTime
			sort.SliceStable(m, func(i, j int) bool { return m[i].MapBestRaceTime < m[j].MapBestRaceTime })
		}
		for _, m := range rdw.MapRankingPerBestLapTime { // Para cada mapa, ordena por BestLapTime
			sort.SliceStable(m, func(i, j int) bool { return m[i].MapBestLapTime < m[j].MapBestLapTime })
		}
	}

	// Limita los rankings a RANKING_MAXIMUM_SIZE
	{
		if len(rdw.RankingPerExperience) > RANKING_MAXIMUM_SIZE {
			rdw.RankingPerExperience = rdw.RankingPerExperience[:RANKING_MAXIMUM_SIZE]
		}
		for _, m := range rm.GameMaps {
			if len(rdw.MapRankingPerScore[m]) > RANKING_MAXIMUM_SIZE {
				rdw.MapRankingPerScore[m] = rdw.MapRankingPerScore[m][:RANKING_MAXIMUM_SIZE]
			}
			if len(rdw.MapRankingPerBestRaceTime[m]) > RANKING_MAXIMUM_SIZE {
				rdw.MapRankingPerBestRaceTime[m] = rdw.MapRankingPerBestRaceTime[m][:RANKING_MAXIMUM_SIZE]
			}
			if len(rdw.MapRankingPerBestLapTime[m]) > RANKING_MAXIMUM_SIZE {
				rdw.MapRankingPerBestLapTime[m] = rdw.MapRankingPerBestLapTime[m][:RANKING_MAXIMUM_SIZE]
			}
		}
	}

	// used_display_name_indices_map := map[int]bool{} // Contendra los indices de los display_names que se estan usando en los rankings.

	account_names_map := map[string]int{} // Dado un account_name devuelve un indice en accounts_info_list
	accounts_info_list := [][2]string{}   // Lista con los flag_ids y display_names de cada account.

	raw_ranking_per_experience := [][2]int{} // Cada entrada es una tupla de la forma (display_name_index, experience)

	for _, e := range rdw.RankingPerExperience {
		index, ok := account_names_map[e.AccountId]
		if !ok {
			index = len(accounts_info_list)
			account_names_map[e.AccountId] = index
			accounts_info_list = append(accounts_info_list, [2]string{strconv.Itoa(int(e.FlagId)), e.DisplayName})
		}

		if len(raw_ranking_per_experience) < RANKING_MAXIMUM_SIZE {
			raw_ranking_per_experience = append(raw_ranking_per_experience, [2]int{index, int(e.Experience)})
			// if _, ok := used_display_name_indices_map[index]; !ok {
			// 	used_display_name_indices_map[index] = true
			// }
		} else {
			break
		}
	}

	raw_map_rankings := map[string][][][]int{}
	for _, m := range rm.GameMaps {
		raw_map_rankings[m] = [][][]int{{}, {}, {}} // [[], [], []] Es una lista que contiene 3 listas con entradas de la forma (display_name_index, map_score), (display_name_index, map_best_race_time), (display_name_index, map_best_lap_time) respectivamente.
	}

	for _, m := range rm.GameMaps {
		// map_score
		out := &raw_map_rankings[m][0]
		for _, e := range rdw.MapRankingPerScore[m] {
			index, ok := account_names_map[e.AccountId]
			if !ok {
				index = len(accounts_info_list)
				account_names_map[e.AccountId] = index
				accounts_info_list = append(accounts_info_list, [2]string{strconv.Itoa(int(e.FlagId)), e.DisplayName})
			}

			if len(*out) < RANKING_MAXIMUM_SIZE {
				*out = append(*out, []int{index, int(e.MapScore)})
				// if _, ok := used_display_name_indices_map[index]; !ok {
				// 	used_display_name_indices_map[index] = true
				// }
			} else {
				break
			}
		}

		// map_best_race_time
		out = &raw_map_rankings[m][1]
		for _, e := range rdw.MapRankingPerBestRaceTime[m] {
			index, ok := account_names_map[e.AccountId]
			if !ok {
				index = len(accounts_info_list)
				account_names_map[e.AccountId] = index
				accounts_info_list = append(accounts_info_list, [2]string{strconv.Itoa(int(e.FlagId)), e.DisplayName})
			}

			if len(*out) < RANKING_MAXIMUM_SIZE {
				*out = append(*out, []int{index, int(e.MapBestRaceTime)})
				// if _, ok := used_display_name_indices_map[index]; !ok {
				// 	used_display_name_indices_map[index] = true
				// }
			} else {
				break
			}
		}
		// map_best_lap_time
		out = &raw_map_rankings[m][2]
		for _, e := range rdw.MapRankingPerBestLapTime[m] {
			index, ok := account_names_map[e.AccountId]
			if !ok {
				index = len(accounts_info_list)
				account_names_map[e.AccountId] = index
				accounts_info_list = append(accounts_info_list, [2]string{strconv.Itoa(int(e.FlagId)), e.DisplayName})
			}

			if len(*out) < RANKING_MAXIMUM_SIZE {
				*out = append(*out, []int{index, int(e.MapBestLapTime)})
				// if _, ok := used_display_name_indices_map[index]; !ok {
				// 	used_display_name_indices_map[index] = true
				// }
			} else {
				break
			}
		}
	}

	json_serializable_ranking := dict{
		"accounts":               accounts_info_list,
		"ranking_per_experience": raw_ranking_per_experience,
		"map_rankings":           raw_map_rankings,
	}

	// fmt.Println(json_serializable_ranking)

	bytes, err := json.Marshal(json_serializable_ranking)
	if err != nil {
		panic(err)
	}

	rdw.Content = string(bytes)

	// Publica la nueva version del ranking.
	{
		rm.PrevRankingData = rm.CurrRankingData
		rm.CurrRankingData = rdw
	}

	// Intercambia el doble buffer <rman.RankingData>
	// {
	// 	atomic.StoreUint64(&rm.RankingDataIndex, (rm.RankingDataIndex+1)%2) // Hace que el buffer de escritura se convierta en el de lectura modificando el indice del buffer de lectura.
	// 	// rm.RankingData[(rm.RankingDataIndex+1)%2] = nil                     // Borra el buffer que antes era de lectura.
	// }
}
