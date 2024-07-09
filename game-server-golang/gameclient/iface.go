package main

// import "io"

// type A struct {
// 	Data int64
// }

// // type B struct {
// // 	Data int64
// // }

// // type Writable interface {
// // 	Write(data []interface{})
// // 	Write2(pb interface{})
// // }

// // func (a A) Write(data []interface{}) {
// // 	a.Data = int64(data[0].(int64))
// // }

// // func (a A) Write2(pb interface{}) {
// // 	a.Data = pb.(B).Data
// // }

// // func (b B) Write(data []interface{}) {
// // 	b.Data = int64(data[0].(int64))
// // }

// // func (b B) Write2(pb interface{}) {
// // 	b.Data = pb.(B).Data
// // }

// // func Trace(c Writable) {
// // 	d := 2
// // 	c.Write2(interface{}(d))
// // }

// //go:noinline
// func (a *A) Read(p []byte) (n int, err error) {
// 	// P = p
// 	return len(p), nil
// }

// var GA A = A{}

// // var P []byte

// //go:noinline
// func test() {
// 	a := A{}
// 	// x := Writable(a)
// 	// x.Write2(2)

// 	// Trace(x)

// 	z := make(map[string]io.Reader)
// 	z["2"] = nil //&a
// 	v := []io.Reader{&a}
// 	u := []io.Reader{}
// 	u = append(u, nil)
// 	g := make([]byte, 0, 100)

// 	v[0].(*A).Read(g)
// 	u[0].(*A).Read(g)

// 	// a := A{}
// 	// b := B{}
// 	// b2 := B{}

// 	// f := make([]interface{}, 2, 10)
// 	// f[0] = 1
// 	// // f2 := 2
// 	// var uu interface{}

// 	// tt := []Writable{a, b}

// 	// ii := tt[1]

// 	// ii.Write(f)
// 	// // ii.Write2(b2)
// 	// tt[1].(B).Write2(b2)

// 	// // tt[1].Write2(b2)

// 	// // a.Write(f)
// 	// // b2.Write2(b)

// }
