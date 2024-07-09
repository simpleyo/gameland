package main

import (
	"fmt"
)

type Wheel struct {
	Size int
}

type Car struct {
	Name string
	Wheel
}

func (wheel *Wheel) GetWheelSize() int {
	return wheel.Size
}

type Event interface {
	Handle()
}

type MyEvent1 struct {
	Value int
	other int
}
type MyEvent2 struct {
	Text string
}

func (e *MyEvent1) Handle() {
	// e.Value = 7
}
func (e MyEvent2) Handle() {
}

func (e *MyEvent1) Add(a int, b int) int {
	e.other = a + b
	return e.other
}

// loop is a function that continuously listens to the ch channel and processes the received events.
// It sends a boolean value to the rch channel after processing each event.
func loop(ch chan Event, rch chan<- bool) {
	// var m1 *MyEvent1
	for {
		select {
		case v := <-ch:
			// Check if the received event is of type *MyEvent1
			if d, ok := v.(*MyEvent1); ok {
				fmt.Println("MyEvent1: ", d.Value)
				// m1 = &d
				d.Value = 8
				rch <- true
			} 
			// Check if the received event is of type MyEvent2
			else if d, ok := v.(MyEvent2); ok {
				fmt.Println("MyEvent2: ", d.Text)
				// fmt.Println("MyEvent1: ", m1.Value)
				rch <- true
			}
		}
	}
}

type Float interface {
	~float32 | ~float64
}

func Add[T Float](a T, b T) T {
	return a + b
}

func main() {

	// Array numérico, se inicializan a 0
	var numbers [5]int
	fmt.Println(numbers) // Output: [0 0 0 0 0]

	c := Car{}

	c.Size = 4
	fmt.Println("Wheel size: ", c.GetWheelSize(), Add(2., 3.))

	ch := make(chan Event, 10)
	rch := make(chan bool)

	m1 := MyEvent1{1, 0}
	m2 := MyEvent2{"HOLA"}

	m1.Add(1, 1)

	var e1, e11 Event

	// e = m2
	e1 = &m1
	e11 = &m1

	m1.Value = 7

	vv1 := e1.(*MyEvent1)
	vv11 := e11.(*MyEvent1)

	fmt.Println("MyEvent1: ", vv1, vv11)

	go loop(ch, rch)

	ch <- &m1
	<-rch
	fmt.Println("MyEvent1: ", m1.Value)
	m1.Value = 5
	ch <- m2
	<-rch

	for {
	}

}
