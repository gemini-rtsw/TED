# Standard library imports
import os
import logging
import json

# Related third-party imports

# Configure logging
logging = logging.getLogger('CACHE')

archivesPath="../jsons/archives.json"
channelsByArchivePath="../jsons/channelsByArchive.json"

def loadJsonFile(filePath, fetchFunction, cacheName):
    """Helper function to load JSON data from a file or fetch it if not available."""
    if os.path.exists(filePath):
        logging.debug(f"File '{filePath}' exists.")
        try:
            with open(filePath, 'r') as jsonFile:
                data = json.load(jsonFile)
                logging.info(f"Successfully loaded {cacheName} from file.")
                return data
        except Exception as e:
            logging.error(f"Failed to load {cacheName} from file: {e}")
            return fetchFunction()
    else:
        logging.debug(f"File '{filePath}' does not exist.")
        return fetchFunction()

def readArchives(gea):
    archivesDict = {}
    try:
        logging.info("Retrieving list of archives.")
        archives = gea.archiver.archives()
        for archive in archives:
            archivesDict[archive['name']] = archive['key']
        logging.info("Successfully retrieved archives.")
    except Exception as e:
        logging.error(f"Failed to retrieve archives: {e}")

    try:
        logging.info("Saving archives to 'archives.json'.")
        with open(archivesPath, 'w') as jsonFile:
            json.dump(archivesDict, jsonFile, indent=4)
    except Exception as e:
        logging.error(f"Failed to save archives to file: {e}")

    return archivesDict

def readChannels(gea, archivesCache):
    channelsByArchiveDict = {}
    try:
        logging.info("Retrieving channels by archive.")
        for name, key in archivesCache.items():
            logging.debug(f"Processing archive '{name}' (Key: {key})")
            channelNames = [["None","None","None"]]

            try:
                channels = gea.archiver.names(int(key), "")
                for channel in channels:
                    channelNames.append([channel['name'],int(channel['start_sec']*1000 + channel['start_nano']/1000000 ),int(channel['end_sec']*1000 + channel['end_nano']/1000000 )])
                channelsByArchiveDict[name] = channelNames

            except Exception as channelError:
                logging.error(f"Failed to retrieve channels for '{name}': {channelError}")

        logging.info("Successfully retrieved channels.")
    except Exception as e:
        logging.error(f"Failed to retrieve channels: {e}")

    try:
        logging.info("Saving channels by archive to 'channelsByArchive.json'.")
        with open(channelsByArchivePath, 'w') as jsonFile:
            json.dump(channelsByArchiveDict, jsonFile, indent=4)
    except Exception as e:
        logging.error(f"Failed to save channels to file: {e}")

    return channelsByArchiveDict

def initializeCache(gea):
    """Initialize or load the cache.""" 
    archivesCache = loadJsonFile(archivesPath, lambda: readArchives(gea), "archives")
    channelsByArchiveCache = loadJsonFile(channelsByArchivePath, lambda: readChannels(gea, archivesCache) , "channels")
    return [archivesCache, channelsByArchiveCache]

def updateArchivesCache (gea):
    return readArchives(gea)

def updateChannelsCache(gea,archivesCache):
    return readChannels(gea,archivesCache)
