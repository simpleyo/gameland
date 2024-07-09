package main

import (
	"encoding/json"
	"os"
)

type Config struct {
	GAME_SERVER_PORT uint
}

func ReadConfig() *Config {
	cfg := Config{}
	{
		var data []byte
		var err error
		filename := "./gameserver/gogameserver.cfg"
		data, err = os.ReadFile(filename)
		if err != nil {
			filename := "./gogameserver.cfg"
			data, err = os.ReadFile(filename)
			if err != nil {
				panic(err)
			}
		}
		json.Unmarshal(data, &cfg)
	}

	return &cfg
}
