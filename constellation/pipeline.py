from dataclasses import dataclass, field
from typing import Any, Dict, List
import datetime
import logging
from aiostream import stream, pipe


log = logging.getLogger(__name__)


@dataclass
class Msg:
    """The main object passed from collectors downstream."""
    measurement: str = None
    timestamp: str = '1992-09-20 11:30:00'  # field(default_factory=datetime.datetime.now().isoformat)
    value: Any = None
    tags: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


def build_pipeline(collectors, processor):
    return stream.merge(*collectors) | pipe.action(processor)
