
from datetime import datetime
from utils import str_to_date, hashmd5
from validate_email import validate_email
from .sendmail import send_gameland_email

# UPGRADE_ACCOUNT
# 1. El cliente envia UPGRADE_ACCOUNT(session_id, upgrade_code) al servidor.
# 2. El servidor comprueba que existe esa session_id y no esta caducada.
# 3. El servidor comprueba el upgrade_code y modifica email_validated en la cuenta indicada por session_id si
#    el codigo es valido.
async def UPGRADE_ACCOUNT(req, ws, send_message, database):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('session_id', 'upgrade_code')):
        print("ERROR: UPGRADE_ACCOUNT bad input parameters.")
        return

    error_response = {
        "error": "Invalid ticket.",
        "request_id": req['request_id']
    }  

    valid = False

    ### Comprueba si existe esa session_id

    session_id = req["session_id"]

    query = { "session_id": session_id }
    projection = 'session_expire guest_account_id email'
    response = await database.read_account(req, ws, send_message, query, projection)
    if response is None:
        return

    ### Comprueba que la session no esta caducada y que el upgrade_code es valido

    if 'session_expire' in response:
        # session_expire_date = datetime_from_json_date_str(response['session_expire'])
        # if session_expire_date >= datetime.datetime.now():
        if 'guest_account_id' in response or str_to_date(response['session_expire']) >= datetime.now():

            upgrade_code = req["upgrade_code"]

            is_valid_code = False

            # Comprueba que la cuenta tenga un email asociado, en caso que no lo tenga entonces el
            # codigo no puede ser correcto.
            if 'email' in response:
                email = response['email']            
                valid_code = hashmd5(database.UPGRADE_CODE_SALT + email)[:6]
                is_valid_code = (upgrade_code == valid_code)

            if is_valid_code:
                ### Update email_validated

                query = { "session_id": session_id }
                update = { 'email_validated': True }

                projection = 'session_id session_expire email email_validated'
                response = await database.update_account(req, ws, send_message, query, update, projection)
                if response is None:
                    return

                response["request_id"] = req['request_id']
                await send_message(response, ws)  # send response

                valid = True
            else:
                error_response["error"] = "Invalid upgrade code."
        else:
            error_response["error"] = "Session is expired."
    else:
        error_response["error"] = "No account found."

    ### Envia error al cliente.

    if not valid:
        await send_message(error_response, ws)
