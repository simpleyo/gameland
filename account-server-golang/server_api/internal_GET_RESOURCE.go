package server_api

import (
	"account-server/resource_manager"
	"account-server/utils"
	"encoding/json"
)

func internal_GET_RESOURCE(requestId string, gameName string, resourcePath string, resourceMd5 string,
	sendResponse func([]byte), sendBlob func([]byte)) error {

	result, resMd5, err := resource_manager.GetResource(gameName, resourcePath, resourceMd5)
	if err != nil {
		return err
	}

	responseDict := dict{
		"request_id":   requestId,
		"resource_md5": resMd5,
	}

	var blob []byte
	if result != nil {
		blobId := utils.GenerateRandomString(32)
		responseDict["resource_blob_id"] = blobId
		blob = append([]byte("BLOB"), []byte(blobId)...)
		blob = append(blob, result...)
	}

	response, err := json.Marshal(responseDict)
	if err != nil {
		return err
	}

	sendResponse(response)

	if blob != nil {
		sendBlob(blob)
	}

	return err
}
