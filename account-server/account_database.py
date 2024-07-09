import sys
import json
import asyncio
import xmlrpc.client
from utils import hashmd5, generate_random_str
from account_defaults import AccountDefaults

class Database:
    UPGRADE_CODE_SALT = "c1a3c537c4ea6a849b181c4d87beae6f"

    def __init__(self, xmlrpc_server_url):
        self.rpcclient = xmlrpc.client.ServerProxy(xmlrpc_server_url)

    # Crea una cuenta de guest y devuelve la respuesta como objeto json.
    # Devuelve None si ha habido algun error. En ese caso envia el mensaje de error al cliente antes de retornar None.
    async def create_guest_account(self, rq, ws, send_message):

        error_response = {
            "error": "",
            "request_id": rq['request_id']
        }

        query = {
            "guest_account_id": rq["guest_account_id"]
        }
        update = {
            "creation_time": rq["creation_time"],
            "session_id": rq["session_id"],
            "session_expire": rq["session_expire"],
            "guest_account_id": rq["guest_account_id"],
            # "display_name":     rq["display_name"],            
            "account_info": AccountDefaults.ACCOUNT_INFO,
            "player_data": AccountDefaults.PLAYER_DATA,
            "player_readonly_data": AccountDefaults.PLAYER_READONLY_DATA
        }

	# var expire_date = new Date();
	# expire_date.setTime( expire_date.getTime() + 10000 ); // SESSION_EXPIRE_DAYS * 86400000 );

	# p.update.session_id = crypto.randomBytes(16).toString('hex');
	# p.update.session_expire = expire_date;

        display_name = rq['display_name'] if 'display_name' in rq else AccountDefaults.DISPLAY_NAME
        display_name = display_name[:16] # Limita el display name a 16 caracteres unicode.
        update['display_name'] = display_name
                
        options = {'fields': '_id guest_account_id display_name session_id session_expire creation_time player_data player_readonly_data account_info'}
        
        params = {'query': query, 'update': update, 'options': options}

        valid = False
        response_str = None

        try:
            params_str = json.dumps(params)            
            response_str = self.rpcclient.createAccount(params_str) # recibe la respuesta como str
        except xmlrpc.client.Fault as err:
            print(err)
            # print(err.faultCode)
            # print(err.faultString)
            error_response['error'] = err
        except Exception as e:
            print(e)
            error_response['error'] = str(e)

        if response_str is not None:          
            response = json.loads(response_str)    # Convierte la respuesta de str a objeto json
            valid = True

        if valid:
            response["request_id"] = rq['request_id']
            return response
        else:
            await send_message(error_response, ws)  # send error response
            return None


    # Crea una cuenta y devuelve la respuesta como objeto json.
    # Devuelve None si ha habido algun error. En ese caso envia el mensaje de error al cliente antes de retornar None.
    async def create_account(self, rq, ws, send_message, projection):

        error_response = {
            "error": "",
            "request_id": rq['request_id']
        }

        account_salt = generate_random_str(32)
        account_hash = hashmd5(rq["key_hash"] + account_salt)

        display_name = rq["display_name"]
        display_name = display_name[:16] # Limita el display name a 16 caracteres unicode.

        email = rq['email'] if 'email' in rq else ""

        query = {"account_name": rq["account_name"]}
        update = {
            "creation_time": rq["creation_time"],
            "session_id": rq["session_id"],
            "session_expire": rq["session_expire"],

            "account_name": rq["account_name"],
            "display_name": display_name,
            "email": email,
            "email_validated": False,
            "account_salt": account_salt,
            "account_hash": account_hash,
            "account_info": AccountDefaults.ACCOUNT_INFO,
            "player_data": AccountDefaults.PLAYER_DATA,
            "player_readonly_data": AccountDefaults.PLAYER_READONLY_DATA
        }
        options = { 'fields': projection }
        
        params = { 'query': query, 'update': update, 'options': options }

        valid = False
        response_str = None

        try:
            params_str = json.dumps(params)            
            response_str = self.rpcclient.createAccount(params_str) # recibe la respuesta como str
        except xmlrpc.client.Fault as err:
            print(err)
            # print(err.faultCode)
            # print(err.faultString)
            error_response['error'] = err
        except Exception as e:
            print(e)
            error_response['error'] = str(e)

        if response_str is not None:           
            response = json.loads(response_str)    # Convierte la respuesta de str a objeto json
            valid = True

        if valid:
            response["request_id"] = rq['request_id']
            return response
        else:
            await send_message(error_response, ws)  # send error response
            return None

    # Obtiene informacion de una cuenta y devuelve la respuesta como objeto json. Tambien permite
    # comprobar si una cuenta existe.
    # Devuelve {} si no se ha encontrado la cuenta especificada.
    # Devuelve None si ha habido algun error. En ese caso envia el mensaje de error al cliente antes de retornar None.
    async def read_account(self, rq, ws, send_message, query, projection):

        error_response = {
            "error": "",
            "request_id": rq['request_id']
        }

        params = { 
            "query": query,            
            "projection": projection # projection: Indica las propiedades que seran devueltas por readAccount.
        }

        valid = False
        response_str = None

        try:
            params_str = json.dumps(params)
            response_str = self.rpcclient.readAccount(params_str)
        except xmlrpc.client.Fault as err:
            print(err)
            error_response['error'] = err
        except Exception as e:
            print(e)
            error_response['error'] = str(e)

        if response_str is not None:
            response = json.loads(response_str)    # Convierte la respuesta de str a objeto json
            valid = True

        if valid:            
            return response
        else:
            await send_message(error_response, ws)  # send error response
            return None

    # Modifica informacion de una cuenta y devuelve la respuesta como objeto json.
    # La no existencia de la cuenta es considerada como un error.
    # Devuelve None si ha habido algun error. En ese caso envia el mensaje de error al cliente antes de retornar None.
    async def update_account(self, rq, ws, send_message, query, update, projection):

        error_response = {
            "error": "",
            "request_id": rq['request_id']
        }

        options = { 'fields': projection }

        params = { 
            "query": query,
            "update": update,
            "options": options
        }

        valid = False
        response_str = None

        try:
            params_str = json.dumps(params)
            response_str = self.rpcclient.updateAccount(params_str)
        except xmlrpc.client.Fault as err:
            print(err)
            error_response['error'] = err
        except Exception as e:
            print(e)
            error_response['error'] = str(e)

        if response_str is not None:
            response = json.loads(response_str)    # Convierte la respuesta de str a objeto json
            if not response: # Empty dict se convierte a false. rpcclient.readAccount_ devuelve {} si no se ha encontrado la account especificada.
                error_response['error'] = "Account not found."
                await send_message(error_response, ws)  # send error response
            else:
                valid = True

        if valid:
            response["request_id"] = rq['request_id']
            return response
        else:
            await send_message(error_response, ws)  # send error response
            return None

    # Obtiene informacion de multiples cuentas y devuelve la respuesta como objeto json.
    # Devuelve un objeto json {accounts: <JSON array>} con las accounts que cumplen el criterio de la query.
    # Devuelve None si ha habido algun error.
    def sync_read_accounts(self, query, projection):

        params = { 
            "query": query,            
            "projection": projection # projection: Indica las propiedades que seran devueltas por readAccount.
        }

        valid = False
        response_str = None

        try:
            params_str = json.dumps(params)
            response_str = self.rpcclient.readAccounts(params_str)
        except xmlrpc.client.Fault as err:
            print(err)
            return None
        except Exception as e:
            print(e)
            return None

        if response_str is not None:
            response = json.loads(response_str)    # Convierte la respuesta de str a objeto json
            valid = True

        if valid:
            return response
        else:
            return None


################# TEST #################



async def test_task():
    while True:
        try:
            database.rpcclient.testFunction()
        except Exception as e:
            print("Exception in test_task: ", str(e))
        await asyncio.sleep(5)

if __name__ == "__main__":

    port = 8004

    # El primer argumento es el puerto.
    for arg in sys.argv[1:]:
        port = int(arg)
        # print(arg)
        break    

    database = Database('http://127.0.0.1:{}'.format(port))

    asyncio.get_event_loop().run_until_complete(test_task())
    asyncio.get_event_loop().run_forever()









