
from datetime import datetime, timedelta

import pandas as pd
import requests
from slack_sdk import WebClient

import logging
logger = logging.getLogger(__name__)

SLACK_TOKEN = "TOKEN_HERE"
CLIENT_ID = "#soil-power-students"

class Cell:
    """Class representing a cell in the Dirtviz API."""

    def __init__(self, data: str):
        """Initialize the Cell object from a cell ID.

        Args:
            data: json data from the Dirtviz API containing cell information.
        """

        self.id = data["id"]
        self.name = data["name"]
        self.location = data["location"]
        self.latitude = data["latitude"]
        self.longitude = data["longitude"]

    def __repr__(self):
        return f"Cell(id={self.cell_id}, name={self.name})"


class BackendClient:
    """Client for interacting with the Dirtviz API."""

    DEFAULT_BASE_URL = "https://dirtviz.jlab.ucsc.edu/api/"

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        """Initialize the BackendClient.

        Sets the base URL for the API. Defaults to the Dirtviz API.
        """

        self.base_url = base_url

    def get(self, endpoint: str, params: dict = None) -> dict:
        """Get request to the API.

        Args:
            endpoint: The API endpoint to request.
            params: Optional parameters for the request.

        Returns:
            A dictionary containing the response data.
        """

        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def power_data(self, cell: Cell, start: datetime, end: datetime) -> pd.DataFrame:
        """Gets power data for a specific cell.

        Args:
            cell: The Cell object for which to get power data.
            start: The start date of the data.
            end: The end date of the data.

        Returns:
            A pandas DataFrame containing the power data.
        """

        start_str = self.format_time(start)
        end_str = self.format_time(end)

        endpoint = f"/power/{cell.id}"
        params = {
            "startTime": start_str,
            "endTime": end_str,
        }

        data = self.get(endpoint, params=params)

        data_df = pd.DataFrame(data)
        data_df["timestamp"] = pd.to_datetime(data_df["timestamp"])

        return data_df

    def teros_data(self, cell: Cell, start: datetime, end: datetime) -> pd.DataFrame:
        """Gets teros data for a specific cell.

        Args:
            cell: The Cell object for which to get teros data.
            start: The start date of the data.
            end: The end date of the data.

        Returns:
            A pandas DataFrame containing the teros data.
        """

        start_str = self.format_time(start)
        end_str = self.format_time(end)

        endpoint = f"/teros/{cell.id}"
        params = {
            "startTime": start_str,
            "endTime": end_str,
        }

        data = self.get(endpoint, params=params)

        data_df = pd.DataFrame(data)
        data_df["timestamp"] = pd.to_datetime(data_df["timestamp"])

        return data_df

    @staticmethod
    def format_time(dt: datetime) -> str:
        """Formats a datetime object to the API's expected string format.

        Args:
            dt: The datetime object to format.

        Returns:
            A string representing the formatted datetime.
        """

        timestamp_format = "%a, %d %b %Y %H:%M:%S GMT"
        dt_str = dt.strftime(timestamp_format)
        return dt_str

    def cell_from_id(self, cell_id: int) -> Cell | None:
        """Get a Cell object from its ID.

        Args:
            cell_id: The ID of the cell.

        Returns:
            A Cell object. None if the cell does not exist.
        """

        cell_list = self.cells()

        for cell in cell_list:
            if cell.id == cell_id:
                return cell

        return None

    def cell_from_name(self, name: str) -> Cell | None:
        """Get a Cell object from its name.

        Args:
            name: The name of the cell.

        Returns:
            A Cell object. None if the cell does not exist.
        """

        cell_list = self.cells()

        for cell in cell_list:
            if cell.name == name:
                return cell

        return None

    def cells(self) -> list[Cell]:
        """Gets a list of all cells from the API.

        Returns:
            A list of Cell objects.
        """

        cell_list = []

        endpoint = "/cell/id"
        cell_data_list = self.get(endpoint)

        for c in cell_data_list:
            cell = Cell(c)
            cell_list.append(cell)

        return cell_list




def post_hello_world(client: WebClient):
    msg = "Hello, World!"
    client.chat_postMessage(channel=CLIENT_ID, text=msg)

def post_cell_data(client: WebClient, cells: list[int]):
    """Post cell data into a channel

    Queries the previous day's data and posts the most recent data point. If
    there is no data then it uses the string "No Data".

    Args:
        client: Slack WebClient
        cells: List of cell ids to query
    """

    backend = BackendClient()

    end = datetime.utcnow()
    start = end - timedelta(days=1)

    msg = f"Checking data at {end} UTC\n\n"

    for cid in cells:
        cell = backend.cell_from_id(cid)
        if cell is None:
            logger.warning("Cell ID %d not found", cid)
            continue


        power_df = backend.power_data(cell, start, end)
        teros_df = backend.teros_data(cell, start, end)

        voltage = power_df['v'].iloc[-1] if not power_df.empty else 'No Data'
        current = power_df['i'].iloc[-1] if not power_df.empty else 'No Data'
        vwc = teros_df['vwc'].iloc[-1] if not teros_df.empty else 'No Data'
        temp = teros_df['temp'].iloc[-1] if not teros_df.empty else 'No Data'
        ec = teros_df['ec'].iloc[-1] if not teros_df.empty else 'No Data'

        msg += f"*{cell.name}*:\n"
        msg += f"\tv:    {voltage} mV\n"
        msg += f"\ti:    {current} mA\n"
        msg += f"\tvwc:  {vwc} %\n"
        msg += f"\ttemp: {temp} C\n"
        msg += f"\tec:   {ec} dS/m\n"
        msg += "\n"

    client.chat_postMessage(channel=CLIENT_ID, text=msg)

def entry():
    """Entrypoint for the slack bot"""

    logging.basicConfig(level=logging.INFO)

    cells = list(range(1514, 1539))
    logger.info(f"Posting data for cells: {cells}")

    client = WebClient(token=SLACK_TOKEN)
    #post_hello_world(client)
    post_cell_data(client, cells)


if __name__ == "__main__":
    entry()
