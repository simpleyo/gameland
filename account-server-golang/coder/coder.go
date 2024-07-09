package coder

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"crypto/md5"
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"errors"
	"io"
	"io/ioutil"
)

func check(e error) {
	if e != nil {
		panic(e)
	}
}

var serverKey *rsa.PrivateKey
var serverPublicKey *rsa.PublicKey

func init() {

	// Load server private key
	{
		priv, err := ioutil.ReadFile("./server_key.pem")
		check(err)

		privPem, _ := pem.Decode(priv)
		if privPem.Type != "RSA PRIVATE KEY" {
			panic("RSA private key is of the wrong type")
		}

		data, err := x509.DecryptPEMBlock(privPem, []byte("12345678"))
		check(err)

		var parsedKey interface{}
		if parsedKey, err = x509.ParsePKCS1PrivateKey(data); err != nil {
			panic("Unable to parse RSA private key")
		}

		serverKey = parsedKey.(*rsa.PrivateKey)
	}

	// Load server public key
	{
		priv, err := ioutil.ReadFile("./server_public_key.pem")
		check(err)

		privPem, _ := pem.Decode(priv)
		if privPem.Type != "PUBLIC KEY" {
			panic("RSA public key is of the wrong type")
		}

		data, err := x509.DecryptPEMBlock(privPem, []byte("12345678"))
		check(err)

		var parsedKey interface{}
		if parsedKey, err = x509.ParsePKIXPublicKey(data); err != nil {
			panic("Unable to parse RSA public key")
		}

		serverPublicKey = parsedKey.(*rsa.PublicKey)
	}
}

type CodedRequest struct {
	A string
	B string
	C string
}

func ServerDecode(msg []byte) (decodedMessage []byte, serverSessionKey []byte, err error) {

	var cr CodedRequest
	err = json.Unmarshal(msg, &cr)
	if err != nil {
		return
	}

	iv, err := base64.StdEncoding.DecodeString(cr.A)
	if err != nil {
		return
	}

	ct, err := base64.StdEncoding.DecodeString(cr.B)
	if err != nil {
		return
	}

	sk, err := base64.StdEncoding.DecodeString(cr.C)
	if err != nil {
		return
	}

	sk, err = rsa.DecryptPKCS1v15(nil, serverKey, sk)
	if err != nil {
		return
	}

	md5Hash := sk[(len(sk) - 16):]
	sk = sk[:(len(sk) - 16)]

	m := md5.Sum(sk)
	if !bytes.Equal(m[:], md5Hash) {
		err = errors.New("md5 error")
		return
	}

	serverSessionKey = sk

	block, err := aes.NewCipher([]byte(serverSessionKey))
	if err != nil {
		return
	}
	mode := cipher.NewCBCDecrypter(block, iv)
	mode.CryptBlocks(ct, ct)

	padding := int(ct[len(ct)-1])
	ct = ct[:(len(ct) - padding)]

	decodedMessage = ct

	return
}

func ServerCode(msg []byte, requestId string, serverSessionKey []byte) (codedMessage []byte, err error) {

	block, err := aes.NewCipher(serverSessionKey)
	if err != nil {
		return
	}

	var inputMessage []byte
	if len(msg)%aes.BlockSize == 0 {
		inputMessage = make([]byte, aes.BlockSize+len(msg))
		p := inputMessage[len(msg):]
		for i := range p {
			p[i] = aes.BlockSize
		}
	} else {
		padding := byte(aes.BlockSize - (len(msg) % aes.BlockSize))
		inputMessage = make([]byte, ((len(msg)/aes.BlockSize)+1)*aes.BlockSize)
		p := inputMessage[len(msg):]
		for i := range p {
			p[i] = padding
		}
	}
	copy(inputMessage, msg)

	orig_iv := make([]byte, 16)
	if _, err = io.ReadFull(rand.Reader, orig_iv); err != nil {
		return
	}
	iv := make([]byte, 16)
	copy(iv, orig_iv)

	// codedMessage = make([]byte, len(inputMessage))
	cbc := cipher.NewCBCEncrypter(block, iv)
	cbc.CryptBlocks(inputMessage, inputMessage)

	iv_str := base64.StdEncoding.EncodeToString(iv)
	cm_str := base64.StdEncoding.EncodeToString(inputMessage) //codedMessage)

	codedMessage, err = json.Marshal(map[string]string{"a": requestId, "b": iv_str, "c": cm_str})

	return
}

// def server_code(msg, request_id, server_session_key):
//     if type(msg) == str:
//         msg = msg.encode()

//     cipher = AES.new(server_session_key, AES.MODE_CBC)
//     ct_bytes = cipher.encrypt(pad(msg, AES.block_size))

//     iv = b64encode(cipher.iv).decode('utf-8')               # input vector
//     ct = b64encode(ct_bytes).decode('utf-8')                # cipher text
//     result = json.dumps({'a': request_id, 'b':iv, 'c':ct })

//     return result
