import Events

import time
from datetime import datetime
from sbapp.sideband.sense import Telemeter

TestAddy = "3c12dba895c18fe8997ebb556de9d951"


def TestCallback():
  now = datetime.now()
  R = "Not sure what's going on here\nbut we're gonna try anyway.\n\n" 
  R = R + now.strftime("%m/%d/%Y, %H:%M:%S")
  T = Telemeter()
  T.synthesize("battery")
  charge_percent = 71
  is_charging = True
  T.sensors["battery"].data={"charge_percent": round(charge_percent, 1), "charging": is_charging}
  return Events.EventReturn(R,Telemetry = T.packed())

E = Events.LXMEventHandler("Testbed Handler")
if not E.LoadEvents():
#  E.FireEvent("BIT")
  print("Generating Test Events")
  E.AddEvent("BIT",EventCallback = TestCallback)
  E.AddEvent("Debug",EventText = "I need a nap.")
  S = Events.Subscriber(TestAddy)
  E.AddSubscriber("Debug",S)
  S = Events.Subscriber(TestAddy)
  S.RejectTests = True
  E.AddSubscriber("BIT",S)
  E.EventList["BIT"].Description = "Built-In Test"
  #E.AddSubscriber("FIT",S)

#E.AddEvent("BIT")
#E.AddEvent("BIT", Overwrite = True)

#E.SetCallback("NIT",None)
#E.SetCallback("BIT",TestCallback)
E.FireEvent("BIT")
E.FireEvent("Debug",isTest = True)
print(E.EnumerateEvents())
print(E.ListEvents())
#time.sleep(30)
E.SaveEvents()
