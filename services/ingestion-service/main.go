package main

import (
	"database/sql"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
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

	// Generate unique ID for this upload
	uploadID := fmt.Sprintf("demo_%d", time.Now().Unix())
	filename := header.Filename

	// Create file path
	filepath := filepath.Join(is.config.DataPath, uploadID+"_"+filename)

	// Create the file
	// TODO: need to clear this out or the pod will run out of space
	dst, err := os.Create(filepath)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to save file",
			"message": err.Error(),
		})
		return
	}
	defer dst.Close()

	// Copy the uploaded file to the destination
	size, err := io.Copy(dst, file)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Failed to save file",
			"message": err.Error(),
		})
		return
	}

	log.Printf("Demo uploaded: ID=%s, Filename=%s, Size=%d bytes", uploadID, filename, size)

	// TODO: Start background processing of the demo file
	// For now, just return success
	response := UploadResponse{
		ID:       uploadID,
		Filename: filename,
		Size:     size,
		Status:   "uploaded",
		Message:  "Demo file uploaded successfully. Processing will begin shortly.",
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
