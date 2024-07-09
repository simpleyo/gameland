package main

import (
	"fmt"
	"gameserver-go/slots"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/websocket/v2"
)

type Request struct {
	Request_id *string
	Command    *string
}

type WebsocketMessage struct {
	slotId      int
	messageType int
	data        []byte
}

type websocketControl struct {
	slotId int
}

type WebsocketClient struct {
	OperationType int // 0: Acquire Slot, 1: Release Slot
	SlotId        int
	C             *websocket.Conn
	Control       chan websocketControl
}

// Este loop mantiene la conexion websocket de un cliente.
// Datos que mantiene:
//		- C: 		*websocket.Conn				// La conexion websocket.
//		- Control:  chan websocketControl 		// chan que se usa para recibir el slotId asignado desde el registro.
// 		- SlotId: 	int							// SlotId asignado.
//
// Datos externos:
//		- registry: 	chan<- WebsocketClient	// chan que se usa para registrar el cliente pidiendo la asignacion de un slot.
//		- messageQueue: chan<- WebsocketMessage	// chan que se usa para encolar los mensajes recibidos.
//
func websocketClientReadLoop(c *websocket.Conn, registry chan<- WebsocketClient, messageQueue chan<- WebsocketMessage) {
	fmt.Println("RemoteAddr: ", c.Conn.RemoteAddr())

	wsc := WebsocketClient{
		OperationType: slots.RegistryOperationAcquireSlot,
		SlotId:        -1, // Si es -1 indicara, al registro, que se quiere ocupar un slot.
		C:             c,
		Control:       make(chan websocketControl),
	}

	registry <- wsc

	wcd := <-wsc.Control
	slotId := wcd.slotId
	fmt.Println("WebsocketClient assigned slot: ", slotId)

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

		fmt.Println("Message type:", mt)
		switch mt {
		case websocket.TextMessage: // TextMessage denotes a text data message. The text message payload is interpreted as UTF-8 encoded text data.
			// message = []byte(msg)
		case websocket.BinaryMessage: // BinaryMessage denotes a binary data message.
			// message = msg
		case websocket.CloseMessage: // ATENCION: Este caso nunca sucede, ya que c.ReadMessage() considera error la llegada de un websocket.CloseMessage. Se puede comprobar si el error es un CloseError mediante if e, ok := err.(*CloseError); ok {}
			fmt.Println("CloseMessage: ", msg)
			goto exit
		}

		// fmt.Println("Message:", message)
		messageQueue <- WebsocketMessage{slotId, mt, message}

		// if err = c.WriteMessage(websocket.BinaryMessage, message); err != nil {
		// }
	}

exit:
	wsc.OperationType = slots.RegistryOperationReleaseSlot
	wsc.SlotId = slotId // Si es distinto de -1, indica, al registro, que se quiere dejar libre el slot.

	registry <- wsc
}

func define_websockets_api(app *fiber.App, registry chan WebsocketClient, messageQueue chan WebsocketMessage) {

	app.Use("/ws", func(c *fiber.Ctx) error {
		// IsWebSocketUpgrade returns true if the client
		// requested upgrade to the WebSocket protocol.
		if websocket.IsWebSocketUpgrade(c) {
			c.Locals("allowed", true)
			return c.Next()
		}
		return fiber.ErrUpgradeRequired
	})

	// Fiber/Fasthttp uses a sync pool for the Context. This means that the moment you return from
	// the handler the Ctx will be re-used and becomes invalid. Everything you execute in the handler
	// is already running in a Go routine because fasthttp uses a workerpool by design.
	// So it's safe to use your function without spawning a second go routine.
	// Es decir, que websocketClientReadLoop no se debe ejecutar con 'go websocketClientReadLoop(...)' ya
	// que entonces se retornaria del handler app.Get y el Ctx, creado por websocket.New dejaria de ser valido.
	// El handler app.Get ya se ejecuta en su propia goroutine.
	app.Get("/ws", websocket.New(func(c *websocket.Conn) {
		websocketClientReadLoop(c, registry, messageQueue)
	}, websocket.Config{
		HandshakeTimeout: time.Second * 3, // HandshakeTimeout specifies the duration for the handshake to complete.
		ReadBufferSize:   4096,
		WriteBufferSize:  4096,
	}))
}
