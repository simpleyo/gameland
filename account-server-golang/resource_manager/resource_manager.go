package resource_manager

import (
	"crypto/md5"
	"encoding/json"
	"errors"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"

	"golang.org/x/exp/slices"
)

var resourceManager = ResourceManager{
	ResourceServerPath: "../resource-server",
	Resources:          dict{},
	Games:              dict{},
}

type dict = map[string]any

type Resource struct {
	RootPathParts []string
	FilePath      string
	Md5           string
}

func getDictValueAs[T any](theDict map[string]any, name string) (result T, valid bool) {
	valid = false
	if v, ok := theDict[name]; ok {
		if result, ok = v.(T); ok {
			valid = true
		}
	}
	return
}

func (r *Resource) UpdateResource() {
	content, err := ioutil.ReadFile(r.FilePath)
	if err != nil {
		panic(err)
	}

	if len(content) == 0 {
		r.Md5 = ""
	} else {
		r.Md5 = Md5ToHexString(md5.Sum(content))
	}
}

type ResourceManager struct {
	ResourceServerPath string
	Resources          dict
	Games              dict
}

func Initialize(resource_server_dir string) {
	if resource_server_dir != "" {
		resourceManager.ResourceServerPath = resource_server_dir
	}
	updateResources()
	updateGames()
}

func GetGame(gameName string) dict {
	if game, ok := resourceManager.Games[gameName]; ok {
		return game.(dict)
	}
	return dict{}
}

func GetGameParameters(gameName string) dict {
	if game, ok := resourceManager.Games[gameName]; ok {
		if v, ok := game.(dict)["GAME_PARAMETERS"]; ok {
			return v.(dict)
		}
	}
	return dict{}
}

func GetGameResources(gameName string) dict {
	if game, ok := resourceManager.Games[gameName]; ok {
		if v, ok := game.(dict)["GAME_RESOURCES"]; ok {
			return v.(dict)
		}
	}
	return dict{}
}

func GetGameExistingMaps(gameName string) dict {
	if game, ok := resourceManager.Games[gameName]; ok {
		if v, ok := game.(dict)["GAME_MAPS"]; ok {
			return v.(dict)
		}
	}
	return dict{}
}

func GetGameEnabledMaps(gameName string) []any {
	if game, ok := resourceManager.Games[gameName]; ok {
		if v, ok := game.(dict)["ENABLED_MAPS"]; ok {
			return v.([]any)
		}
	}
	return []any{}
}

func GetGameClientResourcesMd5(gameName string) string {
	if game, ok := resourceManager.Games[gameName]; ok {
		if v, ok := game.(dict)["GAME_CLIENT_RESOURCES_MD5"]; ok {
			return v.(string)
		}
	}
	return ""
}

func GetGameClientResources(gameName string) []string {
	gameResources := GetGameResources(gameName)
	gameClientResources := make([]string, 0, 64)
	for k, v := range gameResources {
		if vv, ok := v.(dict); ok {
			if client, ok := getDictValueAs[bool](vv, "client"); ok {
				if client {
					gameClientResources = append(gameClientResources, k)
				}
			}
		} else {
			panic(0)
		}
	}
	return gameClientResources
}

// def get_game_client_resources(self, game_name):
// game_resources = self.get_game_resources(game_name)
// game_client_resources = [k for k, v in game_resources.items()
// 						 if 'client' in v and v['client']]
// return game_client_resources

// Retorna err distinto de nil si el resource no existe.
// Retorna outResourceMd5 != nil y result == nil si el resource existe pero tiene el mismo md5 que el proporcionado.
// Retorna outResourceMd5 != nil y result != nil si el resource existe y tiene distinto md5
// que el proporcionado. """
func GetResource(gameName string, resourcePath string, resourceMd5 string) (result []byte, outResourceMd5 string, err error) {

	rootDir := resourceManager.ResourceServerPath + "/root"
	filePath := rootDir + "/games/" + gameName + "/" + resourcePath

	p := strings.Split(filePath, "/") // Partes del path.

	var root_path_parts []string
	index := slices.IndexFunc(p, func(name string) bool { return name == "root" })
	if index >= 0 {
		root_path_parts = p[index+1:]
	} else {
		err = errors.New("root not found")
		return
	}

	var od any
	od = resourceManager.Resources
	for _, x := range root_path_parts {
		if dod, ok := od.(dict); ok {
			if v, ok := dod[x]; ok {
				od = v
			} else {
				err = errors.New("not found")
				return
			}
		} else {
			break
		}
	}

	if od == nil {
		panic(0)
	}

	res := od.(Resource)
	outResourceMd5 = res.Md5

	if res.Md5 != resourceMd5 {
		result, err = ioutil.ReadFile(filePath)
		if err != nil {
			result = nil
			return
		}
	}

	return
}

// Retorna error si algunos de los resources no existe.
// Retorna md5_str si todo ha ido correctamente.
// resource_path_list: es una lista de resource_path a partir
// de la cual se calcula su md5.
func CalculateResourcesMd5(gameName string, resourcePathList []string) (resMd5 string, err error) {

	// https://stackoverflow.com/questions/24234322/golang-md5-sum-function

	md5Bytes := make([]byte, 0, 16)
	m := md5.New()

	for _, resPath := range resourcePathList {
		badMd5 := ""
		var result []byte
		result, _, err = GetResource(gameName, resPath, badMd5)
		if err != nil {
			return
		}
		if result == nil {
			err = errors.New("ERROR: " + resPath)
			return
		}

		m.Write(result)
	}

	md5Bytes = m.Sum(nil)

	resMd5 = ""
	if md5Bytes != nil {
		resMd5 = Md5ToHexString(*(*[16]byte)(md5Bytes))
	}

	return
}

// def calculate_resources_md5(self, game_name, resource_path_list):
// """ Retorna {'error': 'Resource not found.'} si algunos de los resources no existe.
// Retorna md5_str si todo ha ido correctamente.
// resource_path_list: es una lista de resource_path a partir
// de la cual se calcula su md5. """

// m = hashlib.md5()
// for resource_path in resource_path_list:
// 	bad_md5 = ""
// 	result = self.get_resource(game_name, resource_path, bad_md5)
// 	if 'error' in result:
// 		return result
// 	if 'resource_data' not in result:
// 		return {'error': 'Resource not found.'}

// 	m.update(result['resource_data'])

// return m.hexdigest().lower()

func updateResources() {
	// Reconstruye self.resources. Esto supone recalcular
	// el md5 de todos los resources.

	rootDir := resourceManager.ResourceServerPath + "/root"

	supportedFiles := []string{".cfg", ".json", ".png"}

	fileList := []string{}

	// Retorna en fileList una lista con todos los paths de los ficheros, no directorios.
	filepath.Walk(rootDir,
		func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}
			if !info.IsDir() {
				if slices.IndexFunc(supportedFiles, func(name string) bool { return filepath.Ext(info.Name()) == name }) >= 0 {
					fileList = append(fileList, filepath.ToSlash(path))
					// fmt.Println(path, info.Size())
				}
			}
			return nil
		})

	newResources := dict{}

	// Recorre recursivamente todos los ficheros que hay en rootdir.
	// Para cada fichero va rellenado new_resources con la informacion
	// apropiada.
	for _, f := range fileList {
		p := strings.Split(f, "/") // Partes del path.

		rootIndex := slices.IndexFunc(p, func(name string) bool { return name == "root" })

		d := newResources

		for i := rootIndex + 1; i < len(p); i++ {
			name := p[i]
			if _, ok := d[name]; !ok { // If not name in d
				if i == len(p)-1 {
					_updateResource(d, p[rootIndex+1:], f)
				} else {
					d[name] = dict{}
				}
			}

			if i < len(p)-1 {
				d = d[name].(dict)
			}
		}
	}

	resourceManager.Resources = newResources
}

// _updateResource Busca al resource identificado por root_path_parts en el
// resourceManager.Resources y en caso de que exista entonces utiliza ese objeto Resource para insertarlo en dest.
// En caso de que no exista se crea un nuevo objeto Resource. En ambos casos se recalcula el md5 del resource.
// dest: es el dict que contendra a este resource.
// root_path_parts: son las partes del path del resource desde el directorio root.
// flie_path: es un objeto Path que define el path completo del resource.
func _updateResource(dest dict, root_path_parts []string, file_path string) {

	var od any = resourceManager.Resources
	for _, rootPart := range root_path_parts {
		if smap, ok := od.(dict); ok {
			od = smap
			if v, ok := smap[rootPart]; ok {
				od = v
			} else {
				od = nil
				break
			}
		} else {
			// od debe ser del tipo Resource aqui.
			if _, ok := od.(Resource); !ok {
				panic(0)
			}
			od = nil
			break
		}
	}

	name := root_path_parts[len(root_path_parts)-1]

	if od == nil {
		res := Resource{
			RootPathParts: root_path_parts,
			FilePath:      file_path,
			Md5:           "",
		}
		res.UpdateResource()
		dest[name] = res
		// print(hashmd5(file_path.read_bytes()))
	} else {
		// El resource ya existe.
		print("El resource ya existe.")

		if res, ok := od.(Resource); ok {
			res.UpdateResource()
			dest[name] = res
		} else {
			panic(0)
		}
	}
}

// UpdateGames reconstruye ResourceManager.Games.
// Esta funcion asume que los ficheros con nombre 'game.cfg' representan
// la configuracion de un game.
func updateGames() {

	rootDir := resourceManager.ResourceServerPath + "/root"

	fileList := []string{}

	// Retorna en fileList una lista con todos los paths de los ficheros, no directorios.
	filepath.Walk(rootDir,
		func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}
			if !info.IsDir() && info.Name() == "game.cfg" {
				fileList = append(fileList, filepath.ToSlash(path))
			}
			return nil
		})

	newGames := dict{}

	// Recorre todos los ficheros de file_list.
	// Para cada fichero va rellenado newGames con la informacion
	// apropiada.
	for _, f := range fileList {
		content, err := ioutil.ReadFile(f)
		if err != nil {
			panic(err)
		}

		var gameConfig dict
		err = json.Unmarshal(content, &gameConfig)
		if err != nil {
			panic(err)
		}

		d := newGames
		if _, ok := gameConfig["GAME_NAME"]; !ok {
			continue
		}
		if _, ok := gameConfig["GAME_RESOURCES"]; !ok {
			continue
		}

		gameConfig["GAME_MAPS"] = dict{}

		gameName := gameConfig["GAME_NAME"].(string)

		d[gameName] = gameConfig
	}

	// fmt.Println("newGames: ", newGames)

	resourceManager.Games = newGames

	updateGameMaps()

	// Para todos los games, calcula el MD5 de su client_resources
	{
		for gameName, game := range resourceManager.Games {
			gameClientResources := []string{}
			failed := true
			if tgame, ok := game.(dict); ok {
				if gameResources, ok := getDictValueAs[dict](tgame, "GAME_RESOURCES"); ok {
					for k, v := range gameResources {
						if vv, ok := v.(dict); ok {
							failed = false
							if client, ok := getDictValueAs[bool](vv, "client"); ok {
								if client {
									gameClientResources = append(gameClientResources, k)
								}
							}
						} else {
							panic(0)
						}
					}
				}

				// Calcula el md5 de los gameClientResources.
				gameClientResourcesMd5, err := CalculateResourcesMd5(gameName, gameClientResources)
				if err != nil {
					panic(0)
				}

				tgame["GAME_CLIENT_RESOURCES_MD5"] = gameClientResourcesMd5
			}
			if failed {
				panic(0)
			}
		}
	}
}

// updateGameMaps reconstruye ResourceManager.GameMaps. Esto supone recalcular
// el md5 de todos los resources de los game maps.
func updateGameMaps() {

	rootDir := resourceManager.ResourceServerPath + "/root"

	fileList := []string{}

	// Retorna en fileList una lista con todos los paths de los ficheros, no directorios.
	filepath.Walk(rootDir,
		func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}
			if !info.IsDir() && info.Name() == "map.cfg" {
				fileList = append(fileList, filepath.ToSlash(path))
			}
			return nil
		})

	// Recorre todos los ficheros de file_list.
	// Para cada fichero va rellenado newGameMaps con la informacion
	// apropiada.
	for _, f := range fileList {
		content, err := ioutil.ReadFile(f)
		if err != nil {
			panic(err)
		}

		var mapConfig dict
		err = json.Unmarshal(content, &mapConfig)
		if err != nil {
			panic(err)
		}

		if _, ok := mapConfig["GAME_NAME"]; !ok {
			continue
		}
		if _, ok := mapConfig["MAP_NAME"]; !ok {
			continue
		}
		if _, ok := mapConfig["MAP_RESOURCES"]; !ok {
			continue
		}

		gameName := mapConfig["GAME_NAME"].(string)

		if _, ok := resourceManager.Games[gameName]; !ok {
			continue
		}

		d := resourceManager.Games[gameName].(dict)

		if _, ok := d["GAME_MAPS"]; !ok {
			continue
		}

		d = d["GAME_MAPS"].(dict)

		mapName := mapConfig["MAP_NAME"].(string)
		mapResources := mapConfig["MAP_RESOURCES"]

		d[mapName] = dict{"MAP_RESOURCES": mapResources}
	}

	// fmt.Println("resourceManager.Games: ", resourceManager.Games)
}
