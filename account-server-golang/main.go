package main

import (
	"account-server/database"
	"account-server/ranking"
	"account-server/resource_manager"
	"account-server/utils"
	"fmt"
	"runtime"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
)

type dict = map[string]any

var accountServerConfig *Config

func main() {

	accountServerConfig = ReadConfig()
	cfg := accountServerConfig

	// origin_updater.Initialize(cfg.IS_TEST_INSTANCE, cfg.MAIN_SERVER_PORT, cfg.TEST_MAIN_SERVER_PORT, cfg.ORIGIN_SERVER_ADDRESS, cfg.ORIGIN_SERVER_PORT)
	resource_manager.Initialize(cfg.RESOURCE_SERVER_DIR)
	database.Initialize(cfg.IS_TEST_INSTANCE)
	ranking.Initialize(resource_manager.GetGameEnabledMaps("tanks"))

	app := fiber.New()

	app.Use(cors.New()) // Default config

	define_websockets_api(app)
	define_paypal_api(app)
	// define_launchers_api(app)

	utils.EnableControlCHandler() // Intercepta la finalizacion del programa mediante la pulsacion de la tecla Control-C.

	main_server_port := cfg.MAIN_SERVER_PORT
	if cfg.IS_TEST_INSTANCE {
		main_server_port = cfg.TEST_MAIN_SERVER_PORT
		fmt.Println("TEST MAIN SERVER")
	}

	if runtime.GOOS == "windows" {
		// app.Listen(fmt.Sprintf(":%d", main_server_port))
		if err := app.ListenTLS(fmt.Sprintf(":%d", main_server_port), "../fullchain1.pem", "../privkey1.pem"); err != nil {
			fmt.Println(err)
		}
	} else if runtime.GOOS == "linux" {
		if err := app.ListenTLS(fmt.Sprintf(":%d", main_server_port), "/home/angel/DEV/letsencrypt/live/fullchain.pem", "/home/angel/DEV/letsencrypt/live/privkey.pem"); err != nil {
			fmt.Println(err)
		}
	}
}
