# Script to check the status of PolicyAide MCP servers
Write-Host "Checking PolicyAide MCP server status..." -ForegroundColor Cyan

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port
    )
    
    $connections = netstat -ano | Select-String ":$Port"
    return ($null -ne $connections)
}

# Function to test HTTP endpoint and display response
function Test-HTTPEndpoint {
    param(
        [string]$URL
    )
    
    try {
        $response = Invoke-WebRequest -Uri $URL -Method GET -UseBasicParsing -TimeoutSec 3
        return $response
    } catch {
        return $null
    }
}

# Check Brave MCP HTTP Server (Port 8051)
$braveRunning = Test-PortInUse -Port 8051
$braveResponse = $null
if ($braveRunning) {
    $braveResponse = Test-HTTPEndpoint -URL "http://localhost:8051/"
}

# Display status information
Write-Host "`nServer Status:" -ForegroundColor Cyan
Write-Host "-------------" -ForegroundColor Cyan

# Brave MCP Status
if ($braveRunning) {
    Write-Host "Brave MCP HTTP Server: RUNNING (Port 8051)" -ForegroundColor Green
    if ($braveResponse -and $braveResponse.StatusCode -eq 200) {
        $content = $braveResponse.Content | ConvertFrom-Json
        Write-Host "  Version: $($content.version)" -ForegroundColor Green
        Write-Host "  Status: $($content.status)" -ForegroundColor Green
        $tools = $content.tools -join ", "
        Write-Host "  Available Tools: $tools" -ForegroundColor Green
        
        # Test specific endpoints
        try {
            $testPayload = @{
                "mcp_version" = "0.1.0"
                "tool_calls" = @(
                    @{
                        "id" = "test-call-$(Get-Date -Format 'yyyyMMddHHmmss')"
                        "name" = "brave_web_search"
                        "parameters" = @{
                            "query" = "test query"
                            "count" = 1
                        }
                    }
                )
            } | ConvertTo-Json
            
            $testResponse = Invoke-WebRequest -Uri "http://localhost:8051/tools/execute" -Method POST -Body $testPayload -ContentType "application/json" -UseBasicParsing -TimeoutSec 3
            if ($testResponse.StatusCode -eq 200) {
                Write-Host "  ✅ API Endpoint Test: SUCCESS" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️ API Endpoint Test: Returned status code $($testResponse.StatusCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ⚠️ API Endpoint Test: FAILED - $($_.Exception.Message)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠️ Warning: Server is running but HTTP endpoint is not responding" -ForegroundColor Yellow
    }
} else {
    Write-Host "Brave MCP HTTP Server: NOT RUNNING (Port 8051)" -ForegroundColor Red
}

# Display information on starting servers if not running
if (-not $braveRunning) {
    Write-Host "`nTo start the Brave MCP HTTP server, run:" -ForegroundColor Yellow
    Write-Host "  .\run_policy_aide_servers.ps1" -ForegroundColor Yellow
    Write-Host "  or" -ForegroundColor Yellow
    Write-Host "  node brave_http_proxy.js" -ForegroundColor Yellow
}

# Display how to run the demo if server is running
if ($braveRunning) {
    Write-Host "`nServer is ready. To run the context gathering demo:" -ForegroundColor Green
    Write-Host "  python src/civicaide/examples/context_gathering_demo.py" -ForegroundColor Green
} 