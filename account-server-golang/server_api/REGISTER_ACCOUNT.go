package server_api

import (
	"github.com/gofiber/websocket/v2"
)

func REGISTER_ACCOUNT(message []byte, sendResponse func([]byte), c *websocket.Conn) error {
	return LOGIN(message, sendResponse, c, true)
}
