#!/usr/bin/env python3
"""Concert Alert Bot."""
import json
import os
import warnings
from datetime import datetime
from typing import List, Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

import config
from sources import ticketmaster
from sources.normalize import NormalizedEvent

warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL')


class ConcertBot:
    def __init__(self):
        self.spotify = None
        self.notified_concerts = self._load_notified_concerts()

    # ---------------- Notified-concerts storage ----------------

    def _load_notified_concerts(self) -> dict:
        if not os.path.exists(config.NOTIFIED_CONCERTS_FILE):
            return {}
        with open(config.NOTIFIED_CONCERTS_FILE, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            data = {k: None for k in data}
        return self._migrate_notified(data)

    def _migrate_notified(self, data: dict) -> dict:
        """Prefix unprefixed keys with `tm:` and expand values to {date, artist}."""
        migrated = {}
        for k, v in data.items():
            new_key = k if (":" in k and k.split(":", 1)[0] in ("tm", "bit")) else f"tm:{k}"
            if isinstance(v, dict):
                new_val = {"date": v.get("date"), "artist": v.get("artist")}
            else:
                new_val = {"date": v, "artist": None}
            migrated[new_key] = new_val
        return migrated

    def _save_notified_concerts(self):
        with open(config.NOTIFIED_CONCERTS_FILE, 'w') as f:
            json.dump(self.notified_concerts, f, indent=2)

    def _cleanup_past_concerts(self):
        today = datetime.now().date()
        to_remove = []
        for sid, meta in self.notified_concerts.items():
            date_str = meta.get("date") if isinstance(meta, dict) else None
            if not date_str:
                continue
            try:
                if datetime.strptime(date_str, '%Y-%m-%d').date() < today:
                    to_remove.append(sid)
            except (ValueError, TypeError):
                pass
        for sid in to_remove:
            del self.notified_concerts[sid]
        if to_remove:
            print(f"Cleaned up {len(to_remove)} past concerts from tracking")

    def is_already_notified(self, event: NormalizedEvent) -> bool:
        return event.storage_id in self.notified_concerts

    def record_notified(self, event: NormalizedEvent):
        self.notified_concerts[event.storage_id] = {
            "date": event.local_date,
            "artist": event.artist,
        }

    # ---------------- Spotify (unchanged behavior) ----------------

    def _init_spotify(self):
        if self.spotify is not None:
            return self.spotify
        if config.SPOTIFY_REFRESH_TOKEN:
            auth = SpotifyOAuth(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET,
                redirect_uri=config.SPOTIFY_REDIRECT_URI,
                scope=config.SPOTIFY_SCOPES,
            )
            token = auth.refresh_access_token(config.SPOTIFY_REFRESH_TOKEN)
            self.spotify = spotipy.Spotify(auth=token['access_token'])
        else:
            self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET,
                redirect_uri=config.SPOTIFY_REDIRECT_URI,
                scope=config.SPOTIFY_SCOPES,
            ))
        return self.spotify

    def _load_curated_artists(self) -> List[dict]:
        artists = []
        with open(config.MY_ARTISTS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    artists.append({'name': line, 'id': None, 'source': 'manual'})
        return artists

    def get_favorite_artists(self) -> List[dict]:
        artists = []
        if os.path.exists(config.MY_ARTISTS_FILE):
            print(f"Loading curated artist list from {config.MY_ARTISTS_FILE}...")
            curated = self._load_curated_artists()
            artists.extend(curated)
            print(f"Loaded {len(curated)} curated artists")

        if config.SKIP_SPOTIFY:
            print("Skipping Spotify authentication (SKIP_SPOTIFY=true)")
            print(f"Monitoring {len(artists)} artists total")
            return artists

        print("Checking Spotify for followed artists...")
        try:
            self._init_spotify()
            followed = self.spotify.current_user_followed_artists(limit=50)
            added = 0
            while True:
                for item in followed['artists']['items']:
                    if not any(a['name'].lower() == item['name'].lower() for a in artists):
                        artists.append({'name': item['name'], 'id': item['id'], 'source': 'spotify_followed'})
                        added += 1
                if not followed['artists']['next']:
                    break
                followed = self.spotify.next(followed['artists'])
            print(f"Added {added} new artists from Spotify follows" if added else "No new artists found on Spotify")
        except Exception as e:
            print(f"Could not connect to Spotify: {e}")
            print("Continuing with curated artist list only...")

        print(f"Monitoring {len(artists)} artists total")
        with open(config.ARTISTS_CACHE_FILE, 'w') as f:
            json.dump(artists, f, indent=2)
        return artists

    # ---------------- Source orchestration ----------------

    def collect_events(self, artist_name: str) -> List[NormalizedEvent]:
        events: List[NormalizedEvent] = []
        for raw in ticketmaster.search(
            api_key=config.TICKETMASTER_API_KEY,
            artist_name=artist_name,
            latitude=config.LATITUDE,
            longitude=config.LONGITUDE,
            radius_miles=config.SEARCH_RADIUS,
            search_window_months=config.SEARCH_WINDOW_MONTHS,
        ):
            if ticketmaster.is_tribute_show(raw):
                continue
            if not ticketmaster.is_artist_match(raw, artist_name):
                continue
            events.append(ticketmaster.normalize_event(raw, search_artist=artist_name))
        return events

    # ---------------- Formatting ----------------

    @staticmethod
    def _fmt_dt(iso: Optional[str]) -> str:
        if not iso:
            return "TBA"
        try:
            return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M %Z").strip()
        except ValueError:
            return iso

    def format_concert_alert(self, event: NormalizedEvent) -> str:
        time_str = event.local_time or "TBA"
        lines = [
            "=" * 80,
            "NEW CONCERT ALERT!",
            "=" * 80,
            f"Artist: {event.artist}",
            f"Event: {event.event_name}",
            f"Date: {event.local_date} at {time_str}",
            f"Venue: {event.venue_name}, {event.city}",
            f"Tickets: {event.ticket_url}",
        ]
        if event.on_sale_datetime:
            lines.append(f"On-sale: {self._fmt_dt(event.on_sale_datetime)}")
        if event.presales:
            lines.append("Presales:")
            for p in event.presales:
                lines.append(f"  - {p.name}: {self._fmt_dt(p.start_datetime)} -> {self._fmt_dt(p.end_datetime)}")
        lines.append("=" * 80)
        return "\n".join(lines) + "\n"

    # ---------------- Email ----------------

    def send_email(self, alerts: List[str], events: List[NormalizedEvent]):
        if not config.SEND_EMAIL_NOTIFICATIONS:
            print("Email notifications disabled (SEND_EMAIL_NOTIFICATIONS=false)")
            return
        if not alerts:
            print("No new concerts -- skipping email")
            return
        if not (config.SENDGRID_API_KEY and config.SENDER_EMAIL and config.RECIPIENT_EMAIL):
            print("Email enabled but SendGrid config missing. Skipping email.")
            return

        subject = f"{len(alerts)} New Concert Alert{'s' if len(alerts) > 1 else ''}!"
        html = self._build_html(events)
        text = f"You have {len(alerts)} new concert alert{'s' if len(alerts) > 1 else ''}!\n\n" + "\n".join(alerts)

        try:
            message = Mail(
                from_email=Email(config.SENDER_EMAIL),
                to_emails=To(config.RECIPIENT_EMAIL),
                subject=subject,
                plain_text_content=Content("text/plain", text),
                html_content=Content("text/html", html),
            )
            sg = SendGridAPIClient(config.SENDGRID_API_KEY)
            response = sg.send(message)
            if response.status_code == 202:
                print(f"Email sent successfully to {config.RECIPIENT_EMAIL}")
            else:
                print(f"Email sent with status code: {response.status_code}")
        except Exception as e:
            print(f"Error sending email: {e}")

    def _build_html(self, events: List[NormalizedEvent]) -> str:
        head = """<html><head><style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .header { background-color: #1DB954; color: white; padding: 20px; text-align: center; }
            .concert { border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; }
            .artist { font-size: 18px; font-weight: bold; color: #1DB954; }
            .event { font-size: 16px; margin: 5px 0; }
            .details { color: #666; margin: 5px 0; }
            .source { font-size: 11px; color: #999; text-transform: uppercase; }
            .presale { background: #f4f4f4; padding: 8px; border-radius: 4px; margin: 8px 0; font-size: 13px; }
            .button { background-color: #1DB954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }
            .footer { text-align: center; margin-top: 30px; color: #999; font-size: 12px; }
        </style></head><body>"""
        body = f'<div class="header"><h1>New Concert Alerts</h1><p>You have {len(events)} new concert{"s" if len(events) > 1 else ""} to check out!</p></div>'

        for ev in events:
            body += f'<div class="concert">'
            body += f'<div class="artist">{ev.artist}</div>'
            body += f'<div class="event">{ev.event_name}</div>'
            body += f'<div class="details">Date: {ev.local_date} at {ev.local_time or "TBA"}</div>'
            body += f'<div class="details">Venue: {ev.venue_name}, {ev.city}</div>'
            if ev.on_sale_datetime:
                body += f'<div class="presale"><strong>On-sale:</strong> {self._fmt_dt(ev.on_sale_datetime)}</div>'
            for p in ev.presales:
                body += (f'<div class="presale"><strong>{p.name}:</strong> '
                         f'{self._fmt_dt(p.start_datetime)} -> {self._fmt_dt(p.end_datetime)}</div>')
            if ev.ticket_url:
                body += f'<a href="{ev.ticket_url}" class="button">Get Tickets</a>'
            body += '</div>'

        body += '<div class="footer"><p>You\'re receiving this because you set up Concert Alert Bot.</p></div></body></html>'
        return head + body

    # ---------------- Main ----------------

    def run(self):
        print("Starting Concert Alert Bot...")
        print(f"Searching within {config.SEARCH_RADIUS} miles of ({config.LATITUDE}, {config.LONGITUDE})")
        print()

        self._cleanup_past_concerts()
        artists = self.get_favorite_artists()

        new_alerts: List[str] = []
        new_events: List[NormalizedEvent] = []

        print("\nSearching for concerts...")
        for i, artist in enumerate(artists, 1):
            print(f"[{i}/{len(artists)}] Checking {artist['name']}...")
            for event in self.collect_events(artist['name']):
                if self.is_already_notified(event):
                    continue
                new_alerts.append(self.format_concert_alert(event))
                new_events.append(event)
                self.record_notified(event)
                print(f"  -> {event.event_name} on {event.local_date}")

        if new_alerts:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(config.OUTPUT_FILE, 'a') as f:
                f.write(f"\n\nRun at: {timestamp}\nFound {len(new_alerts)} new concert(s)\n")
                for a in new_alerts:
                    f.write(a)
            print(f"\nFound {len(new_alerts)} new concert(s)! Check {config.OUTPUT_FILE}")
            self.send_email(new_alerts, new_events)
        else:
            print("\nNo new concerts found -- no email sent.")

        self._save_notified_concerts()
        print("\nDone!")


if __name__ == '__main__':
    ConcertBot().run()
