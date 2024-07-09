package origin_updater

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"
)

const OriginUpdateInterval = 1 * time.Minute // Tiempo entre actualizaciones enviadas al origin server.

var originUpdater OriginUpdater = OriginUpdater{}

type dict = map[string]any

type OriginUpdater struct {
	MainServer struct {
		Is_test_instance bool
		Ipv4_address     string
		Port             uint
	}

	OriginServer struct {
		Ipv4_address string
		Port         uint
	}
}

func (o *OriginUpdater) update() error {
	ip, err := getPublicIP()
	if err != nil {
		return err
	}

	o.MainServer.Ipv4_address = ip

	// Crea el http.Client
	client := &http.Client{
		Timeout: time.Second * 5,
	}

	// Send PUT_MAIN_SERVER_INFO
	{
		// Rellena los bytes que se enviaran
		data := dict{
			// "address":          o.MainServer.Ipv4_address,
			"port":             o.MainServer.Port,
			"is_test_instance": o.MainServer.Is_test_instance,
		}
		dataBytes, err := json.Marshal(data)
		if err != nil {
			return err
		}

		// Crea la request
		url := "http://" + o.OriginServer.Ipv4_address + fmt.Sprintf(":%d", o.OriginServer.Port) + "/api/PUT_MAIN_SERVER_INFO"
		req, err := http.NewRequest("POST", url, bytes.NewBuffer(dataBytes))
		if err != nil {
			return err
		}
		req.Header.Add("Accept-Encoding", "gzip, deflate, br")
		req.Header.Add("Content-type", "application/json")

		// Envia la request al origin-server
		resp, err := client.Do(req)
		if err != nil {
			return err
		}

		// Recibe la respuesta
		defer resp.Body.Close()
		_, err = ioutil.ReadAll(resp.Body)
		if err != nil {
			return err
		}
		// fmt.Println("Body: ", string(body))
	}

	// Send PUT_REGISTRY_VALUE
	{
		// Rellena los bytes que se enviaran
		data := dict{
			"key":   "a",
			"value": dict{"b": 2},
		}
		dataBytes, err := json.Marshal(data)
		if err != nil {
			return err
		}

		// Crea la request
		url := "http://" + o.OriginServer.Ipv4_address + fmt.Sprintf(":%d", o.OriginServer.Port) + "/api/PUT_REGISTRY_VALUE"
		req, err := http.NewRequest("POST", url, bytes.NewBuffer(dataBytes))
		if err != nil {
			return err
		}
		req.Header.Add("Accept-Encoding", "gzip, deflate, br")
		req.Header.Add("Content-type", "application/json")

		// Envia la request al origin-server
		resp, err := client.Do(req)
		if err != nil {
			return err
		}

		// Recibe la respuesta
		defer resp.Body.Close()
		_, err = ioutil.ReadAll(resp.Body)
		if err != nil {
			return err
		}
		// fmt.Println("Body: ", string(body))
	}

	// Send GET_REGISTRY_VALUE
	{
		// Crea la request
		url := "http://" + o.OriginServer.Ipv4_address + fmt.Sprintf(":%d", o.OriginServer.Port) + "/api/GET_REGISTRY_VALUE/?key=a"
		req, err := http.NewRequest("GET", url, nil)
		if err != nil {
			return err
		}
		req.Header.Add("Accept-Encoding", "gzip, deflate, br")
		req.Header.Add("Content-type", "application/json")

		// Envia la request al origin-server
		resp, err := client.Do(req)
		if err != nil {
			return err
		}

		// Recibe la respuesta
		defer resp.Body.Close()
		_, err = ioutil.ReadAll(resp.Body)
		if err != nil {
			return err
		}
		// fmt.Println("Body: ", string(body))
	}

	return nil
}

func (o *OriginUpdater) updateOriginTask() {
	for {
		time.Sleep(OriginUpdateInterval)
		err := o.update()
		if err != nil {
			log.Println("ERROR: ", err)
		}
	}
}

// getPublicIP get your public ip
func getPublicIP() (string, error) {
	resp, err := http.Get("https://ifconfig.me")
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return string(body), nil
}

func Initialize(is_test_instance bool, mainServerPort uint, testMainServerPort uint, originServer string, originServerPort uint) {

	originUpdater.MainServer.Is_test_instance = is_test_instance
	if is_test_instance {
		originUpdater.MainServer.Port = testMainServerPort
	} else {
		originUpdater.MainServer.Port = mainServerPort
	}
	originUpdater.OriginServer.Ipv4_address = originServer
	originUpdater.OriginServer.Port = originServerPort

	err := originUpdater.update()
	if err != nil {
		log.Println("ERROR: ", err)
	}

	go originUpdater.updateOriginTask()
}
