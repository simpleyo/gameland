# LOGIN_AS_GUEST:
#  - El cliente envia guest_account_id (generado aleatoriamente) y display_name.
#  - Si no existe guest_account_id entonces el servidor crea (createAccount) una nueva cuenta, con una caducidad para session_id de 180 dias.
#  - Si existe el guest_account_id, la caducidad de la sesion se actualiza a 180 dias.
#  - El servidor responde al cliente con un session_id.
#  - El cliente guardara el guest_account_id y el session_id el cual tiene fecha de caducidad.
#  - El cliente, con el session_id, puede hacer peticiones al servidor (getPlayerData) hasta que el
#    servidor responda con error de sesion caducada. Entonces el cliente debera utilizar el guest_account_id para
#    volver a hacer login.
#  - El cliente se considera a si mismo logueado si tiene una session_id no caducada, es decir, para la cual el servidor no ha respondido con error.
#  - En la misma llamada de login se devuelve la "player data"
async def LOGIN_AS_GUEST(req, ws, send_message, accounts_cache):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'guest_account_id')):
        print("ERROR: LOGIN_AS_GUEST bad input parameters.")
        return

    response = await accounts_cache.create_guest_account(req, ws, send_message)
    if response is None:
        return

    # Esta comprobacion se realizara en las peticiones de informacion.
    #
    # session_expire = datetime.datetime.strptime(resp['session_expire'], '%Y-%m-%dT%H:%M:%S.%fZ') # convierte la fecha a formato python
    # if session_expire < datetime.datetime.now():
    #     params['error'] = "Session has expired."
    #     await send_message(json.dumps(err), ws)  # send error response
    #     return

    response["request_id"] = req['request_id']
    await send_message(response, ws)  # send response
