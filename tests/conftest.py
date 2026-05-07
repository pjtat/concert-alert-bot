import json
from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def ticketmaster_event():
    return json.loads((FIXTURES / "ticketmaster_event.json").read_text())
