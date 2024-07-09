import sys
import json
import time
from utils import generate_random_str
from accounts_cache import AccountsCache

class RankingEntry:
    def __init__(self, account_name, display_name, experience):
        self.account_name = account_name
        self.display_name = display_name
        self.experience = experience

class MapRankingEntry:
    def __init__(self, account_name, display_name, map_score, map_best_race_time, map_best_lap_time):
        self.account_name = account_name
        self.display_name = display_name
        self.map_score = map_score
        self.map_best_race_time = map_best_race_time
        self.map_best_lap_time = map_best_lap_time

#
# En los rankings solo se tienen en cuenta las cuentas registradas, las cuentas guest no se tienen en cuenta.
# Los rankings que hay son:
#       - Ranking global por <experience> (la experience es la suma total de los points en todos los maps)
#       - Para cada map, ranking global por <points>
#
class Ranking:

    UPDATE_INTERVAL = 10.0 # Tiempo minimo entre actualizaciones del ranking, en segundos.

    RANKING_SIZE = 100 # Numero maximo de entradas en cada uno de los rankings.

    def __init__(self, accounts_cache, game_maps):
        self.accounts_cache = accounts_cache
        self.json_serializable_ranking = None
        self.last_update_time = 0
        self.game_maps = list(game_maps)
        self.ranking_version = None

        self.ranking_per_experience = []
        self.map_ranking_per_score = {}
        self.map_ranking_per_best_race_time = {}
        self.map_ranking_per_best_lap_time = {}

        self._initialize()

    def _initialize(self):
        self.update_ranking()

    def get_account_positions(self, account_name):
        account_positions = [0, {}]
        for m in self.game_maps:
            account_positions[1][m] = [0, 0, 0] # [position by score, position by best_race_time, position by best_lap_time]

        position = 1
        for x in self.ranking_per_experience:
            if x.account_name == account_name:
                account_positions[0] = position
                break
            position += 1

        for m in self.game_maps:
            v = account_positions[1][m]

            position = 1
            for x in self.map_ranking_per_score[m]:
                if x.account_name == account_name:
                    v[0] = position
                    break
                position += 1

            position = 1
            for x in self.map_ranking_per_best_race_time[m]:
                if x.account_name == account_name:
                    v[1] = position
                    break
                position += 1

            position = 1
            for x in self.map_ranking_per_best_lap_time[m]:
                if x.account_name == account_name:
                    v[2] = position
                    break
                position += 1

        return account_positions

    def update_ranking(self):
        print(self.game_maps)

        now = time.monotonic()

        if (now - self.last_update_time) > Ranking.UPDATE_INTERVAL:
            self.last_update_time = now
            self.ranking_version = generate_random_str(8)
        else:
            return
        
        accounts = self.accounts_cache.accounts

        self.ranking_per_experience.clear()
        self.map_ranking_per_score.clear()
        for m in self.game_maps:
            self.map_ranking_per_score[m] = []
            self.map_ranking_per_best_race_time[m] = []
            self.map_ranking_per_best_lap_time[m] = []

        for _key, ac in accounts.items():
            rod = json.loads(ac['player_readonly_data'])

            account_name = ac['account_name']
            display_name = ac['display_name']

            experience = 0

            if 'maps_data' in rod:
                for m in rod['maps_data']: # Para cada map que este en la cuenta
                    if m in self.game_maps: # Si el map esta en self.game_maps
                        h = rod['maps_data'][m]
                        while len(h) < 3:
                            h.append(0)

                        experience += h[0]

                        mrke = MapRankingEntry(account_name, display_name, h[0], h[1], h[2])
                        self.map_ranking_per_score[m].append(mrke) # Inserta la cuenta en el ranking del map
                        self.map_ranking_per_best_race_time[m].append(mrke)
                        self.map_ranking_per_best_lap_time[m].append(mrke)

            rke = RankingEntry(account_name, display_name, experience)
            self.ranking_per_experience.append(rke)

        self.ranking_per_experience = sorted(self.ranking_per_experience, key=lambda x: x.experience, reverse=True)
        
        for k, v in self.map_ranking_per_score.items():
            self.map_ranking_per_score[k] = sorted(v, key=lambda x: x.map_score, reverse=True)
        for k, v in self.map_ranking_per_best_race_time.items():
            self.map_ranking_per_best_race_time[k] = sorted(v, key=lambda x: x.map_best_race_time)
        for k, v in self.map_ranking_per_best_lap_time.items():
            self.map_ranking_per_best_lap_time[k] = sorted(v, key=lambda x: x.map_best_lap_time)

        used_display_name_indices_map = {} # Contendra los indices de los display_names que se estan usando en los rankings.

        account_names_map = {} # Dado un account_name devuelve un indice en accounts_info_list
        accounts_info_list = [] # Lista con los display_names de cada account.
        
        raw_ranking_per_experience = [] # Cada entrada es una tupla de la forma (display_name_index, experience)

        for e in self.ranking_per_experience:
            index = account_names_map.get(e.account_name, None)
            if index is None:
                index = len(accounts_info_list)
                account_names_map[e.account_name] = index
                accounts_info_list.append(e.display_name)

            if len(raw_ranking_per_experience) < Ranking.RANKING_SIZE:
                raw_ranking_per_experience.append((index, e.experience))
                if index not in used_display_name_indices_map:
                    used_display_name_indices_map[index] = True
            else:
                break

        raw_map_rankings = {}
        for m in self.game_maps:
            raw_map_rankings[m] = [[], [], []] # Es una lista que contiene 3 listas con entradas de la forma (display_name_index, map_score), (display_name_index, map_best_race_time), (display_name_index, map_best_lap_time) respectivamente.

        for m in self.game_maps:
            # map_score
            out = raw_map_rankings[m][0]
            for e in self.map_ranking_per_score[m]:
                index = account_names_map.get(e.account_name, None)
                if index is None:
                    index = len(accounts_info_list)
                    account_names_map[e.account_name] = index
                    accounts_info_list.append(e.display_name)

                if len(out) < Ranking.RANKING_SIZE:
                    out.append((index, e.map_score))
                    if index not in used_display_name_indices_map:
                        used_display_name_indices_map[index] = True
                else:
                    break
            # map_best_race_time
            out = raw_map_rankings[m][1]
            for e in self.map_ranking_per_best_race_time[m]:
                index = account_names_map.get(e.account_name, None)
                if index is None:
                    index = len(accounts_info_list)
                    account_names_map[e.account_name] = index
                    accounts_info_list.append(e.display_name)

                if len(out) < Ranking.RANKING_SIZE:
                    out.append((index, e.map_best_race_time))
                    if index not in used_display_name_indices_map:
                        used_display_name_indices_map[index] = True
                else:
                    break
            # map_best_lap_time
            out = raw_map_rankings[m][2]
            for e in self.map_ranking_per_best_lap_time[m]:
                index = account_names_map.get(e.account_name, None)
                if index is None:
                    index = len(accounts_info_list)
                    account_names_map[e.account_name] = index
                    accounts_info_list.append(e.display_name)

                if len(out) < Ranking.RANKING_SIZE:
                    out.append((index, e.map_best_lap_time))
                    if index not in used_display_name_indices_map:
                        used_display_name_indices_map[index] = True
                else:
                    break

        self.json_serializable_ranking = {
            'accounts': accounts_info_list,
            'ranking_per_experience': raw_ranking_per_experience,
            'map_rankings': raw_map_rankings
        }

        print(self.json_serializable_ranking)

        # print([json.dumps(x.__dict__) for x in self.ranking_per_experience])
        # for e, v in self.ranking_per_map.items():
        #     print('Map[', e, ']: ', [json.dumps(x.__dict__) for x in v])


        # self.json_serializable_ranking = {'accounts': [json.dumps(x.__dict__) for x in self.sorted_list]}
        

        # query = {"account_name" : {'$exists' : True}}
        # projection = 'account_name display_name player_readonly_data'

        # response = self.database.sync_read_accounts(query, projection)
        # if response is None:
        #     return

        # # print("Accounts: ", len(response['accounts']))

        # self.sorted_list.clear()

        # for ra in response['accounts']:
        #     rke = RankingEntry(json.loads(ra['player_readonly_data'])['experience'], ra['account_name'], ra['display_name'])
        #     bisect.insort(self.sorted_list, rke)

        # self.json_serializable_ranking = {'accounts': [json.dumps(x.__dict__) for x in self.sorted_list]}

        # # print([[x.account_name, x.display_name, x.experience] for x in self.sorted_list])

    def handle_notify_game_terminated(self, map_name, accounts):
        pass

    # def on_account_player_experience_changed(self, account_name, experience):
    #     pos = next((i for i, x in enumerate(self.sorted_list) if x.account_name == account_name), -1)
    #     if pos >= 0:
    #         entry = self.sorted_list[pos]
    #         self.sorted_list.pop(pos)
    #         entry.experience = experience
    #         bisect.insort(entry)

    #     self.json_serializable_ranking = {'accounts': [json.dumps(x.__dict__) for x in self.sorted_list]}

################# TEST #################


if __name__ == "__main__":
    port = 8004
    # El primer argumento es el puerto.
    for arg in sys.argv[1:]:
        port = int(arg)
        # print(arg)
        break    

    acche = AccountsCache('http://127.0.0.1:{}'.format(port))
    rkn = Ranking(acche, [])
    
    








