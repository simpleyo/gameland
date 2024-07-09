package main

import (
	"account-server/launchers"
	"net/http"

	"github.com/gofiber/fiber/v2"
)

//   - Launcher commands:
//
//     REGISTER_LAUNCHER_INSTANCE
//     UNREGISTER_LAUNCHER_INSTANCE
//     REFRESH_LAUNCHER_INSTANCE_STATE
//
func define_launchers_api(app *fiber.App) {

	app.Post("/api/REGISTER_LAUNCHER_INSTANCE", func(c *fiber.Ctx) error {
		var data launchers.LauncherInfo
		if err := c.BodyParser(&data); err != nil {
			return err
		}

		launchers.AddLauncher(&data)

		return c.SendStatus(http.StatusOK)
	})

	app.Post("/api/UNREGISTER_LAUNCHER_INSTANCE", func(c *fiber.Ctx) error {
		var data launchers.LauncherInfo
		if err := c.BodyParser(&data); err != nil {
			return err
		}

		launchers.RemoveLauncher(data.Launcher_id)

		return c.SendStatus(http.StatusOK)
	})

	app.Post("/api/REFRESH_LAUNCHER_INSTANCE_STATE", func(c *fiber.Ctx) error {
		var data launchers.LauncherInfo
		if err := c.BodyParser(&data); err != nil {
			return err
		}

		launchers.RefreshLauncher(data.Launcher_id)

		return c.SendStatus(http.StatusOK)
	})
}
