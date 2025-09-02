package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	dem "github.com/markus-wa/demoinfocs-golang/v4/pkg/demoinfocs"
	events "github.com/markus-wa/demoinfocs-golang/v4/pkg/demoinfocs/events"
)

func testDemo() {
	if len(os.Args) < 2 {
		log.Fatal("Usage: go run simple_test.go <demo_file_path>")
	}

	demoPath := os.Args[1]
	fmt.Printf("🚀 Go Demo Parser - Testing: %s\n", filepath.Base(demoPath))

	file, err := os.Open(demoPath)
	if err != nil {
		log.Fatalf("❌ Error opening demo file: %v", err)
	}
	defer file.Close()

	parser := dem.NewParser(file)
	defer parser.Close()

	// Parse header
	header, err := parser.ParseHeader()
	if err != nil {
		log.Fatalf("❌ Error parsing header: %v", err)
	}

	fmt.Printf("📍 Map: %s\n", header.MapName)

	startTime := time.Now()
	frameCount := 0
	tickCount := 0
	playerCount := 0

	// Count rounds
	rounds := 0
	parser.RegisterEventHandler(func(e events.RoundStart) {
		rounds++
		if rounds%5 == 0 {
			fmt.Printf("📊 Round %d started\n", rounds)
		}
	})

	// Count kills for excitement
	kills := 0
	parser.RegisterEventHandler(func(e events.Kill) {
		kills++
		if kills%10 == 0 {
			fmt.Printf("💀 %d kills processed\n", kills)
		}
	})

	// Parse frames
	fmt.Println("🔄 Parsing demo frames...")

	for ok, err := parser.ParseNextFrame(); ok; ok, err = parser.ParseNextFrame() {
		if err != nil {
			fmt.Printf("⚠️ Error parsing frame %d: %v\n", frameCount, err)
			continue
		}

		frameCount++

		// Progress every 10000 frames
		if frameCount%10000 == 0 {
			elapsed := time.Since(startTime)
			fps := float64(frameCount) / elapsed.Seconds()
			fmt.Printf("📈 Processed %d frames (%.0f fps)\n", frameCount, fps)
		}

		// Get game state
		gs := parser.GameState()
		if gs == nil {
			continue
		}

		tickCount++

		// Count unique players
		participants := gs.Participants().All()
		if len(participants) > playerCount {
			playerCount = len(participants)
		}

		// Sample some player data every 5000 ticks
		if tickCount%5000 == 0 && len(participants) > 0 {
			player := participants[0]
			if player != nil {
				fmt.Printf("👤 Sample: %s at (%.0f, %.0f, %.0f) HP:%d\n",
					player.Name,
					player.Position().X,
					player.Position().Y,
					player.Position().Z,
					player.Health())
			}
		}
	}

	elapsed := time.Since(startTime)

	fmt.Printf("\n✅ Parsing completed!\n")
	fmt.Printf("⏱️  Total time: %.2f seconds\n", elapsed.Seconds())
	fmt.Printf("📊 Frames processed: %d\n", frameCount)
	fmt.Printf("📊 Ticks processed: %d\n", tickCount)
	fmt.Printf("📊 Rounds: %d\n", rounds)
	fmt.Printf("👥 Players: %d\n", playerCount)
	fmt.Printf("💀 Kills: %d\n", kills)

	if tickCount > 0 {
		fmt.Printf("🚀 Performance: %.0f ticks/second\n", float64(tickCount)/elapsed.Seconds())
	}
	if frameCount > 0 {
		fmt.Printf("🚀 Performance: %.0f frames/second\n", float64(frameCount)/elapsed.Seconds())
	}
}

func main() {
	testDemo()
}
