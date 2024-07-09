import json
import asyncio
from datetime import datetime, timedelta
from utils import generate_random_str, date_to_str, str_to_date
from account_database import Database

class AccountsCache:

    ACCOUNT_PROJECTION = 'account_info display_name player_data player_readonly_data guest_account_id account_name email email_validated creation_time session_id session_expire account_salt account_hash'
    SESSION_EXPIRE_TIME = 180 # En dias. Tiempo que tarda en expirar una sesion desde que se hizo login.
    
    def __init__(self, xmlrpc_server_url):
        self.database = Database(xmlrpc_server_url)
        self.accounts = {} # indexado por account_name. Contiene solo las cuentas que tienen account_name.
        self.accounts_by_guest_account_id = {} # indexado por guest_account_id. Contiene solo las cuentas que tienen guest_account_id.
        self.accounts_by_session_id = {} # indexado por session_id. Contiene todas las cuentas ya que todas tienen session_id.

        self._initialize()

    def _initialize(self):
        # query = {"account_name" : {'$exists' : True}}
        # projection = 'account_name display_name player_data player_readonly_data creation_time session_id session_expire account_info email email_validated account_salt account_hash'

        query = {}
        r = self.database.sync_read_accounts(query, AccountsCache.ACCOUNT_PROJECTION)
        if r is None:
            return

        for entry in r['accounts']:
            new_account = {}
            for key in AccountsCache.ACCOUNT_PROJECTION.split():
                if key in entry:
                    value = entry[key]
                    new_account[key] = value
                    if key == 'guest_account_id':
                        self.accounts_by_guest_account_id[value] = new_account
                    elif key == 'session_id':
                        self.accounts_by_session_id[value] = new_account
                    elif key == 'account_name':
                        self.accounts[value] = new_account

        print("Accounts: ", len(self.accounts), len(self.accounts_by_guest_account_id), len(self.accounts_by_session_id))

        # self.json_serializable_ranking = {'accounts': [json.dumps(x.__dict__) for x in self.sorted_list]}

        # print([[x.account_name, x.display_name, x.experience] for x in self.sorted_list])
        #        

    # def get_account(self, account_name):
    #     return self.accounts.get(account_name, None)

    # Crea una cuenta de guest y devuelve la respuesta como objeto json.
    # Si la cuenta ya existe no hace nada.
    # A las cuentas guest no les afecta el <session_expire>.
    # Devuelve None si ha habido algun error. En ese caso envia el mensaje de error al cliente antes de retornar None.
    async def create_guest_account(self, rq, ws, send_message):

        guest_account_id = rq['guest_account_id']
        if not guest_account_id in self.accounts_by_guest_account_id:
            rq['creation_time'] = date_to_str(datetime.now())
            rq['session_id'] = generate_random_str(32)
            rq['session_expire'] = date_to_str(datetime.now())  # No se usa.

            r = await self.database.create_guest_account(rq, ws, send_message)
            if r is None:
                return

            guest_account = {}
        else:
            guest_account = self.accounts_by_guest_account_id[guest_account_id]
            r = guest_account

        response = {}
        for key in AccountsCache.ACCOUNT_PROJECTION.split():
            if key in r:
                value = r[key]
                response[key] = value
                guest_account[key] = value
                if key == 'guest_account_id':
                    # assert(not value in self.accounts_by_guest_account_id)
                    self.accounts_by_guest_account_id[value] = guest_account
                elif key == 'session_id':
                    # assert(not value in self.accounts_by_session_id)
                    self.accounts_by_session_id[value] = guest_account
                elif key == 'account_name':
                    assert(False)

        print("Response: ", response)
        return response

    # Crea una cuenta y devuelve la respuesta como objeto json.
    # Devuelve None si ha habido algun error. En ese caso envia el mensaje de error al cliente antes de retornar None.
    async def create_account(self, rq, ws, send_message, projection=ACCOUNT_PROJECTION):

        account_name = rq['account_name']
        if not account_name in self.accounts:
            rq['creation_time'] = date_to_str(datetime.now())
            rq['session_id'] = generate_random_str(32)
            rq['session_expire'] = date_to_str(datetime.now() + timedelta(days=AccountsCache.SESSION_EXPIRE_TIME))

            r = await self.database.create_account(rq, ws, send_message, projection)
            if r is None:
                return

            account = {}
        else:
            account = self.accounts[account_name]
            r = account

        for key in AccountsCache.ACCOUNT_PROJECTION.split():
            if key in r:
                value = r[key]
                account[key] = value
                if key == 'guest_account_id':
                    assert(False)
                elif key == 'session_id':
                    # assert(not value in self.accounts_by_session_id)
                    self.accounts_by_session_id[value] = account
                elif key == 'account_name':
                    # assert(not value in self.accounts)
                    self.accounts[value] = account
        
        response = {}
        for key in projection.split():
            if key in account:
                response[key] = account[key]

        print("Response: ", response)
        return response

    # Obtiene informacion de una cuenta y devuelve la respuesta como objeto json. Tambien permite
    # comprobar si una cuenta existe.
    # Devuelve {} si no se ha encontrado la cuenta especificada.
    # Devuelve None si ha habido algun error. En ese caso envia el mensaje de error al cliente antes de retornar None.
    #   ATENCION: Esta funcion nunca debe fallar asi que no se necesita enviar nada al cliente.
    async def read_account(self, _rq, _ws, _send_message, query, projection=ACCOUNT_PROJECTION):
        if 'account_name' in query:
            value = query['account_name']
            account = self.accounts.get(value, None)
        elif 'session_id' in query:
            value = query['session_id']
            account = self.accounts_by_session_id.get(value, None)
        elif 'guest_account_id' in query:
            value = query['guest_account_id']
            account = self.accounts_by_guest_account_id.get(value, None)
        else:
            assert(False)

        response = {}
        if account is not None:
            for key in projection.split():
                if key in account:
                    response[key] = account[key]

        print("Response: ", response)
        return response

    # Modifica informacion de una cuenta y devuelve la respuesta como objeto json.
    # La no existencia de la cuenta es considerada como un error.
    # Devuelve None si ha habido algun error. En ese caso envia el mensaje de error al cliente antes de retornar None.
    # No permite la insercion de nuevas keys en la account.
    async def update_account(self, rq, ws, send_message, query, update, projection=ACCOUNT_PROJECTION):
        r = await self.database.update_account(rq, ws, send_message, query, update, AccountsCache.ACCOUNT_PROJECTION)
        if r is None:
            return

        if 'account_name' in query:
            value = query['account_name']
            account = self.accounts.get(value, None)
            assert(account['account_name'] == r['account_name'])
        elif 'session_id' in query:
            value = query['session_id']
            account = self.accounts_by_session_id.get(value, None)
            assert(account['session_id'] == r['session_id'])
        elif 'guest_account_id' in query:
            value = query['guest_account_id']
            account = self.accounts_by_guest_account_id.get(value, None)
            assert(account['guest_account_id'] == r['guest_account_id'])
        else:
            assert(False)

        assert(account is not None)

        for key in AccountsCache.ACCOUNT_PROJECTION.split():
            if key in r:
                if key in account:
                    account[key] = r[key]

        response = {}
        for key in projection.split():
            if key in r:
                response[key] = r[key]

        print("Response: ", response)
        return response


async def idle_task():
    while True:
        pass
        # await cache.create_guest_account({'request_id': '0', 'guest_account_id': 'jks1dghjfgsgadfdhvjv'}, None, None)
        # await cache.create_account({'request_id': '0', 'account_name': 'ttt123457', 'key_hash': '121', 'display_name': 'dn'}, None, None, '')
        # await cache.read_account({'request_id': '0'}, None, None, {'account_name': 'ttt123457'}, 'display_name')
        # await cache.update_account({'request_id': '0'}, None, None, {'guest_account_id': 'jks1dghjfgsgadfdhvjv'},  {'display_name': 'ttt1'}, 'display_name')

if __name__ == "__main__":

    XMLRPC_SERVER_URL = 'http://127.0.0.1:8004'

    cache = AccountsCache(XMLRPC_SERVER_URL)
    
    asyncio.get_event_loop().create_task(idle_task())
    asyncio.get_event_loop().run_forever()








