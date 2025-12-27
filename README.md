# Concert Alert Bot 🎵

A lightweight Python bot that monitors upcoming concerts for your favorite Spotify artists in your area and sends notifications.

## Features

- ✅ Merges your curated artist list with Spotify followed artists automatically
- ✅ Searches for concerts within a configurable radius of your location (up to 12 months ahead)
- ✅ Filters out tribute bands and false positive matches
- ✅ Formatted output with artist summary and monthly grouping
- ✅ Email notifications via SendGrid (optional)
- ✅ Writes new concert alerts to a text file
- ✅ Tracks previously notified concerts to avoid duplicates
- ✅ Lightweight and easy to run locally or via GitHub Actions

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
cd concert-alert-bot
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get API Credentials

#### Spotify API
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create an App"
4. Name it "Concert Alert Bot" (or anything you like)
5. Copy your **Client ID** and **Client Secret**
6. Click "Edit Settings"
7. Add `http://localhost:8888/callback` to "Redirect URIs" and save

#### Ticketmaster API
1. Go to [Ticketmaster Developer Portal](https://developer.ticketmaster.com/)
2. Sign up for a free account
3. Go to "My Apps" and create a new app
4. Copy your **API Key** (also called Consumer Key)

#### SendGrid Email (Optional)
1. Go to [SendGrid](https://signup.sendgrid.com/)
2. Sign up for a free account (100 emails/day free forever)
3. Go to Settings → [API Keys](https://app.sendgrid.com/settings/api_keys)
4. Click "Create API Key"
5. Name it "Concert Alert Bot" and give it "Full Access"
6. Copy your **API Key** (you won't be able to see it again!)
7. Go to Settings → [Sender Authentication](https://app.sendgrid.com/settings/sender_auth)
8. Verify a sender email address (the email you'll send from)

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
TICKETMASTER_API_KEY=your_ticketmaster_api_key_here
LATITUDE=34.0522
LONGITUDE=-118.2437
SEARCH_RADIUS=40
```

### 4. Create Your Artist List (Optional)

```bash
cp my_artists.txt.example my_artists.txt
```

Edit `my_artists.txt` to add your favorite artists (one per line). The bot will automatically merge this with your Spotify followed artists.

### 5. Run the Bot

```bash
python concert_bot.py
```

On first run, it will:
1. Open a browser window for Spotify OAuth authentication
2. Ask you to authorize the app
3. Redirect to localhost (you can close the browser)
4. Start searching for concerts

New concerts will be written to `concert_alerts.txt`

To generate a formatted, easy-to-read version:

```bash
python format_concerts.py
```

This creates `concert_alerts_formatted.txt` with concerts grouped by month and an artist summary at the top.

## How It Works

1. **Loads your curated artist list** from `my_artists.txt` (if it exists)
2. **Fetches followed artists from Spotify** and merges with your curated list (deduplicates automatically)
3. **Searches Ticketmaster** for concerts by each artist within your specified radius
4. **Filters out tribute bands** and verifies artist matches to avoid false positives
5. **Checks against previous alerts** to avoid duplicates
6. **Writes new concerts** to `concert_alerts.txt` and `concert_alerts_formatted.txt`
7. **Sends email notification** (if enabled) with a nicely formatted HTML email
8. **Saves state** in JSON files to track what's been notified

## Files Created

- `my_artists.txt` - Your curated artist list (optional, created from .example file)
- `artists_cache.json` - Cached list of merged artists (curated + Spotify follows)
- `notified_concerts.json` - IDs of concerts you've already been notified about
- `concert_alerts.txt` - Raw output file with all concert alerts
- `concert_alerts_formatted.txt` - Formatted output grouped by month with artist summary
- `.cache` - Spotify OAuth token (auto-generated)

## Configuration

Edit `config.py` to change:
- Search radius (default: 40 miles)
- Location coordinates (default: Los Angeles - 34.0522, -118.2437)
- Search window (default: 12 months ahead)
- File names

### Enable Email Notifications

To receive email alerts when new concerts are found:

1. Complete the SendGrid setup (see step 2 above)
2. Edit your `.env` file:
   ```
   SEND_EMAIL_NOTIFICATIONS=true
   SENDGRID_API_KEY=your_actual_sendgrid_api_key
   SENDER_EMAIL=verified@sender.com
   RECIPIENT_EMAIL=your@email.com
   ```
3. Run the bot - you'll receive a beautiful HTML email with all new concerts!

**Email Features:**
- 🎨 Clean, professional HTML design with Spotify green branding
- 🎫 Direct "Get Tickets" buttons for each concert
- 📧 Plain text fallback for email clients that don't support HTML
- 📱 Mobile-friendly responsive design

## Running Weekly (GitHub Actions)

To automate weekly runs:

1. Create `.github/workflows/concert-bot.yml`:

```yaml
name: Concert Alert Bot

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
  workflow_dispatch:  # Allow manual runs

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python concert_bot.py
        env:
          SPOTIFY_CLIENT_ID: ${{ secrets.SPOTIFY_CLIENT_ID }}
          SPOTIFY_CLIENT_SECRET: ${{ secrets.SPOTIFY_CLIENT_SECRET }}
          TICKETMASTER_API_KEY: ${{ secrets.TICKETMASTER_API_KEY }}
          LATITUDE: ${{ secrets.LATITUDE }}
          LONGITUDE: ${{ secrets.LONGITUDE }}
          SEARCH_RADIUS: ${{ secrets.SEARCH_RADIUS }}
          SEND_EMAIL_NOTIFICATIONS: ${{ secrets.SEND_EMAIL_NOTIFICATIONS }}
          SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
          SENDER_EMAIL: ${{ secrets.SENDER_EMAIL }}
          RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
```

2. Add your API credentials as GitHub Secrets in your repo settings (Settings → Secrets and variables → Actions → New repository secret):
   - Required: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `TICKETMASTER_API_KEY`, `LATITUDE`, `LONGITUDE`, `SEARCH_RADIUS`
   - Optional for email: `SEND_EMAIL_NOTIFICATIONS` (set to `true`), `SENDGRID_API_KEY`, `SENDER_EMAIL`, `RECIPIENT_EMAIL`

## Manual Testing

To test without waiting a week:

```bash
# Delete the notified concerts file to re-check everything
rm notified_concerts.json

# Run the bot
python concert_bot.py
```

## Troubleshooting

**"No module named 'spotipy'"**
- Make sure you activated the virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**"Invalid client"**
- Check that your Spotify credentials are correct in `.env`
- Make sure you added the redirect URI in Spotify Dashboard

**"No concerts found"**
- This could be normal if none of your artists are touring
- Try reducing the search radius or checking a different zip code
- Verify your Ticketmaster API key is valid

**Rate limits**
- Ticketmaster free tier: 5,000 calls/day (plenty for 500 artists)
- Spotify: Generous rate limits for personal use
- SendGrid free tier: 100 emails/day (perfect for daily/weekly runs)

**Email not sending**
- Check that `SEND_EMAIL_NOTIFICATIONS=true` in your `.env`
- Verify your SendGrid API key is correct
- Make sure your sender email is verified in SendGrid
- Check SendGrid dashboard for error logs

## Future Enhancements

- [x] Email notifications (via SendGrid)
- [ ] Discord/Slack webhooks
- [ ] Filter by venue type
- [ ] Price alerts
- [ ] Multiple locations
- [ ] Web dashboard

## License

Personal use only.
