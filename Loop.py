import Events
from datetime import datetime
import time


#def GitHubRelease(J):
#  now = datetime.now()
#  #print(J)
#  R = "There's been a new release at the "+str(J["event"])+" repository: "+str(J["name"])
#  return Events.EventReturn(R)


# Instatniate Event Handler
E = Events.LXMEventHandler("BtB Node Romeo Alerts")

GH = Events.BuiltIn.GitHubRelease

print("Initializing")
# Add testing events
E.AddEvent("RNodeFirmware",EventCallback = GH,Description = "Updates to the RNode Firmware")
E.AddEvent("LXMF",EventCallback = GH, Description = "LXMF Router Updates")
E.AddEvent("RNS",EventCallback = GH, Description = "New verions of the Reticulum Network Stack")
E.AddEvent("NomadNet",EventCallback = GH, Description = "Nomad Network Updates")
E.AddEvent("Sideband",EventCallback = GH, Description = "Updates to the Sideband client")


E.SaveEvents() # Save events to file for theoretical loading
print("Initialization complete. Standing by.")


LastTime = time.time()
AnnounceTime = 360
E.Announce() # Announce on load

while True: # Sweep events every 20 seconds and process any active triggers.
  if time.time() > LastTime + AnnounceTime:
    LastTime = time.time()
    E.Announce()
  E.LoadEvents()
  E.SweepTriggers()
  time.sleep(20)

