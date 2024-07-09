from distutils import extension
from pathlib import Path
import os
import hashlib
import sys
import json
from base64 import b64encode, b64decode
from utils import hashmd5


class Importer:

    def __init__(self, file_extension):
        self.file_extension = file_extension

class CircuitImporter(Importer):
    
    def __init__(self, file_extension):
        super().__init__(file_extension)
        

class Resource:

    def __init__(self, root_path_parts, file_path):
        self.root_path_parts = root_path_parts
        self.file_path = file_path
        self.md5 = hashmd5(file_path.read_bytes())

        if file_path.suffix:
            print("File extension: <" + file_path.suffix[1:] + ">")

    def update_resource(self):
        self.md5 = hashmd5(self.file_path.read_bytes())

    def __repr__(self):
        return '<Resource: ' + str(self.root_path_parts[-1] + '>')

class CustomFlagManager:

    def __init__(self, resource_server_path):
        self.resource_server_path = resource_server_path
        self.resources = {}
        self.importers = {}
        self.games = {}
        # self.game_maps = {}

        self._update_resources()
        self._update_games()

    

    def get_resource(self, game_name, resource_path, resource_md5):
        """ Retorna {'error': 'Resource not found.'} si el resource no existe.
            Retorna {'resource_md5': md5_str} si el resource existe pero tiene el mismo md5 que el proporcionado.
            Retorna {'resource_md5': md5_str, 'resource_data': <bytes>} si el resource existe y tiene distinto md5
            que el proporcionado. """

        rootdir = Path(self.resource_server_path) / 'root'
        file_path = rootdir / 'games' / game_name / resource_path

        p = file_path.parts
        root_path_parts = p[p.index('root')+1:]

        od = self.resources
        for x in root_path_parts:
            if x in od:
                od = od[x]
            else:
                od = None
                break

        response = {}

        if od:
            response['resource_md5'] = od.md5
            
            if od.md5 != resource_md5:
                response['resource_data'] = od.file_path.read_bytes()
                # response['resource_data'] = b64encode(od.file_path.read_bytes()).decode('utf-8')

        else:
            # Aqui se podria mirar si el resource existe en versiones anteriores.
            response['error'] = 'Resource not found.'
            
        return response

    def calculate_resources_md5(self, game_name, resource_path_list):
        """ Retorna {'error': 'Resource not found.'} si algunos de los resources no existe.
        Retorna md5_str si todo ha ido correctamente.
        resource_path_list: es una lista de resource_path a partir
        de la cual se calcula su md5. """

        m = hashlib.md5()
        for resource_path in resource_path_list:
            bad_md5 = ""
            result = self.get_resource(game_name, resource_path, bad_md5)
            if 'error' in result:
                return result
            if 'resource_data' not in result:
                return {'error': 'Resource not found.'}

            m.update(result['resource_data'])
        
        return m.hexdigest().lower()

    def get_game_client_resources(self, game_name):
        game_resources = self.get_game_resources(game_name)
        game_client_resources = [k for k, v in game_resources.items()
                                 if 'client' in v and v['client']]
        return game_client_resources

    def get_game_client_resources_md5(self, game_name):
        if game_name in self.games:
            game = self.games[game_name]
            if not 'GAME_CLIENT_RESOURCES_MD5' in game:
                return ""
            return game['GAME_CLIENT_RESOURCES_MD5']
        else:
            return ""

    def get_game_resources(self, game_name):
        if game_name in self.games:
            game = self.games[game_name]
            if not 'GAME_RESOURCES' in game:
                return {}
            return game['GAME_RESOURCES']
        else:
            return {}

    def get_game_maps(self, game_name):
        if game_name in self.games:
            game = self.games[game_name]
            if not 'GAME_MAPS' in game:
                return {}
            return game['GAME_MAPS']
        else:
            return {}

    def save_resource(self, game_name, resource_file_name, resource_data):
        pass

    def _update_games(self):
        """ Reconstruye self.games.
        Esta funcion asume que los ficheros con nombre 'game.cfg' representan
        la configuracion de un game."""

        rootdir = Path(self.resource_server_path) / 'root'

        # Return a list of regular files only, not directories
        file_list = [f for f in rootdir.rglob('game.cfg') if f.is_file()]

        new_games = {}

        # Recorre todos los ficheros de file_list.
        # Para cada fichero va rellenado new_games con la informacion
        # apropiada.
        for f in file_list:
            game_config = json.loads(f.read_bytes())
            d = new_games
            
            if not 'GAME_NAME' in game_config:
                continue
            if not 'GAME_RESOURCES' in game_config:
                continue

            game_config['GAME_MAPS'] = {}

            game_name = game_config['GAME_NAME']

            d[game_name] = game_config

            # d = d[game_name]
            
            # game_client_resources = [k for k, v in d['GAME_RESOURCES'].items()
            #                          if 'client' in v and v['client']]

            # # Calcula el md5 de los game_client_resources.
            # game_client_resources_md5 = self.calculate_resources_md5(game_name, game_client_resources)
            # if not isinstance(game_client_resources_md5, str):
            #     print("Error al calcular el md5 de los resources del juego <" + game_name + ">")
            #     game_client_resources_md5 = ""

            # d['GAME_CLIENT_RESOURCES_MD5'] = game_client_resources_md5

            # d['_CLIENT_RESOURCES'] = [k for k, v in d['GAME_RESOURCES'].items()
            #                               if 'client' in v and v['client']]
            # d['_SERVER_RESOURCES'] = list(d['GAME_RESOURCES'].keys())

        print(new_games, "\n\n\n")

        self.games = new_games

        self._update_game_maps()

        # Para todos los games calcula el MD5 de su client_resources
        for _game_name, game in self.games.items():
            game_client_resources = [k for k, v in game['GAME_RESOURCES'].items()
                                     if 'client' in v and v['client']]            

            # Calcula el md5 de los game_client_resources.
            game_client_resources_md5 = self.calculate_resources_md5(game_name, game_client_resources)
            if not isinstance(game_client_resources_md5, str):
                print("Error al calcular el md5 de los resources del juego <" + game_name + ">")
                game_client_resources_md5 = ""

            game['GAME_CLIENT_RESOURCES_MD5'] = game_client_resources_md5

            # game['_CLIENT_RESOURCES'] = [k for k, v in d['GAME_RESOURCES'].items()
            #                               if 'client' in v and v['client']]
            # game['_SERVER_RESOURCES'] = list(d['GAME_RESOURCES'].keys())                

    def _update_game_maps(self):
        """ Reconstruye self.game_maps. Esto supone recalcular
        el md5 de todos los resources de los game maps. 
        Esta funcion asume que los ficheros con nombre 'map.cfg' representan
        la configuracion de un game map."""

        rootdir = Path(self.resource_server_path) / 'root'

        # Return a list of regular files only, not directories
        file_list = [f for f in rootdir.rglob('map.cfg') if f.is_file()]

        # new_game_maps = {}

        # Recorre todos los ficheros de file_list.
        # Para cada fichero va rellenado new_game_maps con la informacion
        # apropiada.
        for f in file_list:
            map_config = json.loads(f.read_bytes())
            # d = new_game_maps
            
            if not 'GAME_NAME' in map_config:
                continue
            if not 'MAP_NAME' in map_config:
                continue
            if not 'MAP_RESOURCES' in map_config:
                continue

            game_name = map_config['GAME_NAME']
            if not game_name in self.games:
                continue
            
            d = self.games[game_name]

            if not 'GAME_MAPS' in d:
                continue

            d = d['GAME_MAPS']

            map_name = map_config['MAP_NAME']
            map_resources = map_config['MAP_RESOURCES']
            # map_resources_md5 = self.calculate_resources_md5(game_name, map_resources)

            # if not isinstance(map_resources_md5, str):
            #     print("Error al calcular el md5 de los resources del map <" + map_name + ">")
            #     print("El map <" + map_name + "> sera ignorado.")
            #     continue

            d[map_name] = {
                'MAP_RESOURCES': map_resources}

        print(self.games.keys())
        print('tanks[GAME_MAPS]: ', self.games['tanks']['GAME_MAPS'].keys(), "\n\n\n")

        # FIXME: Esto no se debe realizar aqui.
        # Recorre todos los games y para cada map inserta su map_image.png en el GAME_RESOURCES del game correspondiente.
        # map_image.png se envia a los clientes para por tener una imagen del mapa a la hora de votar.
        # for _game_name, game in self.games.items():
        #     for map_name in game['GAME_MAPS']:
        #         game['GAME_RESOURCES']['maps/' + map_name + '/map_image.png'] = {'client': True}

        # self.game_maps = new_game_maps

    def _update_resources(self):
        """ Reconstruye self.resources. Esto supone recalcular
        el md5 de todos los resources. """

        rootdir = Path(self.resource_server_path) / 'root'

        # Return a list of regular files only, not directories
        file_list = [f for f in rootdir.rglob('*') if f.is_file()]

        new_resources = {}

        supported_files = [".cfg", ".json", ".png"]

        # Recorre recursivamente todos los ficheros que hay en rootdir.
        # Para cada fichero va rellenado new_resources con la informacion
        # apropiada.
        for f in file_list:
            if not f.suffix in supported_files: # Filtra los ficheros con extensiones no consideradas como recursos.
                continue

            p = f.parts # Partes del path.
            root_index = p.index('root')
            d = new_resources

            for i in range(root_index+1, len(p)):
                name = p[i]
                if not name in d:
                    if i == len(p) - 1:
                        self._update_resource(d, p[root_index+1:], f)
                        # d[name] = name
                    else:
                        d[name] = {}
                d = d[name]

        print(new_resources)

        self.resources = new_resources

    def _update_resource(self, dest, root_path_parts, file_path):
        """ Busca al resource identificado por root_path_parts en el
            self.resources y en caso de que exista entonces utiliza
            ese objeto Resource para insertarlo en dest. En caso de que no
            exista se crea un nuevo objeto Resource. En ambos casos se
            recalcula el md5 del resource.
            dest: es el dict que contendra a este resource. 
            root_path_parts: son las partes del path del resource desde
            el directorio root.
            flie_path: es un objeto Path que define el path completo del
            resource."""

        od = self.resources
        for x in root_path_parts:
            if x in od:
                od = od[x]
            else:
                od = None
                break

        name = root_path_parts[-1]

        if od is None:
            dest[name] = Resource(root_path_parts, file_path)
            # print(hashmd5(file_path.read_bytes()))
        else:
            # El resource ya existe.
            print("El resource ya existe.")
            dest[name] = od
            od.update_resource()



        
################# TEST #################


if __name__ == "__main__":

    resource_manager = ResourceManager('../resource-server')

    # print(resource_manager.get_resource('bubble.io', '1', 'h.txt', 'e'))