# Script to run our custom Brave MCP HTTP server

Write-Host "Preparing Brave MCP HTTP server..."

# Check and install required Node.js packages if not already installed
if (-not (Test-Path -Path "node_modules/express")) {
    Write-Host "Installing required Node.js packages..."
    npm install express axios body-parser
}

# Kill any existing processes using port 8051
try {
    $existingProcess = Get-NetTCPConnection -LocalPort 8051 -ErrorAction SilentlyContinue | 
                        Select-Object -ExpandProperty OwningProcess | 
                        ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }
    
    if ($existingProcess) {
        Write-Host "Found existing process using port 8051: $($existingProcess.Id) ($($existingProcess.ProcessName))"
        Write-Host "Stopping process..."
        Stop-Process -Id $existingProcess.Id -Force
        Start-Sleep -Seconds 1
    }
} catch {
    Write-Host "No existing process found on port 8051."
}

# Start the server in the background
Write-Host "Starting Brave MCP HTTP server on port 8051..."
Write-Host "Press Ctrl+C to stop the server."

node brave_http_proxy.js 