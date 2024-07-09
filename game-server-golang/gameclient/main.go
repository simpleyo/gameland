package main

import (
	"context"
	"fmt"
	"time"

	"nhooyr.io/websocket"
)

// Ejecutar con: go run ./gameclient
func main() {
	fmt.Println("gameclient")

	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()

	c, _, err := websocket.Dial(ctx, "ws://127.0.0.1:37070/ws", nil)
	if err != nil {
		fmt.Println("Error: ", err)
		return
	}
	fmt.Println("OK")

	defer c.Close(websocket.StatusInternalError, "the sky is falling")

	err = c.Write(ctx, websocket.MessageBinary, []byte{2, 3})

	if err != nil {
		// ...
	}

	// Crear un canal para recibir mensajes del servidor
	messages := make(chan string)

	go func() {
		mt, bytes, err := c.Read(ctx)
		if err != nil {
			fmt.Println("Error al leer el mensaje del servidor:", err)
			return
		}
		message := string(bytes)
		fmt.Println("Data:", mt, message)

		// Enviar el mensaje al canal para que lo procese RunGame()
		messages <- message
	}()

	// Iniciar goroutine para recibir mensajes del servidor
	go func() {
		for {
			mt, bytes, err := c.Read(ctx)
			if err != nil {
				fmt.Println("Error al leer el mensaje del servidor:", err)
				return
			}
			message := string(bytes)
			fmt.Println("Data:", mt, message)

			// Enviar el mensaje al canal para que lo procese RunGame()
			messages <- message
		}
	}()

	// mt, bytes, err := c.Read(ctx)
	// fmt.Println("Data: ", mt, bytes, err)

	// Ejecutar el bucle del juego
	RunGame(messages, make(chan string))

	c.Close(websocket.StatusNormalClosure, "")
}
