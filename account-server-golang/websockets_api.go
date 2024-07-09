package main

import (
	"account-server/coder"
	"account-server/server_api"
	"encoding/json"
	"fmt"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/websocket/v2"
)

type Request struct {
	Request_id *string
	Command    *string
}

func consumeMessage(message []byte, serverSessionKey []byte, c *websocket.Conn) {

	fmt.Println(string(message))

	var r Request

	err := json.Unmarshal(message, &r)
	if err != nil {
		fmt.Println("consumeMessage:", err)
		return
	}
	if r.Request_id == nil {
		return
	}
	if r.Command == nil {
		return
	}

	sendResponse := func(response []byte) {
		codedResponse, err := coder.ServerCode(response, *r.Request_id, serverSessionKey)
		if err != nil {
			fmt.Println("consumeMessage["+*r.Command+"]:", err)
			return
		}
		if err = c.WriteMessage(websocket.TextMessage, codedResponse); err != nil {
			fmt.Println("consumeMessage["+*r.Command+"]:", err)
			return
		}
	}

	sendBlob := func(blob []byte) {
		if err = c.WriteMessage(websocket.BinaryMessage, blob); err != nil {
			fmt.Println("consumeMessage["+*r.Command+"]:", err)
			return
		}
	}

	if rateLimiterPerCommand(r.Command, c) {
		fmt.Printf("Command[%s] rate limited.", *r.Command)
		c.WriteMessage(websocket.CloseMessage, nil)
		return
	}

	switch *r.Command {
	// Client commands
	case "LOGIN_AS_GUEST":
		err = server_api.LOGIN_AS_GUEST(message, sendResponse, c)
	case "LOGIN":
		err = server_api.LOGIN(message, sendResponse, c, false)
	case "REGISTER_ACCOUNT":
		err = server_api.REGISTER_ACCOUNT(message, sendResponse, c)
	case "AUTHENTICATE_SESSION_TICKET":
		err = server_api.AUTHENTICATE_SESSION_TICKET(message, sendResponse)
	case "UPDATE_PLAYER_DATA":
		err = server_api.UPDATE_PLAYER_DATA(message, sendResponse)
	case "MATCHMAKE":
		err = server_api.MATCHMAKE(message, sendResponse)
	case "READ_RANKING":
		err = server_api.READ_RANKING(message, sendResponse)
	case "READ_GAME_SERVERS":
		err = server_api.READ_GAME_SERVERS(message, sendResponse)
	case "GET_GAME_RESOURCE":
		err = server_api.GET_GAME_RESOURCE(message, sendResponse, sendBlob)
	case "BUY_WITH_GOLD":
		err = server_api.BUY_WITH_GOLD(message, sendResponse)
	case "PUT_COMMENT":
		err = server_api.PUT_COMMENT(message, sendResponse)

	// Server commands
	case "REGISTER_GAMESERVER_INSTANCE":
		err = server_api.REGISTER_GAMESERVER_INSTANCE(message, sendResponse, c)
	case "UNREGISTER_GAMESERVER_INSTANCE":
		err = server_api.UNREGISTER_GAMESERVER_INSTANCE(message, sendResponse)
	case "REFRESH_GAMESERVER_INSTANCE_STATE":
		err = server_api.REFRESH_GAMESERVER_INSTANCE_STATE(message, sendResponse)
	case "VALIDATE_MACTHMAKER_TICKET":
		err = server_api.VALIDATE_MACTHMAKER_TICKET(message, sendResponse)
	case "NOTIFY_MATCHMAKER_PLAYER_LEFT":
		err = server_api.NOTIFY_MATCHMAKER_PLAYER_LEFT(message, sendResponse)
	case "UPDATE_PLAYER_READONLY_DATA":
		err = server_api.UPDATE_PLAYER_READONLY_DATA(message, sendResponse)
	case "NOTIFY_GAME_TERMINATED":
		err = server_api.NOTIFY_GAME_TERMINATED(message, sendResponse)
	case "GET_GAMESERVER_RESOURCE":
		err = server_api.GET_GAMESERVER_RESOURCE(message, sendResponse, sendBlob)
	}

	if err != nil {
		fmt.Println("Error: ", err)
	}
}

func define_websockets_api(app *fiber.App) {

	app.Use("/ws", func(c *fiber.Ctx) error {
		// IsWebSocketUpgrade returns true if the client
		// requested upgrade to the WebSocket protocol.
		if websocket.IsWebSocketUpgrade(c) {
			c.Locals("allowed", true)
			return c.Next()
		}
		return fiber.ErrUpgradeRequired
	})

	app.Get("/ws", websocket.New(func(c *websocket.Conn) {
		fmt.Println("RemoteAddr: ", c.Conn.RemoteAddr())

		// websocket.Conn bindings https://pkg.go.dev/github.com/fasthttp/websocket?tab=doc#pkg-index
		var (
			mt  int
			msg []byte
			err error
		)
		for {
			if mt, msg, err = c.ReadMessage(); err != nil {
				fmt.Println("read:", err, mt)
				break
			}
			// log.Printf("recv: %s %d", msg, mt)

			message := msg

			// fmt.Println("Message type:", mt)
			switch mt {
			case websocket.TextMessage: // TextMessage denotes a text data message. The text message payload is interpreted as UTF-8 encoded text data.
				// message = []byte(msg)
			case websocket.BinaryMessage: // BinaryMessage denotes a binary data message.
				// message = msg
			case websocket.CloseMessage: // ATENCION: Este caso nunca sucede, ya que c.ReadMessage() considera error la llegada de un websocket.CloseMessage. Se puede comprobar si el error es un CloseError mediante if e, ok := err.(*CloseError); ok {}
				fmt.Println("CloseMessage: ", msg)
				goto exit
			}

			decodedMessage, serverSessionKey, err := coder.ServerDecode(message)
			if err != nil {
				fmt.Println(err)
			} else {
				consumeMessage(decodedMessage, serverSessionKey, c)
			}
		}

	exit:
	}, websocket.Config{
		HandshakeTimeout: time.Second * 3, // HandshakeTimeout specifies the duration for the handshake to complete.
	}))
}
