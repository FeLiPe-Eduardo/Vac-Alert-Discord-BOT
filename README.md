# Vac-Alert-Discord-BOT
Bot that sends automated messages when users receive VAC on Steam.

<img src="https://i.imgur.com/qnFS2NJ.png" width="540"/>


services:
  vac-bot:
    image: iflp/vac_alert_discord_bot:latest
    container_name: vac-bot
    volumes:
      - ./db:/bot/db
    environment:
      - DISCORD_BOT_TOKEN=seu_token
      - STEAM_API_KEY=sua_api
    restart: unless-stopped


