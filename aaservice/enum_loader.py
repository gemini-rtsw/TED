import os
import asyncio
import mysql.connector
import json
from epicsutils import get_enum_strs

def get_mysql_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

async def loadEnumStates(pvName):
    conn = get_mysql_connection()
    cursor = conn.cursor()

    loop = asyncio.get_event_loop()
    enum_strs = await loop.run_in_executor(None, get_enum_strs, pvName)

    if not enum_strs or len(enum_strs) == 0:    
        print(f"⚠️ Could not get enum_strs for {pvName}")
        cursor.close()
        conn.close()
        return

    cursor.execute(
        "SELECT typeInfoJSON FROM PVTypeInfo WHERE JSON_EXTRACT(typeInfoJSON, '$.pvName') = %s",
        (pvName,)
    )
    row = cursor.fetchone()

    if row:
        type_info = json.loads(row[0])
        type_info.setdefault("extraFields", {})["enum_strs"] = enum_strs
        new_json = json.dumps(type_info)

        cursor.execute(
            "UPDATE PVTypeInfo SET typeInfoJSON = %s WHERE JSON_EXTRACT(typeInfoJSON, '$.pvName') = %s",
            (new_json, pvName)
        )
        conn.commit()
        print(f"✅ Updated enum_strs for {pvName}")

    cursor.close()
    conn.close()


async def loadAllEnumsAtOnce():
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pvName FROM PVTypeInfo 
        WHERE JSON_EXTRACT(typeInfoJSON, '$.DBRType') = 'DBR_SCALAR_ENUM';
    """)
    enums = cursor.fetchall()
    cursor.close()
    conn.close()

    sem = asyncio.Semaphore(5)

    async def sem_task(pvName):
        async with sem:
            try:
                await loadEnumStates(pvName)
            except Exception as e:
                print(f"❌ Error loading {pvName}: {e}")

    tasks = [sem_task(enumPvName) for (enumPvName,) in enums]
    await asyncio.gather(*tasks)

    return [e[0] for e in enums]
