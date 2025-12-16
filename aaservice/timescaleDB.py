#!/usr/local/bin/python
import psycopg
from psycopg import sql
import random
from datetime import date, timedelta, datetime
import os
conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="calibrations",
    user="admin",
    password="admin"
)

cur = conn.cursor()

systems = ["ghost","gmos","f2","gsaoi","m1","m2"]

for system in systems:
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {system} (
        time TIMESTAMP NOT NULL,
        key TEXT,
        value DOUBLE PRECISION
    );
    """)


calibDataPath = "/calibrations"
calibParentDir = os.listdir(calibDataPath)

# def getInstrumentFromFileName(fileName):
#     print(fileName)

for direc in calibParentDir:
    # print(direc)
    filePath = f"{calibDataPath}/{direc}"
    files = os.listdir(filePath)
    for fileName in files:
        if "." in fileName:
            # print(fileName)
            # nameInfo = fileName.split("_")
            # system = nameInfo[1] if "." not in nameInfo[1] else nameInfo[1].split(".")[0]
            with open(f"{filePath}/{fileName}") as f:
                for line in f:
                    dataByLine = line.split(" ")
                    print(dataByLine)


                    # Normalize date and time
                    date = dataByLine[0].replace('-', '/')
                    time = dataByLine[1]
                    # Ensure fractional seconds exist
                    if '.' not in time:
                        time += '.0'
                    datetime = datetime.strptime(f"{date} {time}", "%Y/%m/%d %H:%M:%S.%f")
        
                    key = dataByLine[2]
                    
                    system = key.split(":")[1]
                    value = dataByLine[-1].strip()


                    print(datetime)
                    print(system)
                    print(key)
                    print(value)
                    
                    try:
                        cur.execute(
                            sql.SQL("""
                                INSERT INTO {} (time, key, value)
                                VALUES (%s, %s, %s)
                            """).format(sql.Identifier(system.lower())),
                            (
                                datetime,
                                key,
                                value,
                            )
                        )
                    except Exception as e:
                        conn.rollback()
conn.commit()
conn.close()
