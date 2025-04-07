# PowerShell script to run all MCP servers

Write-Host "Setting up MCP environment..."

# Read API keys from local.env file in the current directory
$envPath = "local.env"
if (Test-Path $envPath) {
    Write-Host "Loading environment variables from $((Get-Item $envPath).FullName)"
    $envContent = Get-Content -Path $envPath
    $censusApiKey = $envContent | Where-Object { $_ -match "CENSUS_API_KEY=" } | ForEach-Object { $_.Split("=")[1] }
    $braveApiKey = $envContent | Where-Object { $_ -match "BRAVE_API_KEY=" } | ForEach-Object { $_.Split("=")[1] }

    if (-not $censusApiKey) {
        Write-Warning "❌ CENSUS_API_KEY not found in local.env file"
        exit 1
    }
    else {
        Write-Host "✅ Found Census API key in local.env"
        $env:CENSUS_API_KEY = $censusApiKey
    }

    if (-not $braveApiKey) {
        Write-Warning "❌ BRAVE_API_KEY not found in local.env file"
        exit 1
    }
    else {
        Write-Host "✅ Found Brave API key in local.env"
        $env:BRAVE_API_KEY = $braveApiKey
    }
} else {
    Write-Warning "❌ local.env file not found in current directory"
    Write-Host "Please create a local.env file with your API keys:"
    Write-Host "CENSUS_API_KEY=your_key_here"
    Write-Host "BRAVE_API_KEY=your_key_here"
    exit 1
}

# Start the Census MCP server in a new window
Write-Host "`nStarting Census MCP server on port 8050..."
Start-Process powershell -ArgumentList "-NoExit -Command cd '$PWD'; `$env:CENSUS_API_KEY='$censusApiKey'; python -m uvicorn census_mcp:app --host 0.0.0.0 --port 8050"

# Start the Brave Search MCP server in a new window
Write-Host "Starting Brave Search MCP server on port 8051..."
Start-Process powershell -ArgumentList "-NoExit -Command cd '$PWD'; `$env:BRAVE_API_KEY='$braveApiKey'; `$env:PORT=8051; npx -y @modelcontextprotocol/server-brave-search"

Write-Host "`n✅ All MCP servers started. Please check the new PowerShell windows for details."
Write-Host "When you're done, close the PowerShell windows to stop the servers." 