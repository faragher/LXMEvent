import os
import sys
import RNS
import LXMF
import time
import threading

###############
### WARNING ###
###############
# Pickle allows code injection
# Only import trusted event lists!
import pickle
###############

UseReticulumID = True

class LXMEvent:
  def __init__(self, EventName, EventText):
    self.Name = EventName
    self.Text = EventText
    self.Description = "No Description"
    self.Callback = None
    self.Subscribers = {}
  
  def toJSON(self):
    return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
  def __str__(self):
    return self.Name
    
  def AddSubscriber(self, Sub):
    if not Sub.Address:
      RNS.log("No subscriber address found")
      return
    self.Subscribers[Sub.Address] = Sub

  def RemoveSubscriber(self, Sub):
    if not Sub.Address:
      RNS.log("No subscriber address found")
      return
    self.Subscribers.pop(Sub.Address,None)


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
    self.pending_lookups = []
    self.blacklist = [] #NYI
    #self.last_lookup = None
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
      
    self.eventdirectory = self.userdir+"/.lxmevents"
    if not os.path.exists(self.eventdirectory):
      os.makedirs(self.eventdirectory, exist_ok = True)
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
    EC = None
    isSearching = False
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
        isSearching = True
        #Do Stuff
        #self.SendMessage(S,E,TextOut,EC)
        SendThread = threading.Thread(target = self.SendMessage, args=(S,E,TextOut,EC,))
        SendThread.start()
    while isSearching:
      if len(self.L.pending_outbound) > 0:
        isSearching = False
      time.sleep(0.5)
    
    while len(self.pending_lookups) > 0:
      time.sleep(1)

    while len(self.L.pending_outbound) > 0:
      RNS.log(str(len(self.L.pending_outbound))+" messages to send",RNS.LOG_DEBUG)
      time.sleep(0.5)
    RNS.log("Event "+str(Event)+" success.",RNS.LOG_DEBUG)
    
    
    
  def SendMessage(self, S, E, TextOut, EC):
    out_hash = bytes.fromhex(E.Subscribers[S].Address)
    if not RNS.Transport.has_path(out_hash):
      RNS.log("Destination is not yet known. Requesting path and waiting for announce to arrive...")
      RNS.Transport.request_path(out_hash)
      self.pending_lookups.append(S)
      LookupTime = time.time()
      while not RNS.Transport.has_path(out_hash):
        if (time.time()-LookupTime) > 30:
          RNS.log("Lookup for "+str(out_hash)+ "failed.")
          self.pending_lookups.remove(S)
          return
        time.sleep(0.1)
      self.pending_lookups.remove(S)
    O = RNS.Identity.recall(out_hash)
    RNS.log(E.Subscribers[S].Address,RNS.LOG_DEBUG)
    RNS.log("Sending \""+TextOut+"\" to "+str(E.Subscribers[S].Address),RNS.LOG_VERBOSE)
    OD = RNS.Destination(O, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery")
    M = LXMF.LXMessage(OD,self.D,TextOut)
    if EC and EC.Telemetry:
      M.fields[LXMF.FIELD_TELEMETRY] = EC.Telemetry
    self.L.handle_outbound(M)
      
    
  def FireTestEvent(self,Event):
    self.FireEvent(Event,isTest = True)
    
  def EnumerateEvents(self):
    buffer="Served events, subscribers\n"
    for E in self.EventList:
      EE = self.EventList[E]
      buffer = buffer+(str(EE.Name)+": "+str(len(EE.Subscribers))+"\n")
    return buffer
    
  def ListEvents(self):
    buffer = []
    for E in self.EventList:
      buffer.append(E)
    return buffer
    
  def AddSubscriber(self,Event,Sub):
    if Event not in self.EventList:
      RNS.log("Event "+str(Event)+" does not exist")
      return
    self.EventList[Event].AddSubscriber(Sub)
    self.SaveEvents()
    self.MessageSubscription(Event,Sub)

  def RemoveSubscriber(self,Event,Sub):
    if Event not in self.EventList:
      RNS.log("Event "+str(Event)+" does not exist")
      return
    self.EventList[Event].RemoveSubscriber(Sub)
    self.SaveEvents()
    self.MessageUnsubscription(Event,Sub)

  def MessageSubscription(self,Event,Sub):
    SubscribeMessage = "You have been subscribed to the "+Event+" list.\n\nMake sure to trust this source in Sideband to receive notifications.\n\nIf this is in error, your identity may be compromised, but you may send \"STOP "+Event+"\" to unsubscribe or \"BLACKLIST\" to permanently stop all messages to this address."
    SendThread = threading.Thread(target = self.SendMessageSimple, args=(Sub,Event,SubscribeMessage,))
    SendThread.start()

  def MessageUnsubscription(self,Event,Sub):
    Message = "You have been unsubscribed to the "+Event+" list."
    SendThread = threading.Thread(target = self.SendMessageSimple, args=(Sub,Event,Message,))
    SendThread.start()

  def MessageBlacklist(self,Event,Sub):
    Message = "Per your request, you will recive no further messages from this server."
    SendThread = threading.Thread(target = self.SendMessageSimple, args=(Sub,Event,Message,))
    SendThread.start()

  def SendMessageSimple(self,Sub,Event,Message):
    out_hash = bytes.fromhex(Sub.Address)
#    SubscribeMessage = "You have been subscribed to the "+Event+" list.\n\nIf this is in error, your identity may be compromised, but you may send \"STOP "+Event+"\" to unsubscribe or \"BLACKLIST\" to permanently stop all messages to this address."
    if not RNS.Transport.has_path(out_hash):
#      RNS.log("Destination is not yet known. Requesting path and waiting for announce to arrive...")
      RNS.Transport.request_path(out_hash)
      while not RNS.Transport.has_path(out_hash):
        time.sleep(0.1)
    O = RNS.Identity.recall(out_hash)
    OD = RNS.Destination(O, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery")
    M = LXMF.LXMessage(OD,self.D,Message)
    self.L.handle_outbound(M)
    time.sleep(0.5)


  def SaveEvents(self,FileName = "eventlist"):
    #P = umsgpack.packb(self.EventList)
    #P = json.dumps(self.EventList)
    #for L in self.EventList:
    #  print(self.EventList[L].toJSON())
    #print(P)
    pickle.dump(self.EventList,open(self.eventdirectory+"/"+FileName,"wb"))
    
  def LoadEvents(self,FileName = "eventlist"):
    if not os.path.exists(self.eventdirectory+"/"+FileName):
      return False
    self.EventList = pickle.load(open(self.eventdirectory+"/"+FileName,"rb"))
    return True


  
