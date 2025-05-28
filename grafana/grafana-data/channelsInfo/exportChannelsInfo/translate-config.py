import os
import json

inputPath = "./config/gea-config"
outputPath= "./config/ted-config"


#Given a system's path, returns the sections and channels as JSON
def getSections(systemPath):
    #Tags of GEA config files to ignore
    ignoreTags=['#[SUBTABLE]','#[CSSCLASS]','#[QUERYSTRPAIRS]','#[ITEMSPERROW]','[MK]','[HTML]']

    #auxiliary variables
    currentSection = ''
    sections={}
    channelsAux=[]

    #Open system's config file 
    fileSystem = open(systemPath,'r')

    for line in fileSystem:
        #skip invalid lines
        if not any(substring in line for substring in ignoreTags) and line !='' and line !="\n" and line != ' ' and not line.startswith('<'):
            #if line starts with '#' contains a tag
            if line.startswith("#"):
                if '[SECTION]' in line:
                    #if section is not empty, and there are channels in channels Aux
                    if currentSection!="" and len(channelsAux)>0:
                        #register section element with its channels
                        sections[currentSection] = channelsAux
                    #clean section name
                    currentSection = ' '.join(line.split(' ')[1:]).strip()
                    #when a section is detected, reset the channels
                    channelsAux=[]
                    
                    #if the section is empty, put a default name
                    if(currentSection==""):
                        currentSection="Unamed Section"

                    #clear [CP] tag in section
                    # if("[CP]" in currentSection):
                    #     currentSection= ' '.join(currentSection.split(" ")[1:]).strip()

            #if there's no tag, then is channel info
            else:
                #GEA config uses '#' to separate channel code and channel name
                line = line.split('#')
                name =""
                #some channels don't have a name, so the name is defined as the code
                if len(line)>1:
                    channel = line[0].strip()
                    name = line[1].strip()
                else:
                    channel = line[0].strip()
                    name = channel
                #the channel is stored as a JSON object in the channelsAux list
                channelsAux.append({channel:name})
    
    #once all lines were read, create currentSection key to channel list value
    sections[currentSection] = channelsAux
    return sections    

#Translate GEA config to TED config
def translate(inputPath,outputPath):
    #The folders are treated as categories
    categories = os.listdir(inputPath)
    #Create directories for categories
    for dir in categories:
        if not (os.path.exists(f"{outputPath}/{dir}")):
            os.mkdir(f"{outputPath}/{dir}")
    #For each category folder 
    for category in categories:
        #Get subsystem's list
        systems = os.listdir(f"{inputPath}/{category}")
        #For each system
        for system in systems:
            #Get the old path
            oldPath = f"{inputPath}/{category}/{system}"
            #Extract sections of that system's file
            sections = getSections(oldPath)
            #Clean system name from path
            system = system.split('Page')[0]
            #Create TED config
            newPath = f"{outputPath}/{category}/{system}.json"
            newFile = open(newPath, 'w')
            newFile.write(json.dumps(sections,indent=4))
       

translate(inputPath,outputPath)
