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
	msg "github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs/msg"
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
	log.Printf("[INIT] Creating new ingestion service with config: Port=%s, DataPath=%s, DatabaseURL=%s",
		config.Port, config.DataPath, maskConnectionString(config.DatabaseURL))

	var db *sql.DB
	var err error

	// Ensure data directory exists
	log.Printf("[INIT] Ensuring data directory exists: %s", config.DataPath)
	if err := os.MkdirAll(config.DataPath, 0755); err != nil {
		log.Printf("[ERROR] Failed to create data directory %s: %v", config.DataPath, err)
		return nil, fmt.Errorf("failed to create data directory: %w", err)
	}
	log.Printf("[INIT] Data directory verified: %s", config.DataPath)

	// Only connect to database if URL is provided
	if config.DatabaseURL != "" {
		log.Printf("[INIT] Attempting database connection...")
		db, err = sql.Open("postgres", config.DatabaseURL)
		if err != nil {
			log.Printf("[ERROR] Failed to open database connection: %v", err)
			return nil, fmt.Errorf("failed to connect to database: %w", err)
		}

		// Test the connection
		log.Printf("[INIT] Testing database connection...")
		if err := db.Ping(); err != nil {
			log.Printf("[WARN] Could not ping database: %v", err)
		} else {
			log.Printf("[INIT] Successfully connected to database")
		}
	} else {
		log.Printf("[INIT] No database URL provided, running without database")
	}

	log.Printf("[INIT] Ingestion service created successfully")
	return &IngestionService{
		config: config,
		db:     db,
	}, nil
}

func (is *IngestionService) setupRoutes() *gin.Engine {
	log.Printf("[ROUTES] Setting up HTTP routes...")

	// Set Gin to release mode for production
	gin.SetMode(gin.ReleaseMode)

	r := gin.Default()

	// Add request logging middleware
	r.Use(gin.LoggerWithFormatter(func(param gin.LogFormatterParams) string {
		return fmt.Sprintf("[HTTP] %s - [%s] \"%s %s %s\" %d %s \"%s\" \"%s\"\n",
			param.ClientIP,
			param.TimeStamp.Format(time.RFC3339),
			param.Method,
			param.Path,
			param.Request.Proto,
			param.StatusCode,
			param.Latency,
			param.Request.UserAgent(),
			param.ErrorMessage,
		)
	}))

	// Health check endpoint
	r.GET("/health", func(c *gin.Context) {
		log.Printf("[HEALTH] Health check requested from %s", c.ClientIP())
		status := gin.H{
			"status":  "healthy",
			"service": "ingestion-service",
			"port":    is.config.Port,
		}

		// Check database connection if available
		if is.db != nil {
			log.Printf("[HEALTH] Checking database connection...")
			if err := is.db.Ping(); err != nil {
				log.Printf("[ERROR] Database health check failed: %v", err)
				status["database"] = "unhealthy"
				status["database_error"] = err.Error()
				c.JSON(http.StatusServiceUnavailable, status)
				return
			}
			log.Printf("[HEALTH] Database connection healthy")
			status["database"] = "healthy"
		} else {
			log.Printf("[HEALTH] Database not configured")
			status["database"] = "not_configured"
		}

		// Check data directory
		log.Printf("[HEALTH] Checking data directory: %s", is.config.DataPath)
		if _, err := os.Stat(is.config.DataPath); err != nil {
			log.Printf("[ERROR] Data directory health check failed: %v", err)
			status["data_directory"] = "unhealthy"
			status["data_directory_error"] = err.Error()
			c.JSON(http.StatusServiceUnavailable, status)
			return
		}
		log.Printf("[HEALTH] Data directory accessible")
		status["data_directory"] = "healthy"

		log.Printf("[HEALTH] Health check completed successfully")
		c.JSON(http.StatusOK, status)
	})

	// Ready check endpoint
	r.GET("/ready", func(c *gin.Context) {
		log.Printf("[READY] Ready check requested from %s", c.ClientIP())
		c.JSON(http.StatusOK, gin.H{
			"status":  "ready",
			"service": "ingestion-service",
		})
	})

	// Configuration endpoint
	r.GET("/config", func(c *gin.Context) {
		log.Printf("[CONFIG] Configuration requested from %s", c.ClientIP())
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

	log.Printf("[ROUTES] HTTP routes configured successfully")
	return r
}

func (is *IngestionService) handleDemoUpload(c *gin.Context) {
	log.Printf("[UPLOAD] Demo upload request received from %s", c.ClientIP())

	// Get the uploaded file
	file, header, err := c.Request.FormFile("demo")
	if err != nil {
		log.Printf("[ERROR] No file uploaded in request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "No file uploaded",
			"message": "Please upload a .dem file",
		})
		return
	}
	defer file.Close()

	log.Printf("[UPLOAD] File received: %s (size: %d bytes)", header.Filename, header.Size)

	// Validate file extension
	if !strings.HasSuffix(strings.ToLower(header.Filename), ".dem") {
		log.Printf("[ERROR] Invalid file type uploaded: %s", header.Filename)
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid file type",
			"message": "Only .dem files are supported",
		})
		return
	}

	// Create temporary file to save the uploaded demo
	log.Printf("[UPLOAD] Creating temporary file in %s", is.config.DataPath)
	tempFile, err := os.CreateTemp(is.config.DataPath, "upload_*.dem")
	if err != nil {
		log.Printf("[ERROR] Failed to create temporary file: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to create temporary file",
			"message": err.Error(),
		})
		return
	}
	tempPath := tempFile.Name()
	log.Printf("[UPLOAD] Created temporary file: %s", tempPath)

	defer func() {
		tempFile.Close()
		log.Printf("[UPLOAD] Cleaning up temporary file: %s", tempPath)
		if removeErr := os.Remove(tempPath); removeErr != nil {
			log.Printf("[WARN] Failed to remove temporary file %s: %v", tempPath, removeErr)
		}
	}()

	// Copy uploaded file to temp file
	log.Printf("[UPLOAD] Copying uploaded file to temporary location...")
	size, err := io.Copy(tempFile, file)
	if err != nil {
		log.Printf("[ERROR] Failed to save uploaded file: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to save uploaded file",
			"message": err.Error(),
		})
		return
	}
	tempFile.Close() // Close before processing
	log.Printf("[UPLOAD] File copied successfully: %d bytes written", size)

	// Generate match ID from file content
	log.Printf("[UPLOAD] Generating match ID from file content...")
	matchID, err := generateMatchID(tempPath)
	if err != nil {
		log.Printf("[ERROR] Failed to generate match ID: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to generate match ID",
			"message": err.Error(),
		})
		return
	}

	log.Printf("[UPLOAD] Demo uploaded successfully: Filename=%s, Size=%d bytes, MatchID=%s", header.Filename, size, matchID)

	// Process the demo file and generate Parquet files
	log.Printf("[PROCESSING] Starting demo processing for match %s...", matchID)
	result, err := is.processDemoFile(tempPath, matchID)
	if err != nil {
		log.Printf("[ERROR] Demo processing failed for match %s: %v", matchID, err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to process demo file",
			"message": err.Error(),
		})
		return
	}

	log.Printf("[PROCESSING] Demo processing completed successfully for match %s: %d ticks, %d players, map: %s",
		matchID, result.TotalTicks, result.TotalPlayers, result.MapName)

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
	log.Printf("[UTIL] Generating match ID for file: %s", filePath)

	file, err := os.Open(filePath)
	if err != nil {
		log.Printf("[ERROR] Failed to open file for hash generation: %v", err)
		return "", err
	}
	defer file.Close()

	hasher := sha256.New()
	bytesRead, err := io.Copy(hasher, file)
	if err != nil {
		log.Printf("[ERROR] Failed to read file for hash generation: %v", err)
		return "", err
	}

	hash := hex.EncodeToString(hasher.Sum(nil))
	matchID := hash[:16] // Use first 16 characters for shorter ID

	log.Printf("[UTIL] Match ID generated successfully: %s (from %d bytes)", matchID, bytesRead)
	return matchID, nil
}

// createOutputPaths creates the directory structure for output files
func createOutputPaths(dataPath, matchID, mapName string) (string, string, error) {
	log.Printf("[UTIL] Creating output paths for match %s on map %s", matchID, mapName)

	now := time.Now()
	datePart := now.Format("2006-01-02")

	// Clean map name for filesystem
	cleanMapName := strings.ReplaceAll(mapName, "/", "_")
	cleanMapName = strings.ReplaceAll(cleanMapName, "\\", "_")
	if cleanMapName == "" {
		cleanMapName = "unknown"
	}
	log.Printf("[UTIL] Cleaned map name: %s -> %s", mapName, cleanMapName)

	outputDir := filepath.Join(dataPath, "processed", datePart, cleanMapName, matchID)
	log.Printf("[UTIL] Creating output directory: %s", outputDir)

	if err := os.MkdirAll(outputDir, 0755); err != nil {
		log.Printf("[ERROR] Failed to create output directory %s: %v", outputDir, err)
		return "", "", fmt.Errorf("failed to create output directory: %w", err)
	}

	ticksFile := filepath.Join(outputDir, "ticks.parquet")
	playerFile := filepath.Join(outputDir, "player_ticks.parquet")

	log.Printf("[UTIL] Output paths created successfully:")
	log.Printf("[UTIL]   - Ticks file: %s", ticksFile)
	log.Printf("[UTIL]   - Players file: %s", playerFile)

	return ticksFile, playerFile, nil
}

// writeParquetFile writes data to a Parquet file
func writeParquetFile(filePath string, data interface{}) error {
	log.Printf("[UTIL] Writing parquet file: %s", filePath)

	file, err := os.Create(filePath)
	if err != nil {
		log.Printf("[ERROR] Failed to create parquet file %s: %v", filePath, err)
		return fmt.Errorf("failed to create file %s: %w", filePath, err)
	}
	defer file.Close()

	// Create schema based on data type
	var schema *parquet.Schema
	var recordCount int

	switch d := data.(type) {
	case []TickData:
		schema = parquet.SchemaOf(new(TickData))
		recordCount = len(d)
		log.Printf("[UTIL] Writing %d tick records to parquet file", recordCount)
	case []PlayerTickData:
		schema = parquet.SchemaOf(new(PlayerTickData))
		recordCount = len(d)
		log.Printf("[UTIL] Writing %d player records to parquet file", recordCount)
	default:
		log.Printf("[ERROR] Unsupported data type for Parquet writing: %T", data)
		return fmt.Errorf("unsupported data type for Parquet writing")
	}

	log.Printf("[UTIL] Creating parquet writer with schema...")
	writer := parquet.NewWriter(file, schema)
	defer writer.Close()

	// Write data
	startTime := time.Now()
	switch d := data.(type) {
	case []TickData:
		for i, item := range d {
			if err := writer.Write(&item); err != nil {
				log.Printf("[ERROR] Failed to write tick record %d: %v", i, err)
				return fmt.Errorf("failed to write tick data: %w", err)
			}
		}
	case []PlayerTickData:
		for i, item := range d {
			if err := writer.Write(&item); err != nil {
				log.Printf("[ERROR] Failed to write player record %d: %v", i, err)
				return fmt.Errorf("failed to write player data: %w", err)
			}
		}
	}
	writeTime := time.Since(startTime)

	// Get file size
	fileInfo, _ := file.Stat()
	log.Printf("[UTIL] Parquet file written successfully: %s (%d records, %d bytes, %v)",
		filePath, recordCount, fileInfo.Size(), writeTime)

	return nil
}

// processDemoFile parses a CS2 demo file and generates Parquet files
func (is *IngestionService) processDemoFile(demoPath, matchID string) (*ProcessingResult, error) {
	log.Printf("[PROCESSING] Starting demo processing for match %s from file: %s", matchID, demoPath)

	// Check if file exists and is readable
	fileInfo, err := os.Stat(demoPath)
	if err != nil {
		log.Printf("[ERROR] Cannot access demo file %s: %v", demoPath, err)
		return nil, fmt.Errorf("failed to access demo file: %w", err)
	}
	log.Printf("[PROCESSING] Demo file verified: %s (%d bytes)", demoPath, fileInfo.Size())

	// Open demo file
	log.Printf("[PROCESSING] Opening demo file for parsing...")
	file, err := os.Open(demoPath)
	if err != nil {
		log.Printf("[ERROR] Failed to open demo file %s: %v", demoPath, err)
		return nil, fmt.Errorf("failed to open demo file: %w", err)
	}
	defer file.Close()

	// Create demo parser
	log.Printf("[PROCESSING] Creating demo parser...")
	parser := demoinfocs.NewParser(file)
	defer parser.Close()

	var mapName string
	var processedFrames int
	playerSet := make(map[uint64]bool)

	// Simple event-based approach to collect data
	var ticksData []TickData
	var playersData []PlayerTickData

	log.Printf("[PROCESSING] Registering event handlers...")

	// Register event handler for frame completion
	parser.RegisterEventHandler(func(e events.FrameDone) {
		gameState := parser.GameState()
		tick := gameState.IngameTick()

		// Skip negative or very early ticks
		if tick <= 0 {
			return
		}

		processedFrames++
		if processedFrames%1000 == 0 {
			log.Printf("[PROCESSING] Processed %d frames for match %s (current tick: %d)", processedFrames, matchID, tick)
		}

		// Get map name if not set
		if mapName == "" {
			mapName = "unknown" // Default fallback, will be updated from ServerInfo
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
			Phase:        fmt.Sprintf("%v", gameState.GamePhase()),
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

	// Register net message handler for server info (example usage)
	parser.RegisterNetMessageHandler(func(m *msg.CSVCMsg_ServerInfo) {
		if m != nil {
			// Extract useful server information
			if m.MapName != nil {
				mapName = *m.MapName
				log.Printf("[PROCESSING] Map name detected from ServerInfo: %s", mapName)
			}
			if m.GameDir != nil {
				log.Printf("[PROCESSING] Game directory: %s", *m.GameDir)
			}
			if m.TickInterval != nil {
				log.Printf("[PROCESSING] Server tick interval: %f", *m.TickInterval)
			}
			if m.MaxClients != nil {
				log.Printf("[PROCESSING] Max clients: %d", *m.MaxClients)
			}
		}
	})

	// Register net message handler for game event list
	parser.RegisterNetMessageHandler(func(m *msg.CSVCMsg_GameEventList) {
		if m != nil && m.Descriptors != nil {
			log.Printf("[PROCESSING] Game events available: %d", len(m.Descriptors))
			// Optionally log specific events of interest
			for _, desc := range m.Descriptors {
				if desc.Name != nil && (*desc.Name == "player_death" || *desc.Name == "round_start" || *desc.Name == "round_end") {
					log.Printf("[PROCESSING] Found game event: %s (ID: %d)", *desc.Name, desc.GetEventid())
				}
			}
		}
	})

	// Parse the entire demo
	log.Printf("[PROCESSING] Starting full demo parsing for match %s...", matchID)
	startTime := time.Now()
	err = parser.ParseToEnd()
	parseTime := time.Since(startTime)

	if err != nil {
		log.Printf("[ERROR] Demo parsing failed for match %s after %v: %v", matchID, parseTime, err)
		return nil, fmt.Errorf("demo parsing error: %w", err)
	}

	log.Printf("[PROCESSING] Demo parsing completed for match %s in %v", matchID, parseTime)
	log.Printf("[PROCESSING] Parsing statistics: %d frames processed, %d ticks collected, %d players tracked",
		processedFrames, len(ticksData), len(playerSet))

	// Set default map name if still empty
	if mapName == "" {
		mapName = "unknown"
		log.Printf("[WARN] Map name could not be determined, using default: %s", mapName)
	}

	// Create output file paths
	log.Printf("[PROCESSING] Creating output file paths for match %s on map %s...", matchID, mapName)
	ticksFile, playerFile, err := createOutputPaths(is.config.DataPath, matchID, mapName)
	if err != nil {
		log.Printf("[ERROR] Failed to create output paths for match %s: %v", matchID, err)
		return nil, err
	}
	log.Printf("[PROCESSING] Output paths created - Ticks: %s, Players: %s", ticksFile, playerFile)

	// Write Parquet files
	if len(ticksData) > 0 {
		log.Printf("[PROCESSING] Writing %d tick records to parquet file: %s", len(ticksData), ticksFile)
		writeStartTime := time.Now()
		err = writeParquetFile(ticksFile, ticksData)
		writeTime := time.Since(writeStartTime)
		if err != nil {
			log.Printf("[ERROR] Failed to write ticks parquet file %s: %v", ticksFile, err)
			return nil, fmt.Errorf("failed to write ticks parquet file: %w", err)
		}
		log.Printf("[PROCESSING] Ticks parquet file written successfully in %v", writeTime)
	} else {
		log.Printf("[WARN] No tick data to write for match %s", matchID)
	}

	if len(playersData) > 0 {
		log.Printf("[PROCESSING] Writing %d player records to parquet file: %s", len(playersData), playerFile)
		writeStartTime := time.Now()
		err = writeParquetFile(playerFile, playersData)
		writeTime := time.Since(writeStartTime)
		if err != nil {
			log.Printf("[ERROR] Failed to write players parquet file %s: %v", playerFile, err)
			return nil, fmt.Errorf("failed to write players parquet file: %w", err)
		}
		log.Printf("[PROCESSING] Players parquet file written successfully in %v", writeTime)
	} else {
		log.Printf("[WARN] No player data to write for match %s", matchID)
	}

	log.Printf("[PROCESSING] Demo processing completed successfully for match %s: %d ticks, %d players, Map: %s",
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
	log.Printf("[STARTUP] ==========================================")
	log.Printf("[STARTUP] Starting Ingestion Service...")
	log.Printf("[STARTUP] ==========================================")

	// Load configuration from environment variables
	log.Printf("[STARTUP] Loading configuration from environment...")
	config := NewConfig()
	log.Printf("[STARTUP] Configuration loaded successfully:")
	log.Printf("[STARTUP]   - Port: %s", config.Port)
	log.Printf("[STARTUP]   - Data Path: %s", config.DataPath)
	log.Printf("[STARTUP]   - Database URL: %s", maskConnectionString(config.DatabaseURL))

	// Create ingestion service instance
	log.Printf("[STARTUP] Creating ingestion service instance...")
	ingestionService, err := NewIngestionService(config)
	if err != nil {
		log.Fatalf("[FATAL] Failed to create ingestion service: %v", err)
	}
	log.Printf("[STARTUP] Ingestion service instance created successfully")

	// Setup routes
	log.Printf("[STARTUP] Setting up HTTP routes...")
	router := ingestionService.setupRoutes()
	log.Printf("[STARTUP] HTTP routes configured successfully")

	// Start server
	addr := ":" + config.Port
	log.Printf("[STARTUP] ==========================================")
	log.Printf("[STARTUP] Ingestion Service ready to start!")
	log.Printf("[STARTUP] ==========================================")
	log.Printf("[STARTUP] Listening on: %s", addr)
	log.Printf("[STARTUP] Health check: http://localhost:%s/health", config.Port)
	log.Printf("[STARTUP] Configuration: http://localhost:%s/config", config.Port)
	log.Printf("[STARTUP] Upload endpoint: http://localhost:%s/upload", config.Port)
	log.Printf("[STARTUP] Data directory: %s", config.DataPath)
	log.Printf("[STARTUP] ==========================================")

	log.Printf("[STARTUP] Starting HTTP server...")
	if err := router.Run(addr); err != nil {
		log.Fatalf("[FATAL] Failed to start server: %v", err)
	}
}
