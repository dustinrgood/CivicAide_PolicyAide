// Script to run Brave Search MCP in HTTP mode
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

// Load API key from environment or from local.env file
let braveApiKey = process.env.BRAVE_API_KEY;

if (!braveApiKey) {
  try {
    // Read from local.env file
    const envPath = path.join(__dirname, 'src', 'civicaide', 'local.env');
    console.log(`Loading API key from ${envPath}...`);
    
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, 'utf8');
      const keyMatch = envContent.match(/BRAVE_API_KEY=(.+)/);
      
      if (keyMatch && keyMatch[1]) {
        braveApiKey = keyMatch[1].trim();
        console.log('API key loaded successfully.');
      } else {
        console.error('Could not find BRAVE_API_KEY in the local.env file.');
        process.exit(1);
      }
    } else {
      console.error('Could not find local.env file.');
      process.exit(1);
    }
  } catch (error) {
    console.error(`Error loading API key: ${error.message}`);
    process.exit(1);
  }
}

// Ensure the package is installed
try {
  console.log('Checking if @modelcontextprotocol/server-brave-search is installed...');
  execSync('npm list -g @modelcontextprotocol/server-brave-search', { stdio: 'ignore' });
} catch (error) {
  console.log('Installing @modelcontextprotocol/server-brave-search globally...');
  try {
    execSync('npm install -g @modelcontextprotocol/server-brave-search', { stdio: 'inherit' });
  } catch (installError) {
    console.error('Failed to install package:', installError.message);
    process.exit(1);
  }
}

// Now that we've handled the API key and package, import and use the server
try {
  console.log('Starting Brave MCP server in HTTP mode...');
  
  // Dynamically import the module
  const modulePath = path.dirname(require.resolve('@modelcontextprotocol/server-brave-search'));
  const { BraveMCPServer } = require(path.join(modulePath, 'dist', 'index.js'));
  
  // Set environment variables
  process.env.BRAVE_API_KEY = braveApiKey;
  process.env.PORT = 8051;
  process.env.MCP_MODE = 'http';
  
  // Create server
  const server = new BraveMCPServer({
    apiKey: braveApiKey,
    port: 8051,
    mode: 'http'
  });
  
  // Start server
  server.start();
  
  console.log(`Brave MCP server running in HTTP mode on port 8051.`);
  console.log('Press Ctrl+C to stop the server.');
} catch (error) {
  console.error(`Failed to start server: ${error.message}`);
  console.error(error.stack);
  process.exit(1);
} 