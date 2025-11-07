from epics import PV

def get_enum_strs(pvName):
    print(f"queyring {pvName}")
    pv = PV(pvName)
    if pv.wait_for_connection(timeout=2.0):
        return pv.enum_strs
    return None
