###### 
# LXMEvent Core Logic
#
# Defines classes and sends Reticlum messages
######

import os
import sys
import RNS
import LXMF
import time
import threading
import json
import LXMEventsBuiltIn as BuiltIn

###############
### WARNING ###
###############
# Pickle allows code injection
# Only import trusted event lists!
import pickle
###############

UseReticulumID = False # Use a NomadNet identity
UseCustomID = True # Use an LXMEvent specific identity

# An event itself. Contains both the metadata of the event and the subscriber list
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

# A record of a subscriber, containing both its address hash and opt-out for test messages
class Subscriber:
  def __init__(self, SubbedAddress):
    self.Address = SubbedAddress
    self.RejectTests = False
    
# The return of an event, currently a text string with some optional telemetry for testing.
class EventReturn:
  def __init__(self,TextPayload,Telemetry = None):
    self.Text = TextPayload
    self.Telemetry = Telemetry

# Event Handler class - Initialization logic and event container
class LXMEventHandler:
  def __init__(self, DisplayName):
    self.display_name = DisplayName
    self.R = RNS.Reticulum() # Initialize Reticlum
    self.userdir = os.path.expanduser("~")
    self.EventList = {}
    self.pending_lookups = []
    self.blacklist = []
    #self.EventList["BIT"] = LXMEvent("BIT","BIT is GO.") # Built in Test event

    if UseReticulumID: # Using NomadNet Identity
      self.configdir = self.userdir+"/.nomadnetwork" # Base directory for all stored files
      self.identitypath = self.configdir+"/storage/identity" # Identity file
      if os.path.exists(self.identitypath):
        self.ID = RNS.Identity.from_file(self.identitypath)
      else:
        sys.exit("NomadNet identity not found") # Program will not create a new NN identity
    elif UseCustomID: # Use LXMEvent specific identity
      self.configdir = self.userdir+"/.lxmevents" # Base directory for all stored files
      subpath = self.configdir+"/storage" 
      self.identitypath = self.configdir+"/storage/identity" # Identity file
      os.makedirs(subpath,exist_ok = True) # Failsafe to create paths if they don't exist. Recursive
      if os.path.exists(self.identitypath):
        self.ID = RNS.Identity.from_file(self.identitypath) # Load identity if exists
      else:
        self.ID = RNS.Identity() # Create new identity
        self.ID.to_file(self.identitypath) # Save newly created identity
        
    else:
      sys.exit("No valid identity configuration found.")
      
    self.eventdirectory = self.userdir+"/.lxmevents" # Events are always in this directory, even with NN identity
    if not os.path.exists(self.eventdirectory):
      os.makedirs(self.eventdirectory, exist_ok = True)
    self.triggerdirectory = self.eventdirectory+"/triggers" # Directory for triggers
    os.makedirs(self.triggerdirectory, exist_ok = True)
    #self.eventtemplatedirectory = self.eventdirectory+"/eventinjest" # Not implemented - injests new events
    #os.makedirs(self.eventrempldirectory, exist_ok = True)
    self.L = LXMF.LXMRouter(identity = self.ID, storagepath = self.eventdirectory) # Handles all LXMF routing
    self.D = self.L.register_delivery_identity(self.ID, display_name=self.display_name) # Local destination
    self.L.register_delivery_callback(self.ProcessIncoming) # Called when LXMRouter receives a message
    

# Sets the function to be called when an event is triggered
  def SetCallback(self, Target, CB):
    if Target not in self.EventList:
      RNS.log("Event "+str(Target)+" not in event list.")
      return
    self.EventList[Target].Callback = CB
    
# Check trigger directory, firing the callback for each

  ###
  # NOTE: This is a dangerous routine that assumes both the trigger name is safe and
  # the JSON is well-formed. It needs error checking for anything that allows user input
  ###
  
  def SweepTriggers(self):
    Triggers = os.listdir(self.triggerdirectory)
    for T in Triggers:
      #print(T)
      if os.path.isfile(self.triggerdirectory+"/"+T):
        if T in self.EventList:
          with open(self.triggerdirectory+"/"+T) as f:
            J = json.load(f)
          self.FireEvent(T, payload = J) # Fires event with JSON in the file as the payload
          print(T) # Debug logging that event has fired
          os.remove(self.triggerdirectory+"/"+T) # Removes trigger from directory
          
  # Called for every incoming LXM - Plaintext user input
  def ProcessIncoming(self,message):
    M = message.content.decode('utf-8')  # message.content is the body of an LXM
    H = RNS.hexrep(message.source_hash,delimit = False) # Sending address' hash
    if H in self.blacklist:
      return
    S = Subscriber(H)
    M = M.split(" ") # Separates the command/argument elements of an input
    if len(M) > 0:
      if M[0] == "STOP":
        if len(M)== 1:
          self.SendMessageSimple(S,None,"Requires a single event name to stop. Example: STOP WEATHER90210")
        elif len(M) > 1:
          if M[1] in self.EventList:
            self.RemoveSubscriber(M[1],S)
            #print("I should unsubscribe from "+M[1])
          else:
            self.SendMessageSimple(S,None,"Unknown event: "+M[1]+"\nPlease check your request. Input is case sensitive.")
      elif M[0] == "JOIN":
        if len(M)== 1:
          self.SendMessageSimple(S,None,"Requires a single event name to join. Example: JOIN WEATHER90210")
        elif len(M) > 1:
          if M[1] in self.EventList:
            self.AddSubscriber(M[1],S)
            #print("I should unsubscribe from "+M[1])
          else:
            self.SendMessageSimple(S,None,"Unknown event: "+M[1]+"\nPlease check your request. Input is case sensitive.")
      elif M[0] == "LIST":
        buffer = "Available Events:\n\n"
        for E in self.EventList:
          buffer = buffer + str(self.EventList[E].Name)+" - "+str(self.EventList[E].Description)+"\n\n"
        self.SendMessageSimple(S,None,buffer)
      elif M[0] == "BLACKLIST":
        #self.blacklist.append(H)
        self.BlackListAddress(S)
        print(self.blacklist)
        #print("I should blacklist this address.")
      else: # Informs the user of all available commands and format.
        self.SendMessageSimple(S,None,"Command not recognized. Commands are case sensitive.\nJOIN <EventName>\n  Receive notifications\nSTOP <Event Name>\n  Stop notifications\nBLACKLIST\n  Permanently stop all messages from this server\nLIST\n  List available events\n\nThis mailbox is unmonitored.")
    else:
      print("Error. No content in message. How did you even get here?") # If it's user input, it's error handled
    
    
  # Adds an event to the handler - does NOT overwrite existing events unless explicitly ordered
  def AddEvent(self, EventName, EventText = "This event has no configured text", EventCallback = None, Overwrite = False, Description = None):
    E = LXMEvent(EventName,EventText)
    if EventCallback:
      E.Callback = EventCallback
    if Description:
      E.Description = Description
    if EventName in self.EventList:
      RNS.log("Event "+str(EventName)+" already exists.")
      if Overwrite:
        RNS.log("Overwrite is set. Replacing.") 
        self.EventList[EventName] = E
      else:
        RNS.log("Overwrite not set. Rejecting.")
    else:
      self.EventList[EventName] = E
    
  # Called when event occurs
  def FireEvent(self,Event, isTest = False, payload = None):
    E = self.EventList[Event] # Probably needs error handling
    EC = None # Event Callback
    isSearching = False # True when message has not been sent
    RNS.log("Firing "+E.Name,RNS.LOG_DEBUG)
    if not E.Callback:
      TextOut = E.Text
    else:
      EC = E.Callback(payload)
      TextOut = EC.Text
      TelemetryOut = EC.Telemetry
    if isTest:
      TextOut = "***** THIS IS A TEST *****\n\n"+TextOut+"\n\n***** THIS IS A TEST *****"
    RNS.log(TextOut,RNS.LOG_EXTREME)
    for S in E.Subscribers:
      if not (isTest and E.Subscribers[S].RejectTests):
        isSearching = True
        # Do Stuff
        SendThread = threading.Thread(target = self.SendMessage, args=(S,E,TextOut,EC,))
        SendThread.start()
    while isSearching: # Idle until message is sent - This prevents the logic from conflating "ended" and "not yet started"
      if len(self.L.pending_outbound) > 0: 
        isSearching = False
      time.sleep(0.5)
    
    while len(self.pending_lookups) > 0: # If we're still looking up idenities, we're not done sending
      time.sleep(1)

    while len(self.L.pending_outbound) > 0: # If we still have messages to send, we're not done
      RNS.log(str(len(self.L.pending_outbound))+" messages to send",RNS.LOG_DEBUG)
      time.sleep(0.5)
      
    # No lookups pending, no messages pending, the event is done. We're not sure the success of each, but we're done.
    RNS.log("Event "+str(Event)+" success.",RNS.LOG_DEBUG)
    
  def Announce(self): # Convenience function
    self.D.announce()
    
    
  # Individual message sending logic, additonal control logic - Not currently used - Reference only
  # Sender, Event, Plain text message, unknown
  def SendMessage(self, S, E, TextOut, EC):
    if S in self.blacklist:
      return
    out_hash = bytes.fromhex(E.Subscribers[S].Address)
    if not RNS.Transport.has_path(out_hash): # If we don't know the identity, seek it
      RNS.log("Destination is not yet known. Requesting path and waiting for announce to arrive...",RNS.LOG_VERBOSE)
      RNS.Transport.request_path(out_hash)
      self.pending_lookups.append(S) # For timing
      LookupTime = time.time()
      # Time out in case path cannot be found
      while not RNS.Transport.has_path(out_hash):
        if (time.time()-LookupTime) > 30:
          RNS.log("Lookup for "+str(out_hash)+ "failed.")
          self.pending_lookups.remove(S)
          return
        time.sleep(0.1)
      self.pending_lookups.remove(S)
      
    # Now that we know we have the identity, we load it
    O = RNS.Identity.recall(out_hash)
    RNS.log(E.Subscribers[S].Address,RNS.LOG_DEBUG)
    RNS.log("Sending \""+TextOut+"\" to "+str(E.Subscribers[S].Address),RNS.LOG_VERBOSE)
    #Create output destination
    OD = RNS.Destination(O, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery")
    # Create message: Destination Out, Own Destination, plaintext message
    M = LXMF.LXMessage(OD,self.D,TextOut)
    # Set title of message (optional)
    M.set_title_from_string(E.Name)
    if EC and EC.Telemetry:
      M.fields[LXMF.FIELD_TELEMETRY] = EC.Telemetry # Debug attaching of field to message
    self.L.handle_outbound(M) # Queue message to be sent
      
    
  def FireTestEvent(self,Event):
    self.FireEvent(Event,isTest = True)
    
  def EnumerateEvents(self): # Shows subscription data
    buffer="Served events, subscribers\n"
    for E in self.EventList:
      EE = self.EventList[E]
      buffer = buffer+(str(EE.Name)+": "+str(len(EE.Subscribers))+"\n")
    return buffer
    
  def ListEvents(self): # Shows available events
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
    
  def BlackListAddress(self,Sub):
    for E in self.EventList:
      self.EventList[E].RemoveSubscriber(Sub)
    self.MessageBlacklist(None,Sub)
    self.blacklist.append(Sub.Address)
    self.SaveEvents()


  def MessageSubscription(self,Event,Sub):
    SubscribeMessage = "You have been subscribed to the "+Event+" list.\n\nMake sure to trust this source in Sideband to receive notifications.\n\nIf this is in error, your identity may be compromised, but you may send \"STOP "+Event+"\" to unsubscribe or \"BLACKLIST\" to permanently stop all messages to this address."
    SendThread = threading.Thread(target = self.SendMessageSimple, args=(Sub,Event,SubscribeMessage,))
    SendThread.start()

  def MessageUnsubscription(self,Event,Sub):
    Message = "You have been unsubscribed from the "+Event+" list."
    SendThread = threading.Thread(target = self.SendMessageSimple, args=(Sub,Event,Message,))
    SendThread.start()

  def MessageBlacklist(self,Event,Sub):
    Message = "Per your request, you will recive no further messages from this server."
    SendThread = threading.Thread(target = self.SendMessageSimple, args=(Sub,Event,Message,))
    SendThread.start()

  # Current, limited capability send function
  def SendMessageSimple(self,Sub,Event,Message):
    if Sub.Address in self.blacklist:
      return
    out_hash = bytes.fromhex(Sub.Address) # Target hash
    if not RNS.Transport.has_path(out_hash): # If we don't know the path/identiry, seek it
      RNS.Transport.request_path(out_hash) # Request path
      while not RNS.Transport.has_path(out_hash): # Idle here forever, needs error handling
        time.sleep(0.1)
    O = RNS.Identity.recall(out_hash) # Load known identiry
    # Destination out:
    OD = RNS.Destination(O, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery")
    M = LXMF.LXMessage(OD,self.D,Message) # Create LXM
    self.L.handle_outbound(M) # Queue message for transmission
    time.sleep(0.5) # Prevent premature thread termination. Needs a better way using a reciept


# Pickling events and blacklist to allow runtime changes to persist
  def SaveEvents(self,FileName = "eventlist"):
    pickle.dump(self.EventList,open(self.eventdirectory+"/"+FileName,"wb"))
    with open(self.eventdirectory+"/blacklist",'w') as f:
      json.dump(self.blacklist,f)
    
  def LoadEvents(self,FileName = "eventlist"):
    if not os.path.exists(self.eventdirectory+"/"+FileName):
      return False
    self.EventList = pickle.load(open(self.eventdirectory+"/"+FileName,"rb"))
    if os.path.exists(self.eventdirectory+"/blacklist"):
      with open(self.eventdirectory+"/blacklist") as f:
        self.blacklist = json.load(f)
    return True


  
