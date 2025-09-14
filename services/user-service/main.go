package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
)

type Config struct {
	Port        string
	DatabaseURL string
}

type UserService struct {
	config *Config
	db     *sql.DB
}

func NewConfig() *Config {
	return &Config{
		Port:        getEnvWithDefault("PORT", "8080"),
		DatabaseURL: getEnvWithDefault("DATABASE_URL", ""),
	}
}

func getEnvWithDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func NewUserService(config *Config) (*UserService, error) {
	var db *sql.DB
	var err error

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

	return &UserService{
		config: config,
		db:     db,
	}, nil
}

func (us *UserService) setupRoutes() *gin.Engine {
	// Set Gin to release mode for production
	gin.SetMode(gin.ReleaseMode)

	r := gin.Default()

	// Health check endpoint
	r.GET("/health", func(c *gin.Context) {
		status := gin.H{
			"status":  "healthy",
			"service": "user-service",
			"port":    us.config.Port,
		}

		// Check database connection if available
		if us.db != nil {
			if err := us.db.Ping(); err != nil {
				status["database"] = "unhealthy"
				status["database_error"] = err.Error()
				c.JSON(http.StatusServiceUnavailable, status)
				return
			}
			status["database"] = "healthy"
		} else {
			status["database"] = "not_configured"
		}

		c.JSON(http.StatusOK, status)
	})

	// Ready check endpoint
	r.GET("/ready", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "ready",
			"service": "user-service",
		})
	})

	// Demo endpoint showing environment variable usage
	r.GET("/config", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"port":         us.config.Port,
			"database_url": maskConnectionString(us.config.DatabaseURL),
			"message":      "User service is running and reading configuration from environment variables",
		})
	})

	// Basic user endpoints (placeholder)
	r.GET("/users", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"users":   []string{},
			"message": "User list endpoint - placeholder implementation",
		})
	})

	r.POST("/auth/login", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"token":   "demo-jwt-token",
			"message": "Login endpoint - placeholder implementation",
		})
	})

	return r
}

func maskConnectionString(connectionString string) string {
	if connectionString == "" {
		return "not configured"
	}
	return "configured (masked for security)"
}

func main() {
	log.Println("Starting User Service...")

	// Load configuration from environment variables
	config := NewConfig()
	log.Printf("Loaded configuration: Port=%s", config.Port)

	// Create user service instance
	userService, err := NewUserService(config)
	if err != nil {
		log.Fatalf("Failed to create user service: %v", err)
	}

	// Setup routes
	router := userService.setupRoutes()

	// Start server
	addr := ":" + config.Port
	log.Printf("User Service listening on %s", addr)
	log.Printf("Health check available at: http://localhost:%s/health", config.Port)

	if err := router.Run(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
