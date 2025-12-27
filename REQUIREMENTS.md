# Concert Alert Bot - Requirements

## Overview
A lightweight bot that monitors upcoming concerts for your favorite Spotify artists in your area and sends notifications.

## Functional Requirements

### 1. Spotify Integration
- Fetch user's top artists (via Spotify Web API)
- Fetch artists the user follows
- Handle up to 500 artists
- Store artist data locally to minimize API calls

### 2. Concert Data Collection
- Search for concerts by artist name
- Filter by location (zip code + radius)
- Check for upcoming shows within a configurable time window (e.g., next 3-6 months)
- Store concert data to avoid duplicate notifications

### 3. Notifications
- Send alerts for new concerts discovered
- Include: Artist name, venue, date/time, ticket link
- Method: TBD (email is likely easiest)

### 4. Execution
- Run weekly via cron or GitHub Actions
- Support manual/real-time testing mode
- Minimal dependencies and setup

## Technical Requirements

### Language & Framework
- **Python 3.x** (preferred)

### APIs to Integrate
- **Spotify Web API** - for artist data
- **Concert Data API** - TBD (options below)

### Storage
- Simple local file storage (JSON/SQLite) for:
  - Artist list cache
  - Previously notified concerts (to prevent duplicates)
  - Configuration (zip code, radius, preferences)

### Deployment
- Run locally on macOS
- Optional: GitHub Actions for weekly automation
- Minimal external dependencies

## Configuration Needed
- [ ] Zip code / city for concert search
- [ ] Search radius (in miles)
- [ ] Notification destination (email address, webhook URL, etc.)
- [ ] Time window for upcoming shows (default: 6 months)

## Concert Data API Options

### Option 1: Ticketmaster Discovery API
- **Pros**:
  - Free tier: 5,000 API calls/day
  - Comprehensive US coverage
  - Well-documented
  - Includes venue details, ticket links
- **Cons**:
  - Requires API key (free registration)
  - Primarily US-focused

### Option 2: Bandsintown API
- **Pros**:
  - Free for non-commercial use
  - Good international coverage
  - Simple REST API
  - Artist-focused (search by artist name)
- **Cons**:
  - Rate limits unclear
  - Requires app registration

### Option 3: Songkick API
- **Pros**:
  - Free tier available
  - Good data quality
  - Artist and location search
- **Cons**:
  - API access currently limited (not accepting new applications)

### Option 4: SeatGeek API
- **Pros**:
  - Free tier available
  - Good coverage
  - Includes pricing data
- **Cons**:
  - Requires API key

### Recommendation
Start with **Ticketmaster Discovery API** - it has the most generous free tier and best documentation.

## Notification Options

### Option 1: Email (SMTP)
- **Pros**:
  - Universal, works everywhere
  - Free with Gmail/Outlook
  - Easy to implement
- **Cons**:
  - Need to handle SMTP credentials
- **Implementation**: Use Python's `smtplib` or `yagmail`

### Option 2: Email (SendGrid/Mailgun)
- **Pros**:
  - More reliable delivery
  - Free tiers available
  - Better for automation
- **Cons**:
  - Requires API key

### Option 3: Text File / Console Output
- **Pros**:
  - Simplest option
  - Zero dependencies
  - Good for testing
- **Cons**:
  - Not really a "notification"

### Option 4: Discord/Slack Webhook
- **Pros**:
  - Easy to set up
  - Good for real-time alerts
  - Free
- **Cons**:
  - Requires Discord/Slack

### Recommendation
Start with **simple email via Gmail SMTP** or **console output for testing**, then upgrade to SendGrid or webhooks if needed.

## Next Steps
1. Set up Python project structure
2. Create Spotify API credentials
3. Create Ticketmaster API credentials
4. Implement Spotify artist fetching
5. Implement concert search
6. Implement notification system
7. Add data persistence (avoid duplicate alerts)
8. Set up scheduling (GitHub Actions or cron)
