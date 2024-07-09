package main

import (
	"encoding/json"
	"os"
)

type Config struct {
	IS_TEST_INSTANCE      bool
	ORIGIN_SERVER_ADDRESS string
	ORIGIN_SERVER_PORT    uint
	MAIN_SERVER_PORT      uint
	TEST_MAIN_SERVER_PORT uint
	RESOURCE_SERVER_DIR   string
}

func ReadConfig() *Config {
	cfg := Config{}
	{
		data, err := os.ReadFile("./accountserver.cfg")
		if err != nil {
			panic(err)
		}
		json.Unmarshal(data, &cfg)
	}

	return &cfg
}
