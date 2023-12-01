#! /usr/bin/python3

import requests
import wget
import os
import json
import time


def SaveFile(Asset,StoragePath,Release):
  PathOut = StoragePath+"/"+Release
  os.makedirs(PathOut, exist_ok=True)
  wget.download(str(Asset["browser_download_url"]), out = PathOut)
  
class Target:
  def __init__(self, Name, Desc, URL):
    self.Name = Name
    self.Desc = Desc
    self.URL = URL

LXMEventIntegration = True
Targets = []
Targets.append(Target("RNodeFirmware","RNode Firmware","https://api.github.com/repos/markqvist/RNode_Firmware/releases/latest"))
Targets.append(Target("RNS","Reticulum","https://api.github.com/repos/markqvist/Reticulum/releases/latest"))
Targets.append(Target("NomadNet","Nomad Network","https://api.github.com/repos/markqvist/NomadNet/releases/latest"))
Targets.append(Target("Sideband","Sideband","https://api.github.com/repos/markqvist/Sideband/releases/latest"))
Targets.append(Target("LXMF","LXMF","https://api.github.com/repos/markqvist/LXMF/releases/latest"))



userdir = os.path.expanduser("~")
filedir = userdir+"/.nomadnetwork/storage/files/"
pagedir = userdir+"/.nomadnetwork/storage/pages/"
triggerdir = userdir+"/.lxmevents/triggers"


for T in Targets:
  try:
    response = requests.get(T.URL)

    ReleaseName = response.json()["name"]
    if not os.path.exists(filedir+T.Name+"/"+ReleaseName):
      buffer = "Released: "+T.Desc+", version "+ReleaseName+"\n"
      buffer = buffer+"Published on: "+response.json()["published_at"]+"\n\n"
      for A in response.json()["assets"]:
        #print(A["name"])
    #    if(A["name"]=="release.json"):
        SaveFile(A,filedir+T.Name,ReleaseName)
        buffer = buffer + "`["+A["name"]+"`:/file/"+T.Name+"/"+ReleaseName+"/"+A["name"]+"] - "+str(A["size"])+" bytes\n\n"
      buffer = buffer+"\n\nEnd of directory"
      FileOut = pagedir+T.Name+"/"+ReleaseName
      os.makedirs(FileOut, exist_ok=True)
      with open(FileOut+"/index.mu", "w") as outputfile:
        outputfile.write(buffer)
      FileOut = pagedir+T.Name+"/latest.mu"
      with open(FileOut, "w") as outputfile:
        outputfile.write(buffer)
      if LXMEventIntegration:
        buffer = {}
        J = response.json()
        buffer["event"]=T.Desc
        buffer["name"] = ReleaseName
        #print(buffer)
        with open(triggerdir+"/"+T.Name,'w') as f:
          json.dump(buffer,f)
    time.sleep(60)
  except:
    pass
