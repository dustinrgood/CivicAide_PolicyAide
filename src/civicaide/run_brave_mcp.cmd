@echo off
REM This script installs and runs the Brave Search MCP server

echo Installing Brave Search MCP server...
npm install -g @modelcontextprotocol/server-brave-search

echo Starting Brave Search MCP server on port 8051...
echo Loading Brave API key from local.env file...

REM Extract BRAVE_API_KEY from local.env file using findstr
FOR /F "tokens=2 delims==" %%a IN ('findstr "BRAVE_API_KEY" local.env') DO SET BRAVE_API_KEY=%%a

REM Verify the key was loaded
IF "%BRAVE_API_KEY%"=="" (
    echo Error: Could not find BRAVE_API_KEY in local.env file.
    exit /b 1
) ELSE (
    echo Successfully loaded Brave API key.
)

set PORT=8051
npx -y @modelcontextprotocol/server-brave-search

echo Brave Search MCP server stopped. 