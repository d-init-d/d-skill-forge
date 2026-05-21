# d-skill-forge installer for Windows
# Usage: irm https://raw.githubusercontent.com/d-init-d/d-skill-forge/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$Repo = "d-init-d/d-skill-forge"
$Binary = "dskillforge.exe"
$Asset = "dskillforge-windows-amd64.exe"
$InstallDir = "$env:LOCALAPPDATA\Programs\dskillforge"

Write-Host "🔍 Finding latest release..." -ForegroundColor Cyan

$Release = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest"
$Tag = $Release.tag_name
$Url = "https://github.com/$Repo/releases/download/$Tag/$Asset"

Write-Host "📦 Downloading dskillforge $Tag..." -ForegroundColor Cyan

# Create install directory
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

# Download
$OutPath = Join-Path $InstallDir $Binary
Invoke-WebRequest -Uri $Url -OutFile $OutPath

# Add to PATH if not already there
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", "User")
    Write-Host "📝 Added $InstallDir to PATH" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ dskillforge $Tag installed!" -ForegroundColor Green
Write-Host ""
Write-Host "   Restart your terminal, then run:" -ForegroundColor White
Write-Host "   dskillforge" -ForegroundColor Cyan
Write-Host ""
