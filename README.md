# 🎵 Discord Soundboard Bot - Interactive Voice Channel Sound Player

A feature-rich **Discord soundboard bot** with YouTube integration, personal sound profiles, and interactive UI. Perfect for adding custom sounds, memes, and audio clips to your Discord server voice channels.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-latest-blue.svg)](https://github.com/Rapptz/discord.py)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

## ✨ Key Features

### 🎹 Interactive Soundboard
- **Visual soundboard UI** with clickable buttons for each sound
- Play sounds instantly from an interactive Discord interface
- **Real-time sound management** - upload, play, and delete sounds on the fly
- Automatic cleanup of old soundboard messages

### 🎤 Voice Channel Integration
- Seamless voice channel connection and playback
- **Auto-disconnect** when no users are in the channel (every 5 minutes check)
- Support for multiple audio formats: `.mp3`, `.wav`, `.ogg`
- Queue-free instant sound playback

### 📥 Advanced Upload Options
- **Direct file upload** - Drag and drop audio files into Discord
- **YouTube audio extraction** - Download audio from YouTube videos with `/upload_youtube`
- **Audio trimming** - Specify start and end times to cut audio segments
- Custom sound naming for easy organization
- Configurable file size limits and sound count restrictions

### 👤 Personal Sound Profiles
- **Set personal entrance sounds** that play automatically when you join a voice channel
- Per-user sound customization with `/set_user_sound`
- Clear personal sounds anytime with `/clear_user_sound`

### 🎛️ Full Command Suite
All commands use Discord's modern slash command interface:

| Command | Description |
|---------|-------------|
| `/join` | Connect the bot to your voice channel |
| `/leave` | Disconnect the bot from the voice channel |
| `/play <sound_name>` | Play a specific sound by name |
| `/stop` | Stop the currently playing sound |
| `/soundboard` | Open the interactive soundboard UI |
| `/upload <file> [name] [start] [end]` | Upload an audio file with optional trimming |
| `/upload_youtube <url> <name> [start] [end]` | Extract audio from YouTube video |
| `/delete` | Delete sounds from the library via UI |
| `/set_user_sound` | Set your personal entrance sound |
| `/clear_user_sound` | Remove your personal entrance sound |

### ⚙️ Customizable Configuration
- Set maximum number of sounds per server
- Configure file size limits
- Custom command prefix support
- Persistent sound storage with volume mounting

## 🚀 Quick Start Guide

### Prerequisites
- **Docker** installed on your system (Windows, macOS, Linux, or Raspberry Pi)
- **Discord Bot Token** from the [Discord Developer Portal](https://discord.com/developers/applications)
- **FFmpeg** (included in Docker image)

### 1️⃣ Create Your Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** and give it a name
3. Navigate to the **"Bot"** tab and click **"Add Bot"**
4. Copy your bot token (keep it secret!)
5. Enable the following **Privileged Gateway Intents**:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent
6. Go to **OAuth2 → URL Generator**:
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Connect`, `Speak`, `Send Messages`, `Read Message History`, `Use Slash Commands`
   - Copy the generated URL and invite the bot to your server

### 2️⃣ Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required
DISCORD_TOKEN=your_discord_bot_token_here

# Optional (defaults shown)
DISCORD_PREFIX=/
SOUNDS_DIR=./sounds
MAX_SOUNDS=50
MAX_FILE_SIZE_MB=5
```

### 3️⃣ Deploy with Docker

#### Option A: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/JoseAngelBMT/bubucela-bot.git
cd bubucela-bot

# Start the bot (creates sounds directory automatically)
docker-compose up -d
```

#### Option B: Docker CLI

```bash
# Build the image
docker build -t discord-soundboard-bot .

# Create sounds directory
mkdir -p sounds

# Run the container
docker run -d \
  --name soundboard-bot \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/sounds:/sounds \
  discord-soundboard-bot
```

**For Windows PowerShell**, replace `$(pwd)` with `${PWD}`:
```powershell
docker run -d --name soundboard-bot --restart unless-stopped --env-file .env -v ${PWD}/sounds:/sounds discord-soundboard-bot
```

### 4️⃣ Deploy on Raspberry Pi

Perfect for 24/7 hosting on low-power devices:

```bash
# Install Docker (if not already installed)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Clone and deploy
git clone https://github.com/JoseAngelBMT/bubucela-bot.git
cd bubucela-bot
docker-compose up -d

# Check logs
docker-compose logs -f
```

## 📖 Usage Examples

### Basic Sound Playback
```
1. Join a voice channel in Discord
2. Type `/join` to bring the bot to your channel
3. Type `/soundboard` to open the interactive UI
4. Click any sound button to play it instantly
```

### Upload Sound from File
```
/upload
- Attach: your-audio-file.mp3
- Name: epic-sound
- Start: 00:10 (optional - trim from 10 seconds)
- End: 00:30 (optional - trim to 30 seconds)
```

### Extract Audio from YouTube
```
/upload_youtube
- URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
- Name: rickroll
- Start: 00:00:43
- End: 00:00:48
```

### Set Personal Entrance Sound
```
1. Type `/set_user_sound`
2. Select your favorite sound from the menu
3. Every time you join a voice channel, your sound plays automatically!
```

## 🛠️ Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Your Discord bot token (**required**) | - |
| `DISCORD_PREFIX` | Command prefix for slash commands | `/` |
| `SOUNDS_DIR` | Directory to store sound files | `./sounds` |
| `MAX_SOUNDS` | Maximum number of sounds allowed | `50` |
| `MAX_FILE_SIZE_MB` | Maximum file size per sound in MB | `5` |

## 🔧 Advanced Features

### Audio Trimming
Both upload commands support precise audio trimming with multiple time formats:
- Seconds: `45`
- MM:SS: `01:30`
- HH:MM:SS: `00:01:30`

### Auto-Cleanup
- Automatically disconnects from empty voice channels after 5 minutes
- Cleans up old soundboard UI messages when creating new ones
- Invalidates cache after uploads for instant availability

### Persistent Storage
All sounds are stored in the mounted `./sounds` directory, surviving container restarts and updates.

## 📦 Tech Stack

- **Python 3.12+** - Modern async/await syntax
- **discord.py** - Latest version with slash commands
- **yt-dlp** - YouTube audio extraction
- **FFmpeg** - Audio processing and playback
- **pydub** - Audio manipulation and trimming
- **Docker** - Containerized deployment

## 🐛 Troubleshooting

### Bot doesn't respond to slash commands
1. Ensure you've invited the bot with `applications.commands` scope
2. Wait a few minutes after first deployment for Discord to sync commands
3. Try kicking and re-inviting the bot to your server

### Audio doesn't play in voice channel
1. Verify FFmpeg is installed (included in Docker image)
2. Check bot has `Connect` and `Speak` permissions
3. Ensure audio file format is supported (`.mp3`, `.wav`, `.ogg`)

### YouTube download fails
1. Make sure `yt-dlp` is up to date (rebuild Docker image)
2. Some videos may be region-locked or age-restricted
3. Check the video URL is valid and accessible

### Bot disconnects unexpectedly
- This is normal behavior when no users are in the voice channel for 5+ minutes
- The bot automatically rejoins when needed

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Ideas for Contributions
- Additional audio effects and filters
- Sound search functionality
- Web dashboard for sound management
- Sound categories and tagging
- Volume controls
- Sound queuing system

## 📝 License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International License**.

[![License: CC BY-NC 4.0](https://licensebuttons.net/l/by-nc/4.0/88x31.png)](https://creativecommons.org/licenses/by-nc/4.0/)

- ✅ You can use, modify, and share this bot
- ❌ Commercial use is not permitted
- 📄 [Read full license terms](https://creativecommons.org/licenses/by-nc/4.0/)

## 👤 Author & Attribution

**Created by:** [Jose Angel](https://github.com/JoseAngelBMT)

When using or modifying this bot, please provide attribution to the original creator.

## ⭐ Support

If you find this project useful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs and issues
- 💡 Suggesting new features
- 🔀 Contributing code improvements

## 🔗 Keywords

Discord bot, soundboard, Discord soundboard bot, voice channel bot, audio bot, Discord audio player, YouTube to Discord, Discord sound effects, meme soundboard, custom Discord sounds, Discord voice bot, Python Discord bot, slash commands bot, interactive Discord bot, Discord music alternative, sound manager bot, Raspberry Pi Discord bot, Docker Discord bot, self-hosted Discord bot

