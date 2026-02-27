#!/usr/local/bin/python
import argparse
import psycopg
from psycopg import sql
import os
from pathlib import Path
from datetime import date, datetime, timedelta


calib_data_path = Path("/calibrations")

SYSTEMS = ["ghost","gmos","f2","gsaoi","m1","m2"]

DB_CONFIG={    
    "host":"localhost",
    "port":5432,
    "dbname":"calibrations",
    "user":"admin",
    "password":"admin"
}

def get_conn():
    return psycopg.connect(**DB_CONFIG)

def initTables():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                for system in SYSTEMS:
                    cur.execute(
                        sql.SQL(f"""
                    CREATE TABLE IF NOT EXISTS {system} (
                        time TIMESTAMP NOT NULL,
                        key TEXT,
                        value DOUBLE PRECISION,
                        PRIMARY KEY (time, key)
                    );
                    """).format(sql.Identifier(system)))  
        print("Tables created")
        return 0
    except Exception as e:
        print(f"Error creating tables: {e}")
        return 1

def parse_timerange(date_str: str):
    date_str = date_str.strip()
    print(date_str)
    print(len(date_str))
    # YEAR
    if len(date_str) == 4:
        start = datetime(int(date_str), 1, 1)
        end = datetime(int(date_str) + 1, 1, 1)
    # MONTH
    elif len(date_str) == 6:
        start = datetime.strptime(date_str, "%Y%m")
        if start.month == 12:
            end = datetime(start.year + 1, 1, 1)
        else:
            end = datetime(start.year, start.month + 1, 1)
    # DAY or DATETIME
    else:
        ts = datetime.strptime(date_str, "%Y%m%d")
        start = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    return start, end

def queryCalib(date_str: str, key: str):
    system = key.split(":")[1]
    try:
        parse_timerange(date_str)
        start, end = parse_timerange(date_str)
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("""
                        SELECT *
                        FROM {table}
                        WHERE "key" = %s
                          AND "time" >= %s
                          AND "time" < %s
                        ORDER BY "time"
                    """).format(
                        table=sql.Identifier(system)
                    ),
                    (key, start, end)
                )

                rows = cur.fetchall()
                return rows
        return 0
    except Exception as e:
        print(f"Error querying tables: {e}")
        return 1

def insertAll():
    allDays = calib_data_path.iterdir()
    for day in allDays:
        print(day)
        insertDay(day)

def getDirsByPrefix(prefix):
    dirs = sorted(
        (p for p in calib_data_path.iterdir()
         if p.is_dir() and p.name.startswith(prefix)),
        key=lambda p: p.name
    )    
    for d in dirs:
        yield d.name

def insertDay(dateStr):
    dayPath = calib_data_path / dateStr
    for file in dayPath.iterdir():
        if file.is_file():
            with file.open() as f:
                for line in f:
 
                    dataByLine = line.split(" ")
                    print(dateStr, dataByLine)
                    date = dataByLine[0].replace('-', '/')
                    time = dataByLine[1]
                    if '.' not in time:
                        time += '.0'
                        ts = datetime.strptime(f"{date} {time}", "%Y/%m/%d %H:%M:%S.%f")
                        key = dataByLine[2]                        
                        system = key.split(":")[1]
                        value = dataByLine[-1].strip()
                    try:
                        value = float(value)
                    except ValueError:
                        print(f"Skipping non-numeric value: {value}")
                        continue
                    try:
                        with get_conn() as conn:
                            with conn.cursor() as cur:
                                cur.execute(
                                    sql.SQL("""
                                        INSERT INTO {} (time, key, value)
                                        VALUES (%s, %s, %s)
                                        ON CONFLICT (time, "key") DO NOTHING
                                    """).format(sql.Identifier(system.lower())),
                                    (
                                        ts,
                                        key,
                                        value,
                                    )
                                )
                    except Exception as e:
                        conn.rollback()
def insertToday():
    today = date.today()
    today_str = today.strftime("%Y%m%d")
    print(today_str)
    try:
        insertDay(today_str)
    except Exception as e:
        print(f"Failed: {e}")

def main():
    parser = argparse.ArgumentParser(
        prog="calibrations.py",
        description="TED TimescaleDB calibration data loader"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize tables")

    subparsers.add_parser("all", help="Load all calibrations")

    query_parser = subparsers.add_parser("query", help="Query calibration value")
    query_parser.add_argument(
        "date",
        help="Date in YYYYMMDD, YYYYMM, YYYY, (e.g. 202512)"
    )
    query_parser.add_argument(
        "key",
        help="Key value"
    )

    prefix_parser = subparsers.add_parser("prefix", help="Load calibrations for directories that matches a prefix")
    prefix_parser.add_argument(
        "date",
        help="Date in YYYYMMDD, YYYYMM, YYYY, (e.g. 202512)"
    )
    
    day_parser = subparsers.add_parser("day", help="Load calibrations for one day")
    day_parser.add_argument(
        "date",
        help="Date in YYYYMMDD (e.g. 20251201)"
    )
    
    subparsers.add_parser("today", help="Load today calibration")

    args = parser.parse_args()

    match args.command:
        case "init":
            initTables()
        case "query":
            print(queryCalib(args.date, args.key))
        case "all":
            insertAll()
        case "prefix":
            insertPrefix(args.date)
        case "day":
            insertDay(args.date)
        case "today":
            insertToday()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())