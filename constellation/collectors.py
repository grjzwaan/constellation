from dataclasses import dataclass, field
from typing import Any, Dict, List
import datetime
import httpx
import json
import logging
from aiostream import stream, pipe
from .pipeline import Msg


from .sse import sse_stream


log = logging.getLogger(__name__)


class Collector:
    pass


class ShellyPlugSCollector(Collector):
    url: str
    measurement: str
    tags: Dict[str, str]

    def __init__(self, url, measurement, tags):
        self.url = url
        self.measurement = measurement
        self.tags = tags

    def __call__(self, measurement):
        r = httpx.get(self.url)

        msg = Msg()

        if r.status_code == 200:
            # Parse the JSON and process it
            content = r.json()
            power = float(content['meters'][0]['power'])

            # Return the measurement
            return Msg(
                measurement=self.measurement,
                tags=self.tags,
                value=power
            )
        else:
            # On a fail we return nothing and ignore it
            log.warning(f"Server {self.url} responded with {r.status_code}")
            return msg | {'_errors': ['API call failed']}


class ESGHomeCollector(Collector):

    def __init__(self, url, mapping):
        self.url = url
        self._aiter = sse_stream(self.url)
        self.mapping = mapping

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            m = await self._aiter.__anext__()

            # Ignore ping and log and only look at state
            if m.event == "state":
                # We need to unpack the JSON
                data = json.loads(m.data)
                mapped = self.mapping.get(data['id'])

                if mapped is None:
                    log.debug(f"No mapping found for measurement '{data['id']}', skip.")
                    continue

                measurement, tags = mapped

                return Msg(
                    measurement=measurement,
                    tags=tags,
                    value=data['value']
                )


def poll(collector, every):
    """Turn a one-off collector into a stream."""
    return (
            stream.repeat({}, interval=every)
            | pipe.map(collector)  # Apply the source
            | pipe.filter(lambda msg: len(msg.errors) == 0)  # Only forward if there is no error
    )


def listen(source):
    """Turn an async generator into a stream."""
    return stream.iterate(source)



