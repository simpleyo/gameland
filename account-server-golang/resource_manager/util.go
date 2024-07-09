package resource_manager

import (
	"fmt"
	"strings"
)

func Md5ToHexString(md5Bytes [16]byte) string {
	return strings.ToLower(fmt.Sprintf("%x", md5Bytes))
}
