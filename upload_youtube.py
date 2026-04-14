name: Daily Music Bot

on:
  schedule:
    - cron: "0 8 * * *"
  workflow_dispatch:

jobs:
  generate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install ffmpeg
        run: sudo apt-get install -y ffmpeg

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Install YouTube dependencies
        run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

      - name: Run music bot
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          HF_API_TOKEN: ${{ secrets.HF_API_TOKEN }}
          APIPASS_KEY: ${{ secrets.APIPASS_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python music_bot.py rotation

      - name: Upload to YouTube
        env:
          YOUTUBE_CLIENT_ID: ${{ secrets.YOUTUBE_CLIENT_ID }}
          YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
          YOUTUBE_REFRESH_TOKEN: ${{ secrets.YOUTUBE_REFRESH_TOKEN }}
        run: python upload_youtube.py

      - name: Save progress
        uses: actions/upload-artifact@v4
        with:
          name: album-progress
          path: album_progress.json
          retention-days: 90
          overwrite: true

      - name: Upload output
        uses: actions/upload-artifact@v4
        with:
          name: daily-music-${{ github.run_id }}
          path: output/
          retention-days: 30
