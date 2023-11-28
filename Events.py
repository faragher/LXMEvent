import os
import sys
import RNS
import LXMF
import time
from RNS.vendor import umsgpack as umsgpack


UseReticulumID = True

class LXMEvent:
  def __init__(self, EventName, EventText):
    self.Name = EventName
    self.Text = EventText
    self.Callback = None
    self.Subscribers = {}
    
  def __str__(self):
    return self.Name
    
  def AddSubscriber(self, Sub):
    if not Sub.Address:
      RNS.log("No subscriber address found")
      return
    #Will overwrite the config if it exists, but otherwise should not error
    self.Subscribers[Sub.Address] = Sub
    
class Subscriber:
  def __init__(self, SubbedAddress):
    self.Address = SubbedAddress
    self.RejectTests = False
    
class EventReturn:
  def __init__(self,TextPayload,Telemetry = None):
    self.Text = TextPayload
    self.Telemetry = Telemetry

class LXMEventHandler:
  def __init__(self, DisplayName):
    self.display_name = DisplayName
    self.R = RNS.Reticulum()
    self.userdir = os.path.expanduser("~")
    self.EventList = {}
    
    #self.EventList["BIT"] = LXMEvent("BIT","BIT is GO.")

    if UseReticulumID:
      self.configdir = self.userdir+"/.nomadnetwork"
      self.identitypath = self.configdir+"/storage/identity"
      if os.path.exists(self.identitypath):
        self.ID = RNS.Identity.from_file(self.identitypath)
      else:
        sys.exit("NomadNet identity not found")
    else:
      sys.exit("No valid identity configuration found.")
      
    self.L = LXMF.LXMRouter(identity = self.ID, storagepath = self.userdir+"/LXMEvent")
    self.D = self.L.register_delivery_identity(self.ID, display_name=self.display_name)
    
  def SetCallback(self, Target, CB):
    if Target not in self.EventList:
      RNS.log("Event "+str(Target)+" not in event list.")
      return
    self.EventList[Target].Callback = CB
    
  def AddEvent(self, EventName, EventText = "This event has no configured text", EventCallback = None, Overwrite = False):
    E = LXMEvent(EventName,EventText)
    if EventCallback:
      E.Callback = EventCallback
    if EventName in self.EventList:
      RNS.log("Event "+str(EventName)+" already exists.")
      if Overwrite:
        RNS.log("Overwrite is set. Replacing.") 
        self.EventList[EventName] = E
      else:
        RNS.log("Overwrite not set. Rejecting.")
    else:
      self.EventList[EventName] = E
    
  def FireEvent(self,Event, isTest = False):
    E = self.EventList[Event]
    RNS.log("Firing "+E.Name,RNS.LOG_DEBUG)
    if not E.Callback:
      TextOut = E.Text
    else:
      EC = E.Callback()
      TextOut = EC.Text
      TelemetryOut = EC.Telemetry
    if isTest:
      TextOut = "***** THIS IS A TEST *****\n\n"+TextOut+"\n\n***** THIS IS A TEST *****"
    RNS.log(TextOut,RNS.LOG_EXTREME)
    for S in E.Subscribers:
      if not (isTest and E.Subscribers[S].RejectTests):
        out_hash = bytes.fromhex(E.Subscribers[S].Address)
        if not RNS.Transport.has_path(out_hash):
          RNS.log("Destination is not yet known. Requesting path and waiting for announce to arrive...")
          RNS.Transport.request_path(out_hash)
          while not RNS.Transport.has_path(out_hash):
            time.sleep(0.1)
        

        O = RNS.Identity.recall(out_hash)
        RNS.log(E.Subscribers[S].Address,RNS.LOG_DEBUG)
        RNS.log("Sending \""+TextOut+"\" to "+str(E.Subscribers[S].Address),RNS.LOG_VERBOSE)
        OD = RNS.Destination(O, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery")
        M = LXMF.LXMessage(OD,self.D,TextOut)
        if EC and EC.Telemetry:
          M.fields[LXMF.FIELD_TELEMETRY] = EC.Telemetry
        self.L.handle_outbound(M)
      
    while len(self.L.pending_outbound) > 0:
      RNS.log(str(len(self.L.pending_outbound))+" messages to send",RNS.LOG_DEBUG)
      time.sleep(0.5)
    RNS.log("Event "+str(Event)+" success.",RNS.LOG_DEBUG)
    
  def FireTestEvent(self,Event):
    self.FireEvent(Event,isTest = True)
    
  def EnumerateEvents(self):
    buffer="Served events, subscribers\n"
    for E in self.EventList:
      EE = self.EventList[E]
      buffer = buffer+(str(EE.Name)+": "+str(len(EE.Subscribers))+"\n")
    return buffer
    
  def AddSubscriber(self,Event,Sub):
    if Event not in self.EventList:
      RNS.log("Event "+str(Event)+" does not exist")
      return
    self.EventList[Event].AddSubscriber(Sub)


  