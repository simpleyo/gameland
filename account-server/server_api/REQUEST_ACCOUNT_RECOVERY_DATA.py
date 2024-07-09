
import datetime
import json
from utils import generate_random_str, hashmd5, datetime_from_json_date_str
from validate_email import validate_email
from .sendmail import send_gameland_email

# REQUEST_ACCOUNT_RECOVERY_DATA
# 1. El cliente envia REQUEST_ACCOUNT_RECOVERY_DATA(email) al servidor.
# 2. El servidor comprueba que el email es valido en caso contrario devuelve error al cliente.
# 3. El servidor convierte el email a minusculas.
# 4. El servidor comprueba que existe ese email.
# 5. El servidor comprueba que el email esta validado.
# 6. El servidor genera un nuevo password para la cuenta y actualiza account_hash.
# 7. El servidor envia un email, con el account_name y con el password, al cliente.
async def REQUEST_ACCOUNT_RECOVERY_DATA(req, ws, send_message, database):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('email',)):
        print("ERROR: REQUEST_ACCOUNT_RECOVERY_DATA bad input parameters.")
        return

    error_response = {
        "error": "Invalid ticket.",
        "request_id": req['request_id']
    }  

    valid = False

    ### Comprueba si existe ese email

    req["email"] = req["email"].lower()
    email = req["email"]

    query = { "email": email }
    projection = 'account_name account_salt email_validated email'
    response = await database.read_account(req, ws, send_message, query, projection)
    if response is None:
        return

    ### Comprueba que el email esta validado.

    if validate_email(email):

        if 'email_validated' in response and\
            'email' in response and\
            'account_name' in response and\
            'account_salt' in response:

            email_validated = response['email_validated']
            if email_validated:
                
                account_name = response['account_name']
                account_salt = response['account_salt']
                password = generate_random_str(8)
                key_hash = hashmd5(password + hashmd5(account_name))
                account_hash = hashmd5(key_hash + account_salt)

                query = { 'email': email }
                update = { 'account_hash': account_hash }

                projection = 'session_id session_expire email'
                response = await database.update_account(req, ws, send_message, query, update, projection)
                if response is None:
                    return

                response["request_id"] = req['request_id']
                await send_message(response, ws)  # send response

                send_gameland_email(email, "Recover account", "Your recover data is:\n    AccountName: {}\n    Password: {}\n".format(account_name, password))

                valid = True
            else:
                error_response["error"] = "Account do not have a registered email."
        else:
            if not response: # if response is empty
                error_response["error"] = "No account found."
            else:
                error_response["error"] = "Invalid account."
    else:
        error_response["error"] = "Invalid email."

    ### Envia error al cliente.

    if not valid:
        await send_message(error_response, ws)
