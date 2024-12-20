import logging
from utils import timestampToDate

def fetchValues(gea, archiveKey, channelsList, dateFrom, dateTo, nPoints, valueMode):
    allData = []
    currentDate = dateFrom
    existingDataSet = {}
    lastSecs = 0
    lastNano = 0
    logging.info(f"Attempting to retrieve data from {timestampToDate(dateFrom)} to {timestampToDate(dateTo)}.")
    logging.info (f"Set number of point to {nPoints}")
    while currentDate < dateTo:
        try:
            geaRecord = gea.archiver.values(
                archiveKey,
                channelsList,
                currentDate,
                0,
                dateTo,
                0,
                nPoints,
                valueMode
            )

            if not geaRecord or not any(record.get('values') for record in geaRecord):
                logging.warning(f"No data found for channels: {channelsList} from {timestampToDate(currentDate)} to {timestampToDate(dateTo)}.")
                break

            for record in geaRecord:
                name = record.get("name")
                values = record.get("values", [])
                if values:
                    tmpSecs= values[-1].get("secs", 0)
                    if tmpSecs > lastSecs:
                        lastSecs = tmpSecs
                        lastNano = int(values[-1].get("nano", 1))/1000000000

                if name in existingDataSet:
                    existingDataSet[name]["values"].extend(values)
                    existingDataSet[name]["count"] = len(existingDataSet[name]["values"])
                else:
                    existingDataSet[name] = record

            newDate = int(lastSecs + lastNano)
            if newDate == currentDate:
                logging.info(f"Data retrieval for channels '{channelsList}' completed.")
                break
            
            logging.debug(f"Data obtained from {timestampToDate(currentDate)} to {timestampToDate(newDate)}.")
            currentDate = newDate

        except Exception as e:
            logging.error(f"Error fetching data for channels '{channelsList}': {str(e)}")
            break

    allData = list(existingDataSet.values())
    return allData

