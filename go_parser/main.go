package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	dem "github.com/markus-wa/demoinfocs-golang/v4/pkg/demoinfocs"
	common "github.com/markus-wa/demoinfocs-golang/v4/pkg/demoinfocs/common"
	events "github.com/markus-wa/demoinfocs-golang/v4/pkg/demoinfocs/events"
)

type TickData struct {
	Tick         int     `json:"tick"`
	RoundNum     int     `json:"round_num"`
	Seconds      float64 `json:"seconds"`
	ClockTime    string  `json:"clock_time"`
	TScore       int     `json:"t_score"`
	CTScore      int     `json:"ct_score"`
	SteamID      uint64  `json:"steam_id"`
	Name         string  `json:"name"`
	Team         string  `json:"team"`
	Side         string  `json:"side"`
	IsAlive      bool    `json:"is_alive"`
	HP           int     `json:"hp"`
	Armor        int     `json:"armor"`
	X            float64 `json:"x"`
	Y            float64 `json:"y"`
	Z            float64 `json:"z"`
	ViewX        float64 `json:"view_x"`
	ViewY        float64 `json:"view_y"`
	ActiveWeapon string  `json:"active_weapon"`
	DemoFilename string  `json:"demo_filename"`
	MapName      string  `json:"map_name"`
}

type DemoMetadata struct {
	Filename    string `json:"filename"`
	FilePath    string `json:"file_path"`
	MapName     string `json:"map_name"`
	TotalRounds int    `json:"total_rounds"`
	TotalTicks  int    `json:"total_ticks"`
	Team1Score  int    `json:"team1_score"`
	Team2Score  int    `json:"team2_score"`
	Duration    int    `json:"duration_seconds"`
}

func main() {
	if len(os.Args) < 2 {
		log.Fatal("Usage: go run main.go <demo_file_path>")
	}

	demoPath := os.Args[1]
	fmt.Printf("🚀 Go Demo Parser - Processing: %s\n", filepath.Base(demoPath))

	startTime := time.Now()

	// Parse the demo
	metadata, ticks, err := parseDemoFile(demoPath)
	if err != nil {
		log.Fatalf("❌ Error parsing demo: %v", err)
	}

	parseTime := time.Since(startTime)
	fmt.Printf("📊 Parsing completed in %.2f seconds\n", parseTime.Seconds())
	fmt.Printf("📈 Found %d ticks, %d rounds\n", len(ticks), metadata.TotalRounds)

	// Export to JSON for Python integration
	if err := exportToJSON(metadata, ticks, demoPath); err != nil {
		log.Fatalf("❌ Error exporting JSON: %v", err)
	}

	totalTime := time.Since(startTime)
	ticksPerSecond := float64(len(ticks)) / totalTime.Seconds()

	fmt.Printf("✅ Processing completed!\n")
	fmt.Printf("⏱️  Total time: %.2f seconds\n", totalTime.Seconds())
	fmt.Printf("🔥 Performance: %.0f ticks/second\n", ticksPerSecond)
}

func parseDemoFile(demoPath string) (*DemoMetadata, []TickData, error) {
	file, err := os.Open(demoPath)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to open demo file: %w", err)
	}
	defer file.Close()

	parser := dem.NewParser(file)
	defer parser.Close()

	// Get demo header info
	header, err := parser.ParseHeader()
	if err != nil {
		return nil, nil, fmt.Errorf("failed to parse header: %w", err)
	}

	metadata := &DemoMetadata{
		Filename: filepath.Base(demoPath),
		FilePath: demoPath,
		MapName:  header.MapName,
	}

	var ticks []TickData
	var currentRound int
	var team1Score, team2Score int

	// Track round changes
	parser.RegisterEventHandler(func(e events.RoundStart) {
		currentRound++
	})

	// Track score updates
	parser.RegisterEventHandler(func(e events.RoundEnd) {
		gs := parser.GameState()
		if gs.TeamTerrorists() != nil {
			team1Score = gs.TeamTerrorists().Score()
		}
		if gs.TeamCounterTerrorists() != nil {
			team2Score = gs.TeamCounterTerrorists().Score()
		}
	})

	// Progress tracking
	tickCount := 0
	lastProgress := time.Now()

	// Parse each frame/tick
	for ok, err := parser.ParseNextFrame(); ok; ok, err = parser.ParseNextFrame() {
		if err != nil {
			return nil, nil, fmt.Errorf("error parsing frame: %w", err)
		}

		gs := parser.GameState()
		if gs == nil {
			continue
		}

		// Progress reporting every 50,000 ticks
		tickCount++
		if tickCount%50000 == 0 {
			elapsed := time.Since(lastProgress)
			fmt.Printf("📊 Processed %d ticks (%.0f ticks/sec)\n", tickCount, 50000.0/elapsed.Seconds())
			lastProgress = time.Now()
		}

		// Extract tick data for each player
		for _, player := range gs.Participants().All() {
			if player == nil {
				continue
			}

			// Get weapon info
			activeWeapon := ""
			if player.ActiveWeapon() != nil {
				activeWeapon = player.ActiveWeapon().String()
			}

			// Get team info
			teamName := ""
			side := ""
			if player.Team != common.TeamUnassigned {
				if player.Team == common.TeamTerrorists {
					teamName = "T"
					side = "T"
				} else if player.Team == common.TeamCounterTerrorists {
					teamName = "CT"
					side = "CT"
				}
			}

			// Create tick data
			tickData := TickData{
				Tick:         gs.IngameTick(),
				RoundNum:     currentRound,
				Seconds:      float64(gs.TotalRoundsPlayed()) * 115.0, // Approximate
				ClockTime:    "",                                      // TODO: Calculate actual clock time
				TScore:       team1Score,
				CTScore:      team2Score,
				SteamID:      player.SteamID64,
				Name:         player.Name,
				Team:         teamName,
				Side:         side,
				IsAlive:      player.IsAlive(),
				HP:           player.Health(),
				Armor:        player.Armor(),
				X:            float64(player.Position().X),
				Y:            float64(player.Position().Y),
				Z:            float64(player.Position().Z),
				ViewX:        float64(player.ViewDirectionX()),
				ViewY:        float64(player.ViewDirectionY()),
				ActiveWeapon: activeWeapon,
				DemoFilename: metadata.Filename,
				MapName:      metadata.MapName,
			}

			ticks = append(ticks, tickData)
		}
	}

	// Update metadata
	metadata.TotalTicks = len(ticks)
	metadata.TotalRounds = currentRound
	metadata.Team1Score = team1Score
	metadata.Team2Score = team2Score

	return metadata, ticks, nil
}

func exportToJSON(metadata *DemoMetadata, ticks []TickData, demoPath string) error {
	// Create output directory
	outputDir := "../go_parser_output"
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	baseName := strings.TrimSuffix(filepath.Base(demoPath), filepath.Ext(demoPath))

	// Export metadata
	metadataFile := filepath.Join(outputDir, baseName+"_metadata.json")
	if err := writeJSONFile(metadataFile, metadata); err != nil {
		return fmt.Errorf("failed to write metadata: %w", err)
	}

	// Export ticks data (chunked for large files)
	chunkSize := 100000 // 100k ticks per file
	totalChunks := (len(ticks) + chunkSize - 1) / chunkSize

	fmt.Printf("📁 Exporting %d ticks in %d chunks...\n", len(ticks), totalChunks)

	for i := 0; i < totalChunks; i++ {
		start := i * chunkSize
		end := start + chunkSize
		if end > len(ticks) {
			end = len(ticks)
		}

		chunk := ticks[start:end]
		chunkFile := filepath.Join(outputDir, fmt.Sprintf("%s_ticks_%d.json", baseName, i))

		if err := writeJSONFile(chunkFile, chunk); err != nil {
			return fmt.Errorf("failed to write chunk %d: %w", i, err)
		}
	}

	fmt.Printf("📁 Exported to: %s\n", outputDir)
	return nil
}

func writeJSONFile(filename string, data interface{}) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	return encoder.Encode(data)
}
