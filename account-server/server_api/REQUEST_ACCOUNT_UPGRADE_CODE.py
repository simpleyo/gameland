
from datetime import datetime
from utils import str_to_date, hashmd5
from validate_email import validate_email
from .sendmail import send_gameland_email

# REQUEST_ACCOUNT_UPGRADE_CODE
# 1. El cliente envia REQUEST_ACCOUNT_UPGRADE_CODE(session_id, email) al servidor.
# 2. El servidor comprueba que el email es valido en caso contrario devuelve error al cliente.
# 3. El servidor convierte el email a minusculas.
# 4. El servidor comprueba que existe esa session_id y no esta caducada.
# 5. El servidor modifica email en la cuenta indicada por session_id.
# 6. El servidor envia un email, con el upgrade code, al cliente.
async def REQUEST_ACCOUNT_UPGRADE_CODE(req, ws, send_message, database):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('session_id', 'email')):
        print("ERROR: REQUEST_ACCOUNT_UPGRADE_CODE bad input parameters.")
        return

    error_response = {
        "error": "Invalid ticket.",
        "request_id": req['request_id']
    }  

    valid = False

    ### Comprueba si existe esa session_id

    session_id = req["session_id"]

    query = {"session_id": session_id}
    projection = 'session_expire guest_account_id'
    response = await database.read_account(req, ws, send_message, query, projection)
    if response is None:
        return

    ### Comprueba que la session no esta caducada y que el email es valido

    if 'session_expire' in response:
        # session_expire_date = datetime_from_json_date_str(response['session_expire'])
        # if session_expire_date >= datetime.datetime.now():
        if 'guest_account_id' in response or str_to_date(response['session_expire']) >= datetime.now():
            
            req["email"] = req["email"].lower()
            email = req["email"]

            if validate_email(email):
                ### Update email

                query = { "session_id": session_id }
                update = { 'email': email }

                projection = 'session_id session_expire email'
                response = await database.update_account(req, ws, send_message, query, update, projection)
                if response is None:
                    return

                response["request_id"] = req['request_id']
                await send_message(response, ws)  # send response

                code = hashmd5(database.UPGRADE_CODE_SALT + email)[:6]
                send_gameland_email(email, "Upgrade code", "Your upgrade code is: {}".format(code))

                valid = True
            else:
                error_response["error"] = "Invalid email."
        else:
            error_response["error"] = "Session is expired."
    else:
        error_response["error"] = "No account found."

    ### Envia error al cliente.

    if not valid:
        await send_message(error_response, ws)
