package main

import (
	"account-server/orders"
	"encoding/json"

	"github.com/gofiber/fiber/v2"
)

// PAYPAL TEST ACCOUNT
// sb-thbg4715221958@personal.example.com
// j38Q$EQu

func define_paypal_api(app *fiber.App) {

	app.Post("/api/create-order", func(c *fiber.Ctx) error {
		orderParams := orders.OrderParams{}
		if err := c.BodyParser(&orderParams); err != nil {
			return err
		}
		orderId, err := orders.CreateOrder(&orderParams)
		if err != nil {
			return err
		}
		m := dict{"orderId": orderId}
		result, err := json.Marshal(m)
		if err != nil {
			return err
		}
		return c.Send(result)
	})

	app.Post("/api/payment-canceled-or-error", func(c *fiber.Ctx) error {
		data := struct {
			OrderId       int64
			PaypalOrderId string
		}{}
		if err := c.BodyParser(&data); err != nil {
			return err
		}
		if err := orders.PaymentCanceledOrError(data.OrderId, data.PaypalOrderId); err != nil {
			return err
		}
		return c.Send(c.Request().Body())
	})

	app.Post("/api/payment-completed", func(c *fiber.Ctx) error {
		data := struct {
			OrderId       int64
			PaypalOrderId string
		}{}
		if err := c.BodyParser(&data); err != nil {
			return err
		}
		if err := orders.PaymentCompleted(data.OrderId, data.PaypalOrderId); err != nil {
			return err
		}

		return c.Send(c.Request().Body())
	})
}
