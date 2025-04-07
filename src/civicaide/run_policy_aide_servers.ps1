# Script to run all PolicyAide MCP servers
Write-Host "Starting PolicyAide MCP servers..." -ForegroundColor Green

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port
    )
    
    $connections = netstat -ano | Select-String ":$Port"
    return ($null -ne $connections)
}

# Function to stop a process using a specific port
function Stop-ProcessOnPort {
    param(
        [int]$Port
    )
    
    try {
        $existingProcess = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
                            Select-Object -ExpandProperty OwningProcess | 
                            ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }
        
        if ($existingProcess) {
            Write-Host "Found existing process using port $Port with PID $($existingProcess.Id)" -ForegroundColor Yellow
            Write-Host "Stopping process..." -ForegroundColor Yellow
            Stop-Process -Id $existingProcess.Id -Force
            Start-Sleep -Seconds 1
        }
    } catch {
        Write-Host "No existing process found on port $Port or unable to stop it." -ForegroundColor Yellow
    }
}

# Make sure required directories exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# First, make sure the port is free
Stop-ProcessOnPort -Port 8051

# Check and install required Node.js packages for the Brave MCP HTTP server
if (-not (Test-Path -Path "node_modules/express")) {
    Write-Host "Installing required Node.js packages for Brave MCP HTTP server..." -ForegroundColor Yellow
    npm install express axios body-parser
}

# Start our custom Brave MCP HTTP server (PowerShell job)
$braveJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Write-Host "Starting custom Brave MCP HTTP server on port 8051..."
    # Run our custom Node.js script
    node brave_http_proxy.js > logs/brave_mcp.log 2>&1
}

# Wait a moment for server to start
Start-Sleep -Seconds 3

# Check if server is running
Write-Host "`nChecking server status..." -ForegroundColor Green

$braveRunning = Test-PortInUse -Port 8051

# Display status information
Write-Host "`nServer Status:" -ForegroundColor Cyan
Write-Host "-------------" -ForegroundColor Cyan

if ($braveRunning) {
    Write-Host "Brave MCP HTTP Server: RUNNING (Port 8051)" -ForegroundColor Green
    
    # Test HTTP endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8051/" -Method GET -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -eq 200) {
            $content = $response.Content | ConvertFrom-Json
            Write-Host "  Version: $($content.version)" -ForegroundColor Green
            Write-Host "  Status: $($content.status)" -ForegroundColor Green
            $tools = $content.tools -join ", "
            Write-Host "  Available Tools: $tools" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ Warning: Server is running but HTTP endpoint returned status code $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠️ Warning: Server is running but HTTP endpoint is not responding" -ForegroundColor Yellow
    }
} else {
    Write-Host "Brave MCP HTTP Server: NOT RUNNING (Port 8051)" -ForegroundColor Red
    # Show last few lines of log if available
    if (Test-Path "logs/brave_mcp.log") {
        Write-Host "Last 5 lines of Brave MCP log:" -ForegroundColor Yellow
        Get-Content "logs/brave_mcp.log" -Tail 5
    }
}

# Display how to check logs
Write-Host "`nTo view server logs:" -ForegroundColor Cyan
Write-Host "  Brave MCP: Get-Content -Path 'logs/brave_mcp.log' -Wait" -ForegroundColor Cyan

# Display how to stop server
Write-Host "`nTo stop server:" -ForegroundColor Cyan
Write-Host "  Stop-Job -Id $($braveJob.Id)" -ForegroundColor Cyan
Write-Host "  Remove-Job -Id $($braveJob.Id)" -ForegroundColor Cyan

Write-Host "`nBrave MCP Job ID: $($braveJob.Id)" -ForegroundColor Green
Write-Host "`nServer is running in the background and will continue until you stop it." -ForegroundColor Green
Write-Host "You can continue using this PowerShell window for other commands." -ForegroundColor Green

# Display how to run the demo
Write-Host "`nTo run the context gathering demo:" -ForegroundColor Green
Write-Host "  python src/civicaide/examples/context_gathering_demo.py" -ForegroundColor Green 