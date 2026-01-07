#!/usr/bin/python

# policies.py based on the default policy by  M. Shankar, Jan 31, 2012
#
# This is the policies.py used to enforce policies for archiving PVs
# At a very high level, when users request PVs to be archived, the mgmt web app samples the PV to determine event rate and other parameters.
# In addition, various fields of the PV like .NAME, .ADEL, .MDEL, .RTYP etc are also obtained
# These are passed to this python script as a dictionary argument to a method called determinePolicy
# The variable name in the python environment for this information is 'pvInfo' (so use other variable names etc.).
# The method is expected to use this information to make decisions on various archiving parameters.
# The result is expected to be another dictionary that is placed into the variable called "pvPolicy".
# Optionally, fields in addition to the VAL field that are to be archived with the PV are passed in as a property of pvPolicy called 'archiveFields'
# If the user overrides the policy, this is communicated in the pvinfo as a property called 'policyName'
#
# In addition, this script must communicate the list of available policies to the JVM as another method called getPolicyList which takes no arguments.
# The results of this method is placed into a variable called called 'pvPolicies'.
# The dictionary is a name to description mapping - the description is used in the UI; the name is what is communicated to determinePolicy as a user override
#
# In addition, this script must communicate the list of fields that are to be archived as part of the stream in a method called getFieldsArchivedAsPartOfStream.
# The results of this method is placed into a list variable called called 'pvStandardFields'.


import sys
import math

def round_well(eventRate):
    # Check if the eventRate is greater than 1 to determine significant digits
    if eventRate > 1:
        # Calculate the number of digits in eventRate
        digits = int(math.log10(eventRate)) + 1
        # Take the floor of the inverse to get rid of the fractional part
        # and convert it to a string formatted to the correct number of significant digits
        sampling = str(math.floor(1/eventRate * 10**digits) / 10**digits)
    else:
        # If eventRate is 1 or less, we just take the floor of the inverse
        # to get a whole number (integer)
        sampling = math.floor(1/eventRate)
    return sampling

# Generate a list of policy names. This is used to feed the dropdown in the UI.
def getPolicyList():
    pvPoliciesDict = {}
    pvPoliciesDict["Default"] = "Save all values"
    return pvPoliciesDict


# Define a list of fields that will be archived as part of every PV.
# The data for these fields will included in the stream for the PV.
# We also make an assumption that the data type for these fields is the same as that of the .VAL field
def getFieldsArchivedAsPartOfStream():
	 return [];

# We use the environment variables ARCHAPPL_SHORT_TERM_FOLDER and ARCHAPPL_MEDIUM_TERM_FOLDER to determine the location of the STS and the MTS in the appliance
shorttermstore_plugin_url = "pb://localhost?name=STS&rootFolder=${ARCHAPPL_SHORT_TERM_FOLDER}&partitionGranularity=PARTITION_DAY&consolidateOnShutdown=true&hold=8&gather=1"
mediumtermstore_plugin_url = "pb://localhost?name=MTS&rootFolder=${ARCHAPPL_SHORT_TERM_FOLDER}&partitionGranularity=PARTITION_MONTH&consolidateOnShutdown=true&hold=12&gather=1"
longtermstore_plugin_url = "pb://localhost?name=LTS&rootFolder=${ARCHAPPL_LONG_TERM_FOLDER}&partitionGranularity=PARTITION_YEAR"


def determinePolicy(pvInfoDict):
    pvPolicyDict = {}
    userPolicyOverride = pvInfoDict.get("policyName")
    if userPolicyOverride in ["Save all values", None]:
        if pvInfoDict.get("SCAN") and  pvInfoDict["SCAN"] != "I/O Intr" and pvInfoDict["SCAN"] != "Passive" and pvInfoDict["SCAN"] != "Event":
            pvPolicyDict["samplingPeriod"] = float(pvInfoDict["SCAN"].split()[0])
        else:
            pvPolicyDict["samplingPeriod"] = float(round_well(pvInfoDict["eventRate"]))
        pvPolicyDict["samplingMethod"] = "MONITOR"
        pvPolicyDict["dataStores"] = [
            shorttermstore_plugin_url,
            mediumtermstore_plugin_url,
            longtermstore_plugin_url,
        ]
        pvPolicyDict["policyName"] = "Save all values"
    pvPolicyDict["archiveFields"]=[]
    return pvPolicyDict
