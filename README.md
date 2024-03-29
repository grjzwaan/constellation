# Constellation
Constellation is a personal project to automate stuff in my house. The goal is that the source should be _simple_ and
_explicit_.

## Collect measurements
The idea is to have a single Python script that describes your devices and how you want to collect it. Then, wire it
to a processor for storage.

In this project I've made initial versions for Shelly Plug S and Slimmelezer. The main work is done with async generators
using the library `aiostreams`

This leads to a very simple, yet explicit script:
```python
import asyncio
import logging
from rich.logging import RichHandler
from constellation.pipeline import build_pipeline
from constellation.processors import DuckDBProcessor
from constellation.collectors import ShellyPlugSCollector, ESGHomeCollector, poll, listen


async def main():
    # Set example
    plug = ShellyPlugSCollector("http://192.168.1.207/status",
                                measurement="power",
                                tags={'quantity': 'kWh', 'device': 'heatpump'}
                                )
    slimmemeter = ESGHomeCollector(
        "http://192.168.1.204/events",
        {
            # Add a mapping to the energy usage for tariff 1
            "sensor-energy_consumed_tariff_1": (
                "power",
                {'quantity': 'kWh', 'device': 'meter', 'tariff': '1'}
            )
        }
    )

    collectors = [
        poll(plug, every=6),
        listen(slimmemeter)
    ]

    pipeline = build_pipeline(collectors, DuckDBProcessor(tags=['quantity', 'device', 'tariff']))

    await pipeline


if __name__ == "__main__":
    # Set the logging
    FORMAT = "%(message)s"
    logging.basicConfig(
        level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        pass

```

Building a custom collector is quite easy. If you simply target a different endpoint and get a different JSON, just
copy-paste the `ShellyPlugSCollector` and rewrite the JSON-parsing. 

@TODO: Add some examples.

## Processor
I've added a simple DuckDB processor. It attemps to generate a table to store the measurements. For this you 
need to know the tags in advance as it'll create a column for each.

DuckDB does not yet support categorical columns but intends to do this. Then this approach is simple and performant.