# PowerShell script to run the context gathering demo

# Set environment variables from local.env
Write-Host "Setting up environment variables..."
$scriptPath = $PSScriptRoot
$envPath = Join-Path $scriptPath "local.env"
if (Test-Path $envPath) {
    $envContent = Get-Content -Path $envPath
    $censusApiKey = $envContent | Where-Object { $_ -match "CENSUS_API_KEY=" } | ForEach-Object { $_.Split("=")[1] }
    $braveApiKey = $envContent | Where-Object { $_ -match "BRAVE_API_KEY=" } | ForEach-Object { $_.Split("=")[1] }

    if ($censusApiKey) {
        $env:CENSUS_API_KEY = $censusApiKey.Trim()
        Write-Host "✅ Set CENSUS_API_KEY"
    } else {
        Write-Warning "❌ Could not find CENSUS_API_KEY in local.env"
        exit 1
    }

    if ($braveApiKey) {
        $env:BRAVE_API_KEY = $braveApiKey.Trim()
        Write-Host "✅ Set BRAVE_API_KEY"
    } else {
        Write-Warning "❌ Could not find BRAVE_API_KEY in local.env"
        exit 1
    }
} else {
    Write-Warning "❌ Could not find local.env file"
    exit 1
}

# Add the project root to PYTHONPATH
$projectRoot = (Get-Item (Split-Path $PSScriptRoot -Parent)).Parent.FullName
$env:PYTHONPATH = $projectRoot

Write-Host "`nEnvironment variables set:"
Write-Host "CENSUS_API_KEY: " -NoNewline
Write-Host ($env:CENSUS_API_KEY.Substring(0,5) + "..." + $env:CENSUS_API_KEY.Substring($env:CENSUS_API_KEY.Length-4))
Write-Host "BRAVE_API_KEY: " -NoNewline
Write-Host ($env:BRAVE_API_KEY.Substring(0,5) + "..." + $env:BRAVE_API_KEY.Substring($env:BRAVE_API_KEY.Length-4))
Write-Host "PYTHONPATH: $env:PYTHONPATH"

# Run the demo
Write-Host "`nRunning context gathering demo..."
python examples/context_gathering_demo.py 