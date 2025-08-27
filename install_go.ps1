# PowerShell script to install Go
Write-Host "🚀 Installing Go for Windows..." -ForegroundColor Green

# Download Go installer
$goVersion = "1.21.5"
$goInstaller = "go$goVersion.windows-amd64.msi"
$downloadUrl = "https://go.dev/dl/$goInstaller"
$tempPath = "$env:TEMP\$goInstaller"

Write-Host "📥 Downloading Go $goVersion..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempPath -UseBasicParsing
    Write-Host "✅ Download completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Download failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Install Go
Write-Host "📦 Installing Go..." -ForegroundColor Yellow
try {
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", $tempPath, "/quiet" -Wait
    Write-Host "✅ Go installation completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Clean up
Remove-Item $tempPath -Force -ErrorAction SilentlyContinue

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "🔄 Please restart your terminal or run:" -ForegroundColor Yellow
Write-Host "   `$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')" -ForegroundColor Cyan
Write-Host "   go version" -ForegroundColor Cyan
