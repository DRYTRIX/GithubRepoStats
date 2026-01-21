# GitHub Repository Statistics Display

A beautiful, full-featured Python application for displaying GitHub repository statistics on a Raspberry Pi or any computer with a display. Perfect for monitoring your open-source projects, tracking package downloads, and displaying donation totals.

![GitHub Stats Display](https://img.shields.io/badge/Python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- 📊 **Comprehensive Statistics**: Track stars, forks, issues, commits, and more
- 📦 **Package Downloads**: Monitor GitHub Container Registry package downloads
- 💝 **Donation Tracking**: Display totals from PayPal and Buy Me a Coffee
- 🖥️ **Multiple Display Modes**: 
  - Full-screen GUI for HDMI displays
  - Character LCD support (I2C/GPIO)
  - Terminal output for development
- 🎨 **Beautiful Modern UI**: Dark theme with color-coded stat cards
- ⚡ **Smart Caching**: Reduces API calls and respects rate limits
- 🔄 **Auto-refresh**: Automatically updates at configurable intervals
- 📱 **Raspberry Pi Ready**: Optimized for low-power devices

## Requirements

- Python 3.7 or higher
- GitHub Personal Access Token (with appropriate permissions)
- Display device (HDMI monitor, character LCD, or terminal)

### Optional Dependencies

- **For Character LCD**: `RPLCD` and `RPi.GPIO` (for Raspberry Pi)
- **For GUI Display**: `tkinter` (usually included with Python)

## Installation

1. **Clone or download this repository**

```bash
git clone <repository-url>
cd GithubRepoStats
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **For Raspberry Pi with Character LCD** (optional):

```bash
pip install RPLCD RPi.GPIO
```

## Configuration

1. **Copy the example configuration file**

```bash
cp config.yaml.example config.yaml
```

2. **Edit `config.yaml` with your settings**

### Basic Configuration

```yaml
# GitHub Personal Access Token
# Create one at: https://github.com/settings/tokens
# Required permissions: public_repo (or repo for private repos), read:packages
github_token: "your_github_token_here"

# List of repositories to track
repositories:
  - "owner/repo-name-1"
  - "owner/repo-name-2"

# Refresh interval in minutes
refresh_interval_minutes: 15

# Display type: terminal, character_lcd, gui, or fullscreen
display_type: fullscreen
```

### GitHub Token Setup

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select the following scopes:
   - `public_repo` (for public repositories) or `repo` (for private repos)
   - `read:packages` (for package download statistics)
4. Copy the token and paste it into `config.yaml`

### Display Configuration

#### Full-Screen GUI (HDMI Display)

```yaml
display_type: fullscreen  # or "gui"

display_settings:
  fullscreen: true
  bg_color: "#0a0e27"      # Dark blue background
  text_color: "#ffffff"    # White text
  accent_color: "#00d4ff"  # Cyan accent
  font_family: "Segoe UI"  # Font name
  title_font_size: 64
  body_font_size: 32
  small_font_size: 20
```

#### Character LCD (20x4 I2C)

```yaml
display_type: character_lcd

display_settings:
  mode: i2c
  i2c_address: 0x27  # Default I2C address
  i2c_port: 1        # I2C port (usually 1 on Raspberry Pi)
  width: 20
  height: 4
```

#### Character LCD (GPIO Mode)

```yaml
display_type: character_lcd

display_settings:
  mode: gpio
  pin_rs: 15
  pin_e: 16
  pins_data: [21, 22, 23, 24]
  numbering_mode: BCM  # Options: BCM or BOARD
  width: 20
  height: 4
```

### Package Downloads (GitHub Container Registry)

```yaml
github_packages:
  # Simple format
  - "owner/package-name"
  
  # Full format with type specification
  - owner: "owner"
    name: "package-name"
    type: "container"  # Options: container, npm, maven, nuget, rubygems
```

**Note**: GitHub Container Registry doesn't expose download counts via API. The app will automatically use release asset downloads as a fallback.

### Donation Tracking

#### Buy Me a Coffee

```yaml
donations:
  enabled: true
  buymeacoffee:
    username: "your-username"  # Your Buy Me a Coffee username
```

The app will scrape your public Buy Me a Coffee page to extract total donations.

#### PayPal

```yaml
donations:
  enabled: true
  paypal:
    client_id: "your_client_id"
    client_secret: "your_client_secret"
```

Get PayPal API credentials from [PayPal Developer Dashboard](https://developer.paypal.com/).

### View Modes

```yaml
# Options: summary or per_repo
view_mode: summary  # Shows aggregated stats across all repos
# view_mode: per_repo  # Shows individual repository details
```

### Cache Configuration

```yaml
cache_enabled: true
cache_duration_minutes: 10  # How long to cache API responses
cache_dir: .cache           # Cache directory
```

## Usage

### Basic Usage

```bash
python main.py
```

### Custom Config File

```bash
python main.py --config /path/to/config.yaml
```

### Running on Raspberry Pi

1. **For HDMI Display (Full-screen GUI)**:

```bash
python main.py
```

The app will start in full-screen mode. Press `Escape` to exit.

2. **For Character LCD**:

Make sure your LCD is properly connected:
- **I2C**: Connect SDA, SCL, VCC, and GND
- **GPIO**: Connect according to your pin configuration

Then run:
```bash
python main.py
```

3. **Auto-start on Boot** (Optional):

Create a systemd service or add to `/etc/rc.local`:

```bash
cd /path/to/GithubRepoStats
python3 main.py &
```

## Display Examples

### Summary View

The summary view shows aggregated statistics:
- Total stars across all repositories
- Total forks
- Total open issues
- Number of active repositories
- Package downloads (if configured)
- Total donations (if configured)
- Most starred repository

### Per-Repository View

The per-repository view shows detailed stats for each repo:
- Repository name and description
- Stars and forks
- Open issues
- Primary programming language
- Latest version (if available)
- Release downloads
- Last commit time

## Troubleshooting

### GitHub API Rate Limits

If you see rate limit errors:
- Ensure your GitHub token is configured correctly
- The app automatically caches responses to reduce API calls
- Increase `cache_duration_minutes` in config
- Reduce `refresh_interval_minutes`

### Package Downloads Show Zero

GitHub Container Registry doesn't expose download counts via API. The app will:
1. Try to get counts from package versions (often returns 0)
2. Automatically fall back to release asset downloads
3. Display release downloads if package downloads are unavailable

### Buy Me a Coffee Not Working

The app scrapes your public Buy Me a Coffee page. If it's not working:
- Verify your username is correct
- Check that your profile is public
- The page structure may have changed (check error logs)
- Consider using manual configuration as a fallback

### Character LCD Not Displaying

1. **Check I2C connection**:
```bash
sudo i2cdetect -y 1  # Should show your LCD address (usually 0x27)
```

2. **Check GPIO pins** match your configuration

3. **Verify permissions**:
```bash
sudo usermod -a -G i2c,gpio $USER
# Log out and back in
```

4. **Test with a simple script**:
```python
from RPLCD import I2CCharLCD
lcd = I2CCharLCD('PCF8574', 0x27)
lcd.write_string('Hello World')
```

### GUI Not Starting

- Ensure `tkinter` is installed:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install python3-tk
  
  # macOS (usually pre-installed)
  # Windows (usually pre-installed)
  ```

### Import Errors

If you see import errors:
```bash
pip install -r requirements.txt
```

For Raspberry Pi LCD support:
```bash
pip install RPLCD RPi.GPIO
```

## Project Structure

```
GithubRepoStats/
├── main.py                      # Main application entry point
├── github_fetcher.py            # GitHub API client
├── github_packages_fetcher.py   # GitHub Packages API client
├── donations_fetcher.py         # Donation tracking (PayPal, Buy Me a Coffee)
├── cache_manager.py             # Caching system
├── metrics_calculator.py        # Metrics calculation and aggregation
├── utils.py                     # Utility functions
├── display/
│   ├── base.py                  # Abstract display interface
│   ├── gui.py                   # Full-screen GUI display
│   ├── terminal.py              # Terminal/console display
│   └── character_lcd.py        # Character LCD display
├── config.yaml                  # Your configuration (create from example)
├── config.yaml.example          # Example configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Configuration File Reference

See `config.yaml.example` for a complete configuration reference with all available options and detailed comments.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

- Built with Python and tkinter
- Uses GitHub REST API
- Supports various display types for maximum flexibility

---

**Enjoy monitoring your GitHub statistics!** 🚀
