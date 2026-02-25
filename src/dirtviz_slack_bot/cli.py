from datetime import datetime, timedelta
from typing import Generator

from slack_sdk import WebClient
import argparse
from ents.dirtviz import BackendClient

from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

import logging

logger = logging.getLogger(__name__)

SLACK_TOKEN = ""
CLIENT_ID = "#soil-power-students"


class Group:
    def __init__(
        self, name: str, start: int, end: int, include: list[int], exclude: list[int]
    ):
        self._name = name
        self.start = start
        self.end = end
        self.include = include
        self.exclude = exclude

    def name(self) -> str:
        return self._name

    def cells(self) -> list[int]:
        cells = list(range(self.start, self.end + 1))
        cells += self.include
        cells = [c for c in cells if c not in self.exclude]

        return cells


class Config:
    """Configuration class for the Dirtviz API client."""

    def __init__(self, data: dict):
        self.data = data

    def validate(self) -> bool:
        """Validates the configuration.

        Returns:
            True if the configuration is valid, False otherwise.
        """

        return True

    def channel(self) -> str:
        return self.data["channel"]

    def groups(self) -> Generator:
        for g in self.data["groups"]:
            yield Group(g["name"], g["start"], g["end"], g["include"], g["exclude"])


def post_hello_world(client: WebClient):
    msg = "Hello, World!"
    client.chat_postMessage(channel=CLIENT_ID, text=msg)


def post_cell_data(client: WebClient, name: str, channel: str, cells: list[int]):
    """Post cell data into a channel

    Queries the previous day's data and posts the most recent data point. If
    there is no data then it uses the string "No Data".

    Args:
        client: Slack WebClient
        channel: Slack channel to post to
        cells: List of cell ids to query
    """

    backend = BackendClient()

    end = datetime.utcnow()
    start = end - timedelta(days=1)

    # top level message
    msg = f"*{name}*\n\n"
    msg += "_No Data_\n"

    # thread dta
    thread = f"Checking data at {end} UTC\n\n"

    for cid in cells:
        cell = backend.cell_from_id(cid)
        if cell is None:
            logger.warning("Cell ID %d not found", cid)
            continue

        power_df = backend.power_data(cell, start, end)
        teros_df = backend.teros_data(cell, start, end)

        new_voltage_df = backend.sensor_data_simple(
            cell,
            "POWER_VOLTAGE",
            "Voltage",
            start,
            end
        )

        new_teros_vwc_df = backend.sensor_data_simple(
            cell,
            "POWER_VOLTAGE",
            "Voltage",
            start,
            end
        )

        


        if power_df.empty or teros_df.empty:
            msg += f"- {cell.name}\n"
            logger.warning("No data for cell %s (%d)", cell.name, cell.id)

        voltage = power_df["v"].iloc[-1] if not power_df.empty else "No Data"
        current = power_df["i"].iloc[-1] if not power_df.empty else "No Data"

        vwc = teros_df["vwc"].iloc[-1] if not teros_df.empty else "No Data"
        temp = teros_df["temp"].iloc[-1] if not teros_df.empty else "No Data"
        ec = teros_df["ec"].iloc[-1] if not teros_df.empty else "No Data"

        thread += f"*{cell.name}*:\n"
        thread += f"\tv:    {voltage} mV\n"
        thread += f"\ti:    {current} mA\n"
        thread += f"\tvwc:  {vwc} %\n"
        thread += f"\ttemp: {temp} C\n"
        thread += f"\tec:   {ec} dS/m\n"
        thread += "\n"

    resp = client.chat_postMessage(channel=channel, text=msg)
    thread_ts = resp["ts"]

    client.chat_postMessage(channel=channel, text=thread, thread_ts=thread_ts)


def entry():
    """Entrypoint for the slack bot"""

    parser = argparse.ArgumentParser(description="Dirtviz Slack Bot")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument("config", type=str, help="Path to configuration file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    # parse configuration
    with open(args.config, "r") as f:
        config_data = load(f, Loader=Loader)

    # create slack client
    client = WebClient(token=SLACK_TOKEN)

    # loop over groups
    config = Config(config_data)
    for g in config.groups():
        name = g.name()
        cells = g.cells()
        logger.info(f"Posting data for {name}: {cells}")

        # post actual data
        post_cell_data(client, name, config.channel(), cells)


if __name__ == "__main__":
    entry()
