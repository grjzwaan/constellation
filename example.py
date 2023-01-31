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
