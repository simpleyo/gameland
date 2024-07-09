package utils

import (
	"crypto/rand"
	"fmt"
	"os"
	"os/signal"
	"strings"
	"syscall"
)

// func allNil(vv ...interface{}) bool {
// 	for _, v := range vv {
// 		if v != nil {
// 			return false
// 		}
// 	}
// 	return true
// }

// func allNotNil(vv ...interface{}) bool {
// 	for _, v := range vv {
// 		if v == nil {
// 			return false
// 		}
// 	}
// 	return true
// }

func GenerateRandomBytes(n int) []byte {
	if n%2 != 0 {
		panic(nil)
	}
	token := make([]byte, n)
	rand.Read(token)
	return token
}

func GenerateRandomString(n int) string {
	if n%2 != 0 {
		panic(nil)
	}
	return strings.ToLower(fmt.Sprintf("%x", GenerateRandomBytes(n/2)))
}

func ContainsAllKeys(m map[string]any, keys []string) bool {
	for _, key := range keys {
		if _, ok := m[key]; !ok {
			return false
		}
	}
	return true
}

func Md5ToHexString(md5Bytes [16]byte) string {
	return strings.ToLower(fmt.Sprintf("%x", md5Bytes))
}

// CropString limita <str> a <numberOfRunes> caracteres unicode.
func CropString(str string, numberOfRunes uint) string {
	var runeSlice []rune = make([]rune, 0, numberOfRunes)
	i := uint(0)
	for _, v := range str {
		runeSlice = append(runeSlice, v)
		i += 1
		if i == numberOfRunes {
			break
		}
	}
	return string(runeSlice)
}

type dict = map[string]any

// Asigna a data las keys que estan en update y no en data. Si hay keys que estan en update y en data entonces
// se asigna, a data, el value de update si, y solo si, ambos values no son dicts.
// Esta funcion solo permite actualizar values que NO son dicts en data.
// Tambien permite insertar nuevas keys en data asignandoles cualquier value. Esto sucede cuando la key de update
// no existe en data.
// La estructura de datos en data puede ser considerada un arbol donde las ramas estan compuestas por values que son dicts
// y las hojas con values que no son dicts.
// Leafs (hojas) son considerados todos los values que no son dict en data. Eso es lo que se permite actualizar en data.
// Esta funcion permite insertar una rama en data a condicion de que la key de la raiz (value sera un dict) de dicha rama
// no exista en data.
// ATENCION: update no debe ser modificado despues de llamar a esta funcion pues puede tener objetos compartidos
// con data y se modificaran. """
func MergeDicts(data dict, update dict) {

	type Node struct {
		A dict
		B dict
	}

	nodes := []Node{{data, update}}

	for {
		if len(nodes) == 0 {
			break
		}

		r := nodes[0]
		nodes = nodes[1:]

		for x := range r.B {
			if _, ok := r.A[x]; ok {
				if vb, ok := r.B[x].(dict); ok {
					if va, ok := r.A[x].(dict); ok {
						// Los dos son dict asi que la pareja se añade a la lista de nodos para seguir buscando.
						nodes = append(nodes, Node{va, vb})
					} else {
						// Error: Se intenta asignar un dict a algo que NO es un dict en data.
						panic(0)
					}
				} else {
					if _, ok := r.A[x].(dict); ok {
						// Error: Se intenta asignar un dict a algo que NO es un dict en data.
						panic(0)
					} else {
						// UPDATE: r.A y r.B no son dicts.
						r.A[x] = r.B[x]
					}
				}
			} else {
				// La key x no existe en r.A asi que se inserta la rama r.B[x] en r.A[x]
				r.A[x] = r.B[x]
			}
		}
	}
}

// Intercepta la finalizacion del programa mediante la pulsacion de la tecla Control-C.
func EnableControlCHandler() {
	c := make(chan os.Signal)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-c
		// cleanup()
		fmt.Println("Exiting...")
		os.Exit(1)
	}()
}
