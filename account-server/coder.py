from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Hash import SHA
from Crypto.Hash import MD5
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode
import json

client_session_key = {} # Se debe asociar una session_key a cada request_id que envie el cliente al servidor.

f = open('./server_key.pem','r')        
server_key = RSA.import_key(f.read(), '12345678')           # Server private key. Es usada por el servidor.

f = open('./server_public_key.pem','r') 
server_public_key = RSA.import_key(f.read(), '12345678')    # Server public key. Es usada por el cliente.

def server_decode(msg):
    try:
        b64 = json.loads(msg)
        iv = b64decode(b64['a'])
        ct = b64decode(b64['b'])
        sk = b64decode(b64['c'])       

        cipher = PKCS1_v1_5.new(server_key)
        sk = cipher.decrypt(sk, None)

        md5_hash = sk[-16:]
        sk = sk[:-16]

        assert MD5.new(sk).digest() == md5_hash

        server_session_key = sk

        cipher = AES.new(sk, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        
    except (ValueError, KeyError):
        print("Incorrect decryption")
        return

    return (pt, server_session_key)

def server_code(msg, request_id, server_session_key):
    if type(msg) == str:
        msg = msg.encode()
      
    cipher = AES.new(server_session_key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(msg, AES.block_size))

    iv = b64encode(cipher.iv).decode('utf-8')               # input vector
    ct = b64encode(ct_bytes).decode('utf-8')                # cipher text
    result = json.dumps({'a': request_id, 'b':iv, 'c':ct })

    return result

def client_code(request_id, msg):
    if type(msg) == str:
        msg = msg.encode()

    session_key = get_random_bytes(24)
    h = MD5.new(session_key).digest()
    cipher = PKCS1_v1_5.new(server_key)
    ciphered_session_key = cipher.encrypt(session_key + h)

    global client_session_key
    client_session_key[request_id] = session_key

    cipher = AES.new(session_key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(msg, AES.block_size))

    iv = b64encode(cipher.iv).decode('utf-8')               # input vector
    ct = b64encode(ct_bytes).decode('utf-8')                # cipher text
    sk = b64encode(ciphered_session_key).decode('utf-8')    # session key
    result = json.dumps({'a':iv, 'b':ct, 'c': sk })

    # print(result)

    return result

def client_decode(msg):
    try:
        d = json.loads(msg)
        request_id = d['a']        # El request_id lo usara el cliente para asociar una session_key a cada request_id que envie al servidor.
        iv = b64decode(d['b'])
        ct = b64decode(d['c'])

        global client_session_key
        session_key = client_session_key.pop(request_id, None)

        cipher = AES.new(session_key, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        
    except (ValueError, KeyError):
        print("Incorrect decryption")
        return

    return pt



################# TEST #################



if __name__ == "__main__":
    # test
    test_request = { 
       'request_id': "test123",
       'session_key': "test456"
    }

    client_session_key[test_request['request_id']] = test_request

    test_msg = b'1234567890'
    (msg, session_key) = server_decode(client_code(test_request['request_id'], test_msg))
    assert msg == test_msg
    assert client_decode(server_code(test_msg, test_request['request_id'], session_key)) == test_msg

    print("Tests passed.")
