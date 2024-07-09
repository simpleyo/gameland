package main

import (
	"bytes"
	"fmt"
	"image"
	_ "image/png"
	"log"
	"math"
	"math/rand"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/ebitenutil"
	"github.com/hajimehoshi/ebiten/v2/examples/resources/images"
)

const (
	screenWidth  = 480
	screenHeight = 270
	maxAngle     = 256
)

var (
	ebitenImage *ebiten.Image
)

var theOutsideWidth, theOutsideHeight int

var recvChannel <-chan string // Canal para recibir los mensajes desde el gameserver.

func init() {
	// Decode an image from the image file's byte slice.
	// Now the byte slice is generated with //go:generate for Go 1.15 or older.
	// If you use Go 1.16 or newer, it is strongly recommended to use //go:embed to embed the image file.
	// See https://pkg.go.dev/embed for more details.
	img, _, err := image.Decode(bytes.NewReader(images.Ebiten_png))
	if err != nil {
		log.Fatal(err)
	}
	origEbitenImage := ebiten.NewImageFromImage(img)

	w, h := origEbitenImage.Size()
	ebitenImage = ebiten.NewImage(w, h)

	op := &ebiten.DrawImageOptions{}
	op.ColorM.Scale(1, 1, 1, 0.5)
	ebitenImage.DrawImage(origEbitenImage, op)
}

type Sprite struct {
	imageWidth  int
	imageHeight int
	x           int
	y           int
	vx          int
	vy          int
	angle       int
}

func (s *Sprite) Update() {
	s.x += s.vx
	s.y += s.vy
	if s.x < 0 {
		s.x = -s.x
		s.vx = -s.vx
	} else if mx := screenWidth - s.imageWidth; mx <= s.x {
		s.x = 2*mx - s.x
		s.vx = -s.vx
	}
	if s.y < 0 {
		s.y = -s.y
		s.vy = -s.vy
	} else if my := screenHeight - s.imageHeight; my <= s.y {
		s.y = 2*my - s.y
		s.vy = -s.vy
	}
	s.angle++
	if s.angle == maxAngle {
		s.angle = 0
	}
}

type Sprites struct {
	sprites []*Sprite
	num     int
}

func (s *Sprites) Update() {
	for i := 0; i < s.num; i++ {
		s.sprites[i].Update()
	}
}

const (
	MinSprites = 0
	MaxSprites = 50000
)

type Game struct {
	touchIDs []ebiten.TouchID
	sprites  Sprites
	op       ebiten.DrawImageOptions
	inited   bool
}

func (g *Game) init() {
	defer func() {
		g.inited = true
	}()

	g.sprites.sprites = make([]*Sprite, MaxSprites)
	g.sprites.num = 500
	for i := range g.sprites.sprites {
		w, h := ebitenImage.Size()
		x, y := rand.Intn(screenWidth-w), rand.Intn(screenHeight-h)
		vx, vy := 2*rand.Intn(2)-1, 2*rand.Intn(2)-1
		a := rand.Intn(maxAngle)
		g.sprites.sprites[i] = &Sprite{
			imageWidth:  w,
			imageHeight: h,
			x:           x,
			y:           y,
			vx:          vx,
			vy:          vy,
			angle:       a,
		}
	}
}

func (g *Game) leftTouched() bool {
	for _, id := range g.touchIDs {
		x, _ := ebiten.TouchPosition(id)
		if x < screenWidth/2 {
			return true
		}
	}
	return false
}

func (g *Game) rightTouched() bool {
	for _, id := range g.touchIDs {
		x, _ := ebiten.TouchPosition(id)
		if x >= screenWidth/2 {
			return true
		}
	}
	return false
}

func (g *Game) Update() error {
	if !g.inited {
		g.init()
	}
	g.touchIDs = ebiten.AppendTouchIDs(g.touchIDs[:0])

	// Verificar si hay mensajes del servidor
	select {
	case msg := <-recvChannel:
		// Procesar el mensaje del servidor
		fmt.Println("Mensaje del servidor:", msg)
	default:
		// No hay mensajes del servidor, continuar con el bucle del juego
	}

	// Decrease the number of the sprites.
	if ebiten.IsKeyPressed(ebiten.KeyArrowLeft) || g.leftTouched() {
		g.sprites.num -= 20
		if g.sprites.num < MinSprites {
			g.sprites.num = MinSprites
		}
	}

	// Increase the number of the sprites.
	if ebiten.IsKeyPressed(ebiten.KeyArrowRight) || g.rightTouched() {
		g.sprites.num += 20
		if MaxSprites < g.sprites.num {
			g.sprites.num = MaxSprites
		}
	}

	g.sprites.Update()
	return nil
}

// Draw renders the game sprites onto the screen image.
func (g *Game) Draw(screen *ebiten.Image) {
	// Draw each sprite.
	// DrawImage can be called many times, but the actual draw call to the GPU is minimal
	// because certain conditions are satisfied, such as all rendering sources and targets being the same.
	// For more details, see: https://pkg.go.dev/github.com/hajimehoshi/ebiten/v2#Image.DrawImage
	w, h := ebitenImage.Size()
	for i := 0; i < g.sprites.num; i++ {
		s := g.sprites.sprites[i]

		// Reset the geometric matrix.
		g.op.GeoM.Reset()

		// Translate the matrix to the center of the image.
		g.op.GeoM.Translate(-float64(w)/2, -float64(h)/2)

		// Rotate the matrix based on the sprite's angle.
		g.op.GeoM.Rotate(2 * math.Pi * float64(s.angle) / maxAngle)

		// Translate the matrix back to the original position.
		g.op.GeoM.Translate(float64(w)/2, float64(h)/2)

		// Translate the matrix to the sprite's position.
		g.op.GeoM.Translate(float64(s.x), float64(s.y))

		// Draw the sprite image onto the screen.
		screen.DrawImage(ebitenImage, &g.op)
	}

	// Create a message with the current TPS, FPS, number of sprites, and other information.
	msg := fmt.Sprintf(`TPS: %0.2f
FPS: %0.2f
Num of sprites: %d
Press <- or -> to change the number of sprites
OutSize: %d, %d`, ebiten.CurrentTPS(), ebiten.CurrentFPS(), g.sprites.num, theOutsideWidth, theOutsideHeight)

	// Draw the debug message onto the screen.
	ebitenutil.DebugPrint(screen, msg)
}

func (g *Game) Layout(outsideWidth, outsideHeight int) (int, int) {
	theOutsideWidth = outsideWidth
	theOutsideHeight = outsideHeight
	return screenWidth, screenHeight
}

func RunGame(messages <-chan string, send chan<- string) {
	recvChannel = messages

	// ebiten.SetWindowClosingHandled(true)
	ebiten.SetWindowSize(screenWidth*2, screenHeight*2)
	ebiten.SetWindowTitle("Sprites (Ebiten Demo)")
	ebiten.SetWindowDecorated(true)
	ebiten.SetWindowResizingMode(ebiten.WindowResizingModeEnabled)
	if err := ebiten.RunGame(&Game{}); err != nil {
		log.Fatal(err)
	}
}
