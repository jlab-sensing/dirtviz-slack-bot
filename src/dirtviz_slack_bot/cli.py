import os
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

SLACK_TOKEN = os.getenv("SLACK_TOKEN")


class Group:
    def __init__(
        self, name: str, start: int, end: int, include: list[int], exclude:
        list[int], _bme280: int
    ):
        self._name = name
        self.start = start
        self.end = end
        self.include = include
        self.exclude = exclude
        self._bme280 = _bme280

    def name(self) -> str:
        return self._name


    def bme280(self) -> int:
        return self._bme280

    def cells(self) -> list[int]:
        cells = list(range(self.start, self.end + 1))
        cells += self.include
        cells = [c for c in cells if c not in self.exclude]
        cells.sort()

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
            yield Group(g["name"], g["start"], g["end"], g["include"],
                        g["exclude"], g["bme280"])


def data_to_string(df, meas) -> str:
    """Creates a print string based on a df and meas name.

    Args:
        df: Data input.
        meas: Column name of measurement.

    Returns:
        String that can be printed out.
    """

    meas_str = df[meas].iloc[-1] if not df.empty else "No Data"
    return meas_str


def get_voltage_str(backend: BackendClient, cell, start: datetime, end: datetime) -> str:
    """Gets the last voltage measurement for a cell.

    If no data is found for that cell it returns "No Data".

    Args:
        backend: Instance of backend client.
        cell: Cell instance.
        start: Start date.
        end: End date.

    Returns:
        Formatted measurement text.
    """

    power_df = backend.power_data(cell, start, end)

    new_voltage_df = backend.sensor_data_simple(
        cell, "POWER_VOLTAGE", "Voltage", start, end
    )

    if not power_df.empty:
        voltage = data_to_string(power_df, "v")
    else:
        voltage = data_to_string(new_voltage_df, "Voltage")

    return voltage


def get_current_str(backend: BackendClient, cell, start: datetime, end: datetime) -> str:
    """Gets the last current measurement for a cell.

    If no data is found for that cell it returns "No Data".

    Args:
        backend: Instance of backend client.
        cell: Cell instance.
        start: Start date.
        end: End date.

    Returns:
        Formatted measurement text.
    """

    power_df = backend.power_data(cell, start, end)
    current = data_to_string(power_df, "i")

    return current


def get_vwc_str(backend: BackendClient, cell, start: datetime, end: datetime) -> str:
    """Gets the last teros vwc measurement for a cell.

    If no data is found for that cell it returns "No Data".

    Args:
        backend: Instance of backend client.
        cell: Cell instance.
        start: Start date.
        end: End date.

    Returns:
        Formatted measurement text.
    """

    teros_df = backend.teros_data(cell, start, end)

    new_teros_vwc_df = backend.sensor_data_simple(
        cell, "TEROS12_VWC_ADJ", "Volumetric Water Content", start, end
    )

    if not teros_df.empty:
        vwc = data_to_string(teros_df, "vwc")
    else:
        vwc = data_to_string(new_teros_vwc_df, "Volumetric Water Content")

    return vwc


def get_ec_str(backend: BackendClient, cell, start: datetime, end: datetime) -> str:
    """Gets the last teros ec measurement for a cell.

    If no data is found for that cell it returns "No Data".

    Args:
        backend: Instance of backend client.
        celll: Cell instance.
        start: Start date.
        end: End date.

    Returns:
        Formatted measurement text.
    """

    teros_df = backend.teros_data(cell, start, end)

    new_teros_ec_df = backend.sensor_data_simple(
        cell, "TEROS12_EC", "Electrical Conductivity", start, end
    )

    if not teros_df.empty:
        ec = data_to_string(teros_df, "ec")
    else:
        ec = data_to_string(new_teros_ec_df, "Electrical Conductivity")

    return ec


def get_temp_str(backend: BackendClient, cell, start: datetime, end: datetime) -> str:
    """Gets the last teros temperature measurement for a cell.

    If no data is found for that cell it returns "No Data".

    Args:
        backend: Instance of backend client.
        cell: Cell instance.
        start: Start date.
        end: End date.

    Returns:
        Formatted measurement text.
    """

    teros_df = backend.teros_data(cell, start, end)

    new_teros_temp_df = backend.sensor_data_simple(
        cell, "TEROS12_TEMP", "Temperature", start, end
    )

    if not teros_df.empty:
        temp = data_to_string(teros_df, "temp")
    else:
        temp = data_to_string(new_teros_temp_df, "Temperature")

    return temp


def get_bme280_temp_str(backend: BackendClient, cell: int, start: datetime, end: datetime) -> str:
    """Gets the last bme280 temperature measurement for a cell.

    If no data is found for that cell it returns "No Data".

    Args:
        backend: Instance of backend client.
        cell: Cell instance.
        start: Start date.
        end: End date.

    Returns:
        Formatted measurement text.
    """

    temp_df = backend.sensor_data_simple(cell, "BME280_TEMP", "Temperature", start, end)

    temp = data_to_string(temp_df, "Temperature")

    return temp


def get_bme280_pressure_str(backend: BackendClient, cell, start: datetime, end: datetime) -> str:
    """Gets the last bme280 pressure measurement for a cell.

    If no data is found for that cell it returns "No Data".

    Args:
        backend: Instance of backend client.
        cell: Cell instance.
        start: Start date.
        end: End date.

    Returns:
        Formatted measurement text.
    """

    pressure_df = backend.sensor_data_simple(
        cell, "BME280_PRESSURE", "Pressure", start, end
    )

    pressure = data_to_string(pressure_df, "Pressure")

    return pressure


def get_bme280_humidity_str(
    backend: BackendClient, cell, start: datetime, end: datetime
) -> str:
    """Gets the last bme280 humidity measurement for a cell.

    If no data is found for that cell it returns "No Data".

    Args:
        backend: Instance of backend client.
        cell: Cell instance.
        start: Start date.
        end: End date.


    Returns:
        Formatted measurement text.
    """

    humidity_df = backend.sensor_data_simple(
        cell, "BME280_HUMIDITY", "Humidity", start, end
    )

    humidity = data_to_string(humidity_df, "Humidity")

    return humidity


def post_cell_data(client: WebClient, name: str, channel: str, cells:
                   list[int], bme280: int):
    """Post cell data into a channel

    Queries the previous day's data and posts the most recent data point. If
    there is no data then it uses the string "No Data".

    Args:
        client: Slack WebClient
        channel: Slack channel to post to
        cells: List of cell ids to query
        bme280: Bme280 cell id
    """

    backend = BackendClient()

    end = datetime.utcnow()
    start = end - timedelta(days=1)

    # top level message
    msg = f"*{name}*\n\n"
    msg += "_No Data_\n"

    # thread dta
    thread = f"Checking data at {end} UTC\n\n"


    # bme280 info
    bme280_cell = backend.cell_from_id(bme280)
    bme280_temp = get_bme280_temp_str(backend, bme280_cell, start, end)
    bme280_pressure = get_bme280_pressure_str(backend, bme280_cell, start, end)
    bme280_humidity = get_bme280_humidity_str(backend, bme280_cell, start, end)

    thread += "*bme280 info:*\n"
    thread += f"\ttemp: {bme280_temp}\n"
    thread += f"\tpressure: {bme280_pressure}\n"
    thread += f"\thumidity: {bme280_humidity}\n"
    thread += "\n"

    # cell info
    for cid in cells:
        cell = backend.cell_from_id(cid)
        if cell is None:
            logger.warning("Cell ID %d not found", cid)
            continue

        voltage = get_voltage_str(backend, cell, start, end)
        current = get_current_str(backend, cell, start, end)
        vwc = get_vwc_str(backend, cell, start, end)
        temp = get_temp_str(backend, cell, start, end)
        ec = get_ec_str(backend, cell, start, end)

        meas_list = [voltage, current, vwc, temp, ec]

        if all(m == "No Data" for m in meas_list):
            msg += f"- {cell.name}\n"
            logger.warning("No data for cell %s (%d)", cell.name, cell.id)

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
        post_cell_data(client, name, config.channel(), cells, g.bme280())


if __name__ == "__main__":
    entry()
