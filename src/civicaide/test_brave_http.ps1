# Script to test if the Brave MCP server is running in HTTP mode

Write-Host "Testing Brave MCP HTTP server connection..."

# Check if there's a process listening on port 8051
$connections = netstat -ano | Select-String ":8051"
if ($connections) {
    Write-Host "✅ Found process listening on port 8051"
    
    # Try to make an HTTP request to the server
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8051/" -Method GET -UseBasicParsing -TimeoutSec 2
        
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Server responded with status code 200 (OK)"
            Write-Host "✅ Brave MCP is successfully running in HTTP mode"
            Write-Host "Response content type: $($response.Headers["Content-Type"])"
        } else {
            Write-Host "❌ Server responded with status code $($response.StatusCode)"
        }
    } catch {
        Write-Host "❌ Failed to connect to the server: $_"
    }
} else {
    Write-Host "❌ No process is listening on port 8051"
    Write-Host "The Brave MCP server is not running in HTTP mode or is not running at all."
    Write-Host "Please start the server using run_brave_mcp.ps1 or run_brave_mcp_http.bat"
}

# Check running Node.js processes that might be related to Brave MCP
Write-Host "`nChecking for running Brave MCP processes..."
$processes = Get-Process | Where-Object { $_.ProcessName -eq "node" }

if ($processes) {
    Write-Host "Found $($processes.Count) Node.js processes running:"
    foreach ($process in $processes) {
        try {
            $cmd = (Get-WmiObject Win32_Process -Filter "ProcessId = $($process.Id)").CommandLine
            if ($cmd -like "*brave*" -or $cmd -like "*mcp*") {
                Write-Host "  - Process ID: $($process.Id)"
                Write-Host "    Command: $cmd"
            }
        } catch {
            Write-Host "  - Process ID: $($process.Id) (Could not get command line)"
        }
    }
} else {
    Write-Host "No Node.js processes found."
} 