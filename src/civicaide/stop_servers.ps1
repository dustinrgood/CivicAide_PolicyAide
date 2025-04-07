# Script to stop PolicyAide MCP servers
Write-Host "Stopping PolicyAide MCP servers..." -ForegroundColor Yellow

# Function to find and stop processes on specific ports
function Stop-ServerOnPort {
    param(
        [int]$Port,
        [string]$ServerName
    )
    
    Write-Host "Checking for $ServerName on port $Port..." -ForegroundColor Cyan
    
    try {
        $existingProcesses = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
                             Select-Object -ExpandProperty OwningProcess -Unique | 
                             ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }
        
        if ($existingProcesses) {
            foreach ($process in $existingProcesses) {
                Write-Host "Found $ServerName process: $($process.Id) ($($process.ProcessName))" -ForegroundColor Green
                Write-Host "Stopping process..." -ForegroundColor Yellow
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            }
            Write-Host "$ServerName stopped successfully." -ForegroundColor Green
            return $true
        } else {
            Write-Host "No $ServerName processes found on port $Port." -ForegroundColor Cyan
            return $false
        }
    } catch {
        Write-Host "Error stopping $ServerName. Check permissions." -ForegroundColor Red
        return $false
    }
}

# Stop running jobs if any
Write-Host "Checking for running PowerShell jobs..." -ForegroundColor Cyan
$jobs = Get-Job | Where-Object { $_.State -eq "Running" }
if ($jobs) {
    Write-Host "Found $($jobs.Count) running jobs. Stopping..." -ForegroundColor Yellow
    foreach ($job in $jobs) {
        Write-Host "Stopping job $($job.Id)..." -ForegroundColor Yellow
        Stop-Job -Id $job.Id
        Remove-Job -Id $job.Id -Force
    }
    Write-Host "All jobs stopped." -ForegroundColor Green
} else {
    Write-Host "No running jobs found." -ForegroundColor Cyan
}

# Stop Brave MCP HTTP server on port 8051
$braveStopped = Stop-ServerOnPort -Port 8051 -ServerName "Brave MCP HTTP"

# Forcibly stop any node processes running our script
Write-Host "Checking for Node.js processes running brave_http_proxy.js..." -ForegroundColor Cyan
try {
    $nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | 
                     Where-Object { $_.CommandLine -like "*brave_http_proxy.js*" }
    
    if ($nodeProcesses) {
        Write-Host "Found $($nodeProcesses.Count) Node.js processes running brave_http_proxy.js" -ForegroundColor Yellow
        foreach ($process in $nodeProcesses) {
            Write-Host "Stopping Node.js process: $($process.Id)" -ForegroundColor Yellow
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
        Write-Host "All matching Node.js processes stopped." -ForegroundColor Green
    } else {
        Write-Host "No Node.js processes running brave_http_proxy.js found." -ForegroundColor Cyan
    }
} catch {
    Write-Host "Error checking Node.js processes." -ForegroundColor Red
}

# Summary
Write-Host "`nServer Status:" -ForegroundColor Cyan
Write-Host "-------------" -ForegroundColor Cyan

if ($braveStopped) {
    Write-Host "Brave MCP HTTP Server: STOPPED" -ForegroundColor Green
} else {
    Write-Host "Brave MCP HTTP Server: No action taken" -ForegroundColor Yellow
}

# Final verification
$braveStillRunning = Get-NetTCPConnection -LocalPort 8051 -ErrorAction SilentlyContinue

if ($braveStillRunning) {
    Write-Host "`nWarning: Brave MCP HTTP Server is still running on port 8051" -ForegroundColor Red
    Write-Host "You may need to manually kill the process by running:" -ForegroundColor Yellow
    Write-Host "  taskkill /f /im node.exe" -ForegroundColor Yellow
    Write-Host "Note: This will kill ALL Node.js processes!" -ForegroundColor Red
} else {
    Write-Host "`nBrave MCP HTTP Server has been stopped successfully." -ForegroundColor Green
}

# Check server status
Write-Host "`nTo verify server status, run:" -ForegroundColor Cyan
Write-Host "  .\check_servers.ps1" -ForegroundColor Cyan 