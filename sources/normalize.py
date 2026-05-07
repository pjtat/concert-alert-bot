"""Normalized event format shared across data sources."""
from dataclasses import dataclass, field
from typing import List, Optional


SOURCE_PREFIXES = {
    "ticketmaster": "tm",
}


@dataclass
class Presale:
    name: str
    start_datetime: Optional[str]
    end_datetime: Optional[str]


@dataclass
class NormalizedEvent:
    source: str
    source_event_id: str
    artist: str
    event_name: str
    local_date: str  # YYYY-MM-DD
    local_time: Optional[str]  # HH:MM or None
    venue_name: str
    city: str
    ticket_url: str
    on_sale_datetime: Optional[str]
    presales: List[Presale] = field(default_factory=list)

    @property
    def storage_id(self) -> str:
        prefix = SOURCE_PREFIXES[self.source]
        return f"{prefix}:{self.source_event_id}"
