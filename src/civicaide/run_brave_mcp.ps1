# PowerShell script to run the Brave Search MCP server

Write-Host "Setting up Brave Search MCP server..."

# Read the API key from local.env file
$envContent = Get-Content -Path "local.env"
$braveApiKey = $envContent | Where-Object { $_ -match "BRAVE_API_KEY=" } | ForEach-Object { $_.Split("=")[1] }

if (-not $braveApiKey) {
    Write-Error "BRAVE_API_KEY not found in local.env file"
    exit 1
}

Write-Host "Found Brave API key in local.env"

# Set environment variables
$env:BRAVE_API_KEY = $braveApiKey
$env:PORT = 8051

Write-Host "Installing Brave Search MCP server..."
npm install -g @modelcontextprotocol/server-brave-search

Write-Host "Starting Brave Search MCP server on port 8051..."
Write-Host "Press Ctrl+C to stop the server"

# Run the MCP server
npx -y @modelcontextprotocol/server-brave-search 