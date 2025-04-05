# Project Overview
This repository contains a Discord bot designed to function as a personal soundboard. The bot allows users to upload, play, and manage sound files directly within Discord voice channels. It is particularly tailored for deployment on devices like the Raspberry Pi, leveraging Docker for easy setup and portability.

## Features:
Soundboard Interface: Interactive buttons to play or delete sounds.

* Commands:

    * /join: Connect the bot to a voice channel.

    * /leave: Disconnect the bot from the voice channel.

    * /play [sound_name]: Play a specific sound.

    * /stop: Stop the currently playing sound.

    * /upload [attachment] [optional_name]: Upload a sound file to the bot's library.

    * /soundboard: Open an interactive soundboard interface.

    * /delete: Delete a sound from the library.

* Supported Formats: .mp3, .wav, .ogg.

* Customizable Limits: Maximum number of sounds and file size restrictions can be configured.

# Deployment Instructions
## Prerequisites:
1. Docker Installed: Ensure Docker is installed on your system (including Raspberry Pi).

2. Environment File (.env): Create a .env file with the following variables:

```text
DISCORD_TOKEN=your_discord_bot_token
DISCORD_PREFIX=!
SOUNDS_DIR=/path/to/sounds
MAX_SOUNDS=50
MAX_FILE_SIZE_MB=5
```
3. Sound Files Directory: Prepare a directory for storing sound files (e.g., sounds/).

## Docker Setup
### Build the Docker Image:
```bash
docker build -t <custom-bot-name> .
```
Replace <custom-bot-name> with your preferred name for the Docker image.

### Run the Docker Container:
```bash
docker run -d --restart unless-stopped --env-file .env -v $(pwd)/sounds/:/sounds/ <custom-bot-name>
```
Explanation of flags:

* -d: Runs the container in detached mode.

* --restart unless-stopped: Automatically restarts the container unless manually stopped.

* --env-file .env: Loads environment variables from the .env file.

* -v $(pwd)/sounds/:/sounds/: Mounts your local sounds/ directory to the container for persistent storage.

### Raspberry Pi Deployment
The bot is optimized for lightweight devices like Raspberry Pi. Follow these additional steps:

1. Install Docker on Raspberry Pi using:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```
2. Clone this repository and navigate to its directory:

```bash
git clone <repository-url>
cd <repository-directory>
```
3. Build and run the Docker container using the commands above.

# How to Use

1.  **Create a Discord Bot:**
    *   Go to the [Discord Developer Portal](https://discord.com/developers/applications).
    *   Create a new application.
    *   Navigate to the "Bot" tab and create a bot user.
    *   Copy the bot's token.  This is your `DISCORD_TOKEN` in the `.env` file.
    *   Enable the "Presence Intent", "Server Members Intent", and "Message Content Intent" in the "Privileged Gateway Intents" section.
2. Invite your bot to your Discord server using its OAuth2 URL (configured in Discord Developer Portal).

3. Use commands in any text channel or interact with the soundboard interface.

4. Manage sounds by uploading or deleting them dynamically.

# Contributing
Feel free to fork this repository, submit issues, or create pull requests to improve functionality or add new features!

# License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License - see [https://creativecommons.org/licenses/by-nc/4.0/](https://creativecommons.org/licenses/by-nc/4.0/) for details.

# Attribution

When using this bot, please attribute the original creation to:

[Jose Angel/JoseAngelBMT]

