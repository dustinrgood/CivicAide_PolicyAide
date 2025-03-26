# CivicAide PolicyAide Changelog

## Database Span Capture Improvements - March 24, 2025

### Fixed Issues
- Fixed issue with NULL values in `input_text`, `output_text`, and `model` fields in the database
- Fixed span hierarchies and parent-child relationships not being correctly recorded
- Fixed token usage tracking to properly store token counts in various formats
- Fixed OpenAI response ID capture
- Added support for extracting metadata from agent interactions
- Improved error handling during database insertions

### Added Features
- Enhanced token tracking: Now captures prompt_tokens, completion_tokens, and total_tokens
- Better parent-child relationships: Now properly maintains hierarchical relationships between spans
- Rich metadata: Captures OpenAI response IDs and other metadata from agent interactions
- More robust data extraction from content and span data
- Added multiple test scripts for verifying database functionality

### Technical Changes
- Improved SQL queries for span insertion with better parent tracking
- Enhanced JSON handling for token usage information
- Standardized span ID format to avoid relationship inconsistencies
- Improved traceability by storing OpenAI response IDs with spans
- Better diagnostic and verification capabilities
- Added comprehensive test scripts for testing different aspects of the system

### Developer Experience
- Added informative console output during trace saving
- Improved error reporting during database operations
- Added verification steps after database operations
- Diagnostic tools for checking database connection and schema 