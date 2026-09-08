# Run FACTMESH locally on Windows
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Starting FACTMESH Local Development Stack" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Set environment
$env:PYTHONPATH = "$PSScriptRoot\..\backend"

# Check if .env exists
if (-not (Test-Path "$PSScriptRoot\..\.env")) {
    Copy-Item "$PSScriptRoot\..\.env.example" "$PSScriptRoot\..\.env"
    Write-Host "Created .env from .env.example" -ForegroundColor Green
}

# Start backend
Write-Host "Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "-m uvicorn app.main:app --port 8000 --reload" -WorkingDirectory "$PSScriptRoot\..\backend"

# Start frontend
Write-Host "Starting React Frontend on http://localhost:5173..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm.cmd run dev" -WorkingDirectory "$PSScriptRoot\..\frontend"

Write-Host "FACTMESH services launched!" -ForegroundColor Green
Write-Host "Backend Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "Frontend App: http://localhost:5173" -ForegroundColor Cyan
