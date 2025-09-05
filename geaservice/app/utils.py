import datetime
import math
import logging
from enum import Enum

class ChannelType(Enum):
    STRING = 0
    ENUM = 1
    INT = 2
    DOUBLE = 3

def adjustResolution(durationSeconds: float, base: int = 10000, scale: int = 900, factor: float = 0.581):
    if durationSeconds < 0:
        logging.error("Duration must be a positive value.")
        raise ValueError("Duration must be a positive value.")

    resolution = base / math.pow(1 + durationSeconds / scale, factor)
    return int(resolution)

def timestampToDate(timestamp: float):
    try:
        date = datetime.datetime.fromtimestamp(timestamp)
        return date.strftime("%d/%m/%Y %H:%M:%S")
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid timestamp: {e}")


def setNPoints(valueMode, dateFrom, dateTo, nPoints):
    try:
        if valueMode in [0, 1]:
            return 10000
        if not nPoints:
            return adjustResolution((int(dateTo) - int(dateFrom)) / 1000)
        nPoints = int(nPoints)
        if nPoints > 10000:
            return 10000
        return nPoints
    except ValueError:
        logging.warning("Invalid 'nPoints' value; defaulting to 3000.")
        return 3000

def processChannels(channel):
    if ',' in channel:
        return [chan.strip() for chan in channel.split(',') if chan.strip() and chan.strip() not in ["None", ""]]
    elif channel.strip() and channel.strip() not in ["None", ""]:
        return [channel.strip()]
    return []


def identifyArchive(channelsByArchive, channelsList):
    channelsListByArchive = {}
    localChannelsByArchive = {k: v for k, v in channelsByArchive.items() if k not in ["- All -", "- All - (last restart)", ""]}

    for channel in channelsList:
        latestEntry = None
        latestKey = None

        for key, valueList in localChannelsByArchive.items():
            for sublist in valueList:
                if channel == sublist[0]:
                    if latestEntry is None or sublist[2] > latestEntry[2]:
                        latestEntry = sublist
                        latestKey = key

        if latestEntry:
            logging.debug(f"Found latest '{channel}' in archive: {latestKey}")
            if latestKey not in channelsListByArchive:
                channelsListByArchive[latestKey] = []
            channelsListByArchive[latestKey].append(channel)

    return channelsListByArchive

def checkType(channelList):
    for channel in channelList:
        count = channel.get("count", 0)
        if count <= 0:
            logging.debug("Channel has no data ('count' = 0)")
            continue

        channeltype = channel.get("type")
        if channeltype is None:
            logging.warning(f"Missing 'type': {channel}")
            continue

        try:
            ctype = ChannelType(channeltype)
        except ValueError:
            logging.error(f"Unknown type ({channeltype}) in channel: {channel}")
            continue

        values = channel.get("values", [])
        if not values or not isinstance(values[0], dict) or "value" not in values[0]:
            logging.error(f"Invalid or missing 'values' in channel: {channel}")
            continue

        first_value_container = values[0]["value"]
        if not isinstance(first_value_container, list) or not first_value_container:
            logging.error(f"'value' field is empty or not a list: {values[0]}")
            continue

        first_value = first_value_container[0]
        logging.debug(f"First value: {first_value} (type: {type(first_value).__name__})")

        # --- Auto-convert STRING if numeric ---
        if ctype == ChannelType.STRING and isinstance(first_value, str):
            for conv, new_type in [(int, ChannelType.INT), (float, ChannelType.DOUBLE)]:
                try:
                    first_value = conv(first_value)
                    logging.warning(f"STRING looks like {new_type.name}, auto-correcting.")
                    ctype = new_type
                    channel["type"]=ctype.value
                    break
                except ValueError:
                    continue

        # --- Final validation ---
        type_checks = {
            ChannelType.ENUM: int,
            ChannelType.STRING: str,
            ChannelType.INT: int,
            ChannelType.DOUBLE: (float, int),
        }

        expected_type = type_checks.get(ctype)
        if isinstance(first_value, expected_type):
            logging.debug(f"Validation OK: {ctype.name} value is valid.")
        else:
            logging.error(
                f"Validation FAIL: {ctype.name} expected {expected_type}, "
                f"got {type(first_value).__name__} with value '{first_value}'"
            )
