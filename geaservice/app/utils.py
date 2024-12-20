import datetime
import math
import logging

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

