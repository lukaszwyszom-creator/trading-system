# Stock RSI Signal Project

This project downloads stock prices using yfinance, calculates the RSI (Relative Strength Index), and prints buy/sell/hold signals based on RSI thresholds.

## Structure
- main.py: Main CLI script
- config.py: Configuration loader for environment variables
- requirements.txt: Dependencies
- README.md: Project documentation
- .env.example: Example environment configuration file

## Configuration

The project uses environment variables for configuration. To set up:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your actual values:
   ```
   API_KEY=your_actual_api_key
   API_SECRET=your_actual_api_secret
   BASE_URL=https://your-trading-api.com
   ```

3. The configuration module will automatically load these values when imported:
   ```python
   from config import get_settings
   
   settings = get_settings()
   print(settings.base_url)  # Access configuration values
   ```

The configuration module validates that all required environment variables are set and provides clear error messages if any are missing.
