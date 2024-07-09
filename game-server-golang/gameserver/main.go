package main

import (
	"fmt"
	"gameserver-go/engine"
	"gameserver-go/tank"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
)

func main() {
	tk := tank.Tank{}
	tk.InitEntity(0)
	tksd := tank.TankSnapData{}
	tk.S.Init(&tksd)

	fmt.Println("Main")

	gameServer = &GameServer{}
	gameServer.Make(ReadConfig())

	engine.Initialize(engine.Config{
		MAX_NUMBER_OF_GMAPS: MAX_NUMBER_OF_ROOMS,
		MAX_NUMBER_OF_VIEWS: MAX_NUMBER_OF_PLAYERS_PER_ROOM,
	}, gameServer.engineEvents)

	cfg := gameServer.config

	app := fiber.New(fiber.Config{
		BodyLimit:    64 * 1024,       // Max body size that the server accepts.
		Concurrency:  1024,            // Maximum number of concurrent connections.
		ReadTimeout:  5 * time.Second, // The amount of time allowed to read the full request including body.
		WriteTimeout: 5 * time.Second, // The maximum duration before timing out writes of the response.
	})

	app.Use(cors.New()) // Default config

	registry := make(chan WebsocketClient, 10)       // chan en el que se registran/desregistran los clientes.
	messageQueue := make(chan WebsocketMessage, 100) // chan en el que los clientes encolan los mensajes que reciben.

	go gameServerLoop(registry, messageQueue)
	go engine.Loop()

	gameServer.AddRoomRequest()

	define_websockets_api(app, registry, messageQueue)

	app.Listen(fmt.Sprintf(":%d", cfg.GAME_SERVER_PORT))
}
