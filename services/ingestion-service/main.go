package main

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
	"github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs"
	common "github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs/common"
	events "github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs/events"
	"github.com/parquet-go/parquet-go"
)

type Config struct {
	Port        string
	DatabaseURL string
	DataPath    string
}

type IngestionService struct {
	config *Config
	db     *sql.DB
}

type UploadResponse struct {
	ID       string `json:"id"`
	Filename string `json:"filename"`
	Size     int64  `json:"size"`
	Status   string `json:"status"`
	Message  string `json:"message"`
}

type ProcessingStatus struct {
	ID        string    `json:"id"`
	Filename  string    `json:"filename"`
	Status    string    `json:"status"`
	Progress  int       `json:"progress"`
	StartedAt time.Time `json:"started_at"`
	Message   string    `json:"message,omitempty"`
}

// TickData represents one row per tick per demo (global state)
type TickData struct {
	MatchID      string    `parquet:"match_id,snappy"`
	TickNumber   int32     `parquet:"tick_number,snappy"`
	GameTime     float64   `parquet:"game_time,snappy"`
	MapName      string    `parquet:"map_name,snappy"`
	Round        int32     `parquet:"round,snappy"`
	ScoreTeamA   int32     `parquet:"score_team_a,snappy"`
	ScoreTeamB   int32     `parquet:"score_team_b,snappy"`
	Phase        string    `parquet:"phase,snappy"`
	BombPlanted  bool      `parquet:"bomb_planted,snappy"`
	BombDefused  bool      `parquet:"bomb_defused,snappy"`
	BombExploded bool      `parquet:"bomb_exploded,snappy"`
	Timestamp    time.Time `parquet:"timestamp,snappy"`
}

// PlayerTickData represents one row per tick per player (player state)
type PlayerTickData struct {
	MatchID       string    `parquet:"match_id,snappy"`
	TickNumber    int32     `parquet:"tick_number,snappy"`
	GameTime      float64   `parquet:"game_time,snappy"`
	SteamID       uint64    `parquet:"steam_id,snappy"`
	Name          string    `parquet:"name,snappy"`
	Team          string    `parquet:"team,snappy"`
	Health        int32     `parquet:"health,snappy"`
	Armor         int32     `parquet:"armor,snappy"`
	Money         int32     `parquet:"money,snappy"`
	PosX          float64   `parquet:"pos_x,snappy"`
	PosY          float64   `parquet:"pos_y,snappy"`
	PosZ          float64   `parquet:"pos_z,snappy"`
	VelX          float64   `parquet:"vel_x,snappy"`
	VelY          float64   `parquet:"vel_y,snappy"`
	VelZ          float64   `parquet:"vel_z,snappy"`
	ViewX         float32   `parquet:"view_x,snappy"`
	ViewY         float32   `parquet:"view_y,snappy"`
	IsAlive       bool      `parquet:"is_alive,snappy"`
	IsBot         bool      `parquet:"is_bot,snappy"`
	IsScoped      bool      `parquet:"is_scoped,snappy"`
	IsDefusing    bool      `parquet:"is_defusing,snappy"`
	HasBomb       bool      `parquet:"has_bomb,snappy"`
	ActiveWeapon  string    `parquet:"active_weapon,snappy"`
	FlashDuration float32   `parquet:"flash_duration,snappy"`
	Timestamp     time.Time `parquet:"timestamp,snappy"`
}

// ProcessingResult contains the result of demo processing
type ProcessingResult struct {
	MatchID      string `json:"match_id"`
	TicksFile    string `json:"ticks_file"`
	PlayerFile   string `json:"player_file"`
	TotalTicks   int    `json:"total_ticks"`
	TotalPlayers int    `json:"total_players"`
	MapName      string `json:"map_name"`
	ProcessedAt  string `json:"processed_at"`
}

func NewConfig() *Config {
	return &Config{
		Port:        getEnvWithDefault("PORT", "8080"),
		DatabaseURL: getEnvWithDefault("DATABASE_URL", ""),
		DataPath:    getEnvWithDefault("DATA_PATH", "/app/data"),
	}
}

func getEnvWithDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func NewIngestionService(config *Config) (*IngestionService, error) {
	var db *sql.DB
	var err error

	// Ensure data directory exists
	if err := os.MkdirAll(config.DataPath, 0755); err != nil {
		return nil, fmt.Errorf("failed to create data directory: %w", err)
	}

	// Only connect to database if URL is provided
	if config.DatabaseURL != "" {
		db, err = sql.Open("postgres", config.DatabaseURL)
		if err != nil {
			return nil, fmt.Errorf("failed to connect to database: %w", err)
		}

		// Test the connection
		if err := db.Ping(); err != nil {
			log.Printf("Warning: Could not ping database: %v", err)
		} else {
			log.Println("Successfully connected to database")
		}
	}

	return &IngestionService{
		config: config,
		db:     db,
	}, nil
}

func (is *IngestionService) setupRoutes() *gin.Engine {
	// Set Gin to release mode for production
	gin.SetMode(gin.ReleaseMode)

	r := gin.Default()

	// Health check endpoint
	r.GET("/health", func(c *gin.Context) {
		status := gin.H{
			"status":  "healthy",
			"service": "ingestion-service",
			"port":    is.config.Port,
		}

		// Check database connection if available
		if is.db != nil {
			if err := is.db.Ping(); err != nil {
				status["database"] = "unhealthy"
				status["database_error"] = err.Error()
				c.JSON(http.StatusServiceUnavailable, status)
				return
			}
			status["database"] = "healthy"
		} else {
			status["database"] = "not_configured"
		}

		// Check data directory
		if _, err := os.Stat(is.config.DataPath); err != nil {
			status["data_directory"] = "unhealthy"
			status["data_directory_error"] = err.Error()
			c.JSON(http.StatusServiceUnavailable, status)
			return
		}
		status["data_directory"] = "healthy"

		c.JSON(http.StatusOK, status)
	})

	// Ready check endpoint
	r.GET("/ready", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "ready",
			"service": "ingestion-service",
		})
	})

	// Configuration endpoint
	r.GET("/config", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"port":         is.config.Port,
			"database_url": maskConnectionString(is.config.DatabaseURL),
			"data_path":    is.config.DataPath,
			"message":      "Ingestion service is running and reading configuration from environment variables",
		})
	})

	// Demo upload endpoint
	r.POST("/upload", is.handleDemoUpload)

	// Processing status endpoint
	r.GET("/status/:id", is.getProcessingStatus)

	// List uploaded demos
	r.GET("/demos", is.listDemos)

	return r
}

func (is *IngestionService) handleDemoUpload(c *gin.Context) {
	// Get the uploaded file
	file, header, err := c.Request.FormFile("demo")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "No file uploaded",
			"message": "Please upload a .dem file",
		})
		return
	}
	defer file.Close()

	// Create temporary file to save the uploaded demo
	tempFile, err := os.CreateTemp(is.config.DataPath, "upload_*.dem")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to create temporary file",
			"message": err.Error(),
		})
		return
	}
	tempPath := tempFile.Name()
	defer func() {
		tempFile.Close()
		os.Remove(tempPath) // Clean up temp file
	}()

	// Copy uploaded file to temp file
	size, err := io.Copy(tempFile, file)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to save uploaded file",
			"message": err.Error(),
		})
		return
	}
	tempFile.Close() // Close before processing

	// Generate match ID from file content
	matchID, err := generateMatchID(tempPath)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to generate match ID",
			"message": err.Error(),
		})
		return
	}

	log.Printf("Demo uploaded: Filename=%s, Size=%d bytes, MatchID=%s", header.Filename, size, matchID)

	// Process the demo file and generate Parquet files
	result, err := is.processDemoFile(tempPath, matchID)
	if err != nil {
		log.Printf("Demo processing failed for match %s: %v", matchID, err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to process demo file",
			"message": err.Error(),
		})
		return
	}

	log.Printf("Demo processing completed for match %s: %d ticks, %d players",
		matchID, result.TotalTicks, result.TotalPlayers)

	// Return processing result
	response := gin.H{
		"match_id":      result.MatchID,
		"filename":      header.Filename,
		"size":          size,
		"status":        "processed",
		"message":       "Demo file processed successfully",
		"ticks_file":    result.TicksFile,
		"player_file":   result.PlayerFile,
		"total_ticks":   result.TotalTicks,
		"total_players": result.TotalPlayers,
		"map_name":      result.MapName,
		"processed_at":  result.ProcessedAt,
	}

	c.JSON(http.StatusOK, response)
}

func (is *IngestionService) getProcessingStatus(c *gin.Context) {
	id := c.Param("id")

	// Placeholder implementation
	status := ProcessingStatus{
		ID:        id,
		Filename:  "example.dem",
		Status:    "processing",
		Progress:  75,
		StartedAt: time.Now().Add(-5 * time.Minute),
		Message:   "Parsing game events...",
	}

	c.JSON(http.StatusOK, status)
}

func (is *IngestionService) listDemos(c *gin.Context) {
	// List files in data directory
	files, err := os.ReadDir(is.config.DataPath)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to list demos",
			"message": err.Error(),
		})
		return
	}

	demos := make([]gin.H, 0)
	for _, file := range files {
		if !file.IsDir() {
			info, _ := file.Info()
			demos = append(demos, gin.H{
				"name":     file.Name(),
				"size":     info.Size(),
				"modified": info.ModTime(),
			})
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"demos":     demos,
		"count":     len(demos),
		"data_path": is.config.DataPath,
	})
}

// generateMatchID creates a unique match ID from file content hash
func generateMatchID(filePath string) (string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	hasher := sha256.New()
	if _, err := io.Copy(hasher, file); err != nil {
		return "", err
	}

	hash := hex.EncodeToString(hasher.Sum(nil))
	return hash[:16], nil // Use first 16 characters for shorter ID
}

// createOutputPaths creates the directory structure for output files
func createOutputPaths(dataPath, matchID, mapName string) (string, string, error) {
	now := time.Now()
	datePart := now.Format("2006-01-02")

	// Clean map name for filesystem
	cleanMapName := strings.ReplaceAll(mapName, "/", "_")
	cleanMapName = strings.ReplaceAll(cleanMapName, "\\", "_")
	if cleanMapName == "" {
		cleanMapName = "unknown"
	}

	outputDir := filepath.Join(dataPath, "processed", datePart, cleanMapName, matchID)
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return "", "", fmt.Errorf("failed to create output directory: %w", err)
	}

	ticksFile := filepath.Join(outputDir, "ticks.parquet")
	playerFile := filepath.Join(outputDir, "player_ticks.parquet")

	return ticksFile, playerFile, nil
}

// writeParquetFile writes data to a Parquet file
func writeParquetFile(filePath string, data interface{}) error {
	file, err := os.Create(filePath)
	if err != nil {
		return fmt.Errorf("failed to create file %s: %w", filePath, err)
	}
	defer file.Close()

	// Create schema based on data type
	var schema *parquet.Schema
	switch data.(type) {
	case []TickData:
		schema = parquet.SchemaOf(new(TickData))
	case []PlayerTickData:
		schema = parquet.SchemaOf(new(PlayerTickData))
	default:
		return fmt.Errorf("unsupported data type for Parquet writing")
	}

	writer := parquet.NewWriter(file, schema)
	defer writer.Close()

	// Write data
	switch d := data.(type) {
	case []TickData:
		for _, item := range d {
			if err := writer.Write(&item); err != nil {
				return fmt.Errorf("failed to write tick data: %w", err)
			}
		}
	case []PlayerTickData:
		for _, item := range d {
			if err := writer.Write(&item); err != nil {
				return fmt.Errorf("failed to write player data: %w", err)
			}
		}
	}

	return nil
}

// processDemoFile parses a CS2 demo file and generates Parquet files
func (is *IngestionService) processDemoFile(demoPath, matchID string) (*ProcessingResult, error) {
	log.Printf("Starting demo processing for match %s", matchID)

	// Open demo file
	file, err := os.Open(demoPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open demo file: %w", err)
	}
	defer file.Close()

	// Create demo parser
	parser := demoinfocs.NewParser(file)
	defer parser.Close()

	var mapName string
	var processedFrames int
	playerSet := make(map[uint64]bool)

	// Simple event-based approach to collect data
	var ticksData []TickData
	var playersData []PlayerTickData

	// Register event handler for frame completion
	parser.RegisterEventHandler(func(e events.FrameDone) {
		gameState := parser.GameState()
		tick := gameState.IngameTick()

		// Skip negative or very early ticks
		if tick <= 0 {
			return
		}

		// Get map name if not set
		if mapName == "" {
			// Try to get it from various sources
			mapName = "unknown" // Default fallback
		}

		// Create tick data (simplified)
		tickData := TickData{
			MatchID:      matchID,
			TickNumber:   int32(tick),
			GameTime:     float64(tick) / 64.0, // Approximate using tick rate
			MapName:      mapName,
			Round:        int32(gameState.TotalRoundsPlayed()),
			ScoreTeamA:   int32(gameState.TeamTerrorists().Score()),
			ScoreTeamB:   int32(gameState.TeamCounterTerrorists().Score()),
			Phase:        string(gameState.GamePhase()),
			BombPlanted:  false,      // Will be updated by events
			BombDefused:  false,      // Will be updated by events
			BombExploded: false,      // Will be updated by events
			Timestamp:    time.Now(), // Simple timestamp
		}
		ticksData = append(ticksData, tickData)

		// Write player data for each connected player
		for _, player := range gameState.Participants().All() {
			if player == nil || !player.IsConnected {
				continue
			}

			playerSet[player.SteamID64] = true

			var teamName string
			if player.Team == common.TeamTerrorists {
				teamName = "T"
			} else if player.Team == common.TeamCounterTerrorists {
				teamName = "CT"
			} else {
				teamName = "SPEC"
			}

			pos := player.Position()

			playerData := PlayerTickData{
				MatchID:       matchID,
				TickNumber:    int32(tick),
				GameTime:      float64(tick) / 64.0,
				SteamID:       player.SteamID64,
				Name:          player.Name,
				Team:          teamName,
				Health:        int32(player.Health()),
				Armor:         int32(player.Armor()),
				Money:         int32(player.Money()),
				PosX:          float64(pos.X),
				PosY:          float64(pos.Y),
				PosZ:          float64(pos.Z),
				VelX:          0, // Velocity not easily accessible in v5
				VelY:          0,
				VelZ:          0,
				ViewX:         player.ViewDirectionX(),
				ViewY:         player.ViewDirectionY(),
				IsAlive:       player.IsAlive(),
				IsBot:         player.IsBot,
				IsScoped:      player.IsScoped(),
				IsDefusing:    player.IsDefusing,
				HasBomb:       false, // Would need bomb state checking
				ActiveWeapon:  "",    // Would need weapon checking
				FlashDuration: player.FlashDuration,
				Timestamp:     time.Now(),
			}
			playersData = append(playersData, playerData)
		}

		processedFrames++

		// Log progress every 1000 frames
		if processedFrames%1000 == 0 {
			log.Printf("Processed %d frames for match %s", processedFrames, matchID)
		}
	})

	// Register bomb event handlers to update state (simplified)
	parser.RegisterEventHandler(func(e events.BombPlanted) {
		// Update last tick data if available
		if len(ticksData) > 0 {
			ticksData[len(ticksData)-1].BombPlanted = true
		}
	})

	parser.RegisterEventHandler(func(e events.BombDefused) {
		if len(ticksData) > 0 {
			ticksData[len(ticksData)-1].BombDefused = true
		}
	})

	parser.RegisterEventHandler(func(e events.BombExplode) {
		if len(ticksData) > 0 {
			ticksData[len(ticksData)-1].BombExploded = true
		}
	})

	// Parse the entire demo
	err = parser.ParseToEnd()
	if err != nil {
		return nil, fmt.Errorf("demo parsing error: %w", err)
	}

	// Set default map name if still empty
	if mapName == "" {
		mapName = "unknown"
	}

	// Create output file paths
	ticksFile, playerFile, err := createOutputPaths(is.config.DataPath, matchID, mapName)
	if err != nil {
		return nil, err
	}

	// Write Parquet files
	if len(ticksData) > 0 {
		err = writeParquetFile(ticksFile, ticksData)
		if err != nil {
			return nil, fmt.Errorf("failed to write ticks parquet file: %w", err)
		}
	}

	if len(playersData) > 0 {
		err = writeParquetFile(playerFile, playersData)
		if err != nil {
			return nil, fmt.Errorf("failed to write players parquet file: %w", err)
		}
	}

	log.Printf("Demo processing completed for match %s: %d ticks, %d players, Map: %s",
		matchID, len(ticksData), len(playerSet), mapName)

	return &ProcessingResult{
		MatchID:      matchID,
		TicksFile:    ticksFile,
		PlayerFile:   playerFile,
		TotalTicks:   len(ticksData),
		TotalPlayers: len(playerSet),
		MapName:      mapName,
		ProcessedAt:  time.Now().Format(time.RFC3339),
	}, nil
}

func maskConnectionString(connectionString string) string {
	if connectionString == "" {
		return "not configured"
	}
	return "configured (masked for security)"
}

func main() {
	log.Println("Starting Ingestion Service...")

	// Load configuration from environment variables
	config := NewConfig()
	log.Printf("Loaded configuration: Port=%s, DataPath=%s", config.Port, config.DataPath)

	// Create ingestion service instance
	ingestionService, err := NewIngestionService(config)
	if err != nil {
		log.Fatalf("Failed to create ingestion service: %v", err)
	}

	// Setup routes
	router := ingestionService.setupRoutes()

	// Start server
	addr := ":" + config.Port
	log.Printf("Ingestion Service listening on %s", addr)
	log.Printf("Health check available at: http://localhost:%s/health", config.Port)
	log.Printf("Data directory: %s", config.DataPath)

	if err := router.Run(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
