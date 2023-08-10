import os
import json
from jsonpath_ng import jsonpath, parse

tedConfPath= "./config/ted-config"

def extractInfo(tedConfPath):
    records=[]
    #The folders are treated as categories
    categories = os.listdir(tedConfPath)
    #For each category folder 
    for category in categories:
        #Get subsystem's list
        systems = os.listdir(f"{tedConfPath}/{category}")
        #For each system
        for system in systems:
            file = open(f"{tedConfPath}/{category}/{system}")
            data = json.load(file)
            #Clean system name from path
            system = system.split('Page')[0]
            system = system.split('.')[0]
            #exctact information of JSON files
            for section,channels in data.items():
                for chan in channels:
                    channelKeys = chan.keys()
                    channelList = list(channelKeys)
                    channel = channelList[0]
                    namesValues = chan.values()
                    namesList = list(namesValues)
                    name = namesList[0]
                    print(category,system,section,name,channel)
                    record = {"category":category,"system":system,"section":section,"name":name,"channel":channel}
                    records.append(record)
    return records

def insertIntoSql(records):
    import sqlite3
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("../ted-channels.db")
    # Create a cursor object to interact with the database
    cursor = conn.cursor()
    # Define a table schema (if the table doesn't exist)
    create_table_query = '''
        CREATE TABLE IF NOT EXISTS channelsConfig (
        id INTEGER PRIMARY KEY,
        category TEXT NOT NULL,
        system TEXT NOT NULL,
        section TEXT NOT NULL,
        name TEXT NOT NULL,
        channel TEXT NOT NULL
        );
    '''
    cursor.execute(create_table_query)

    for record in records:
    # Insert data into the table
        insert_query = f'INSERT INTO channelsConfig (category, system, section, name, channel) VALUES ("{record["category"]}","{record["system"]}","{record["section"]}","{record["name"]}","{record["channel"]}");'
        cursor.execute(insert_query)
    # Commit the changes and close the connection
    conn.commit()
    conn.close()

records=extractInfo(tedConfPath)
insertIntoSql(records)
