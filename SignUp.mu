#! /usr/bin/python3

#####
Micron page for Nomad Network etc. to handle subscriptions

#####


###############
### WARNING ###
###############
# Pickle allows code injection
# Only use trusted event handlers!
###############

import Events
import os
import RNS




# You must define your callbacks or the pickling will fail
# They can, however, be dummied out

#def TestCallback():
#  pass
  
  
##### Utility Functions


## Display an event class
def DisplayEventClass(EV):
  # If the user is not authtenticated or is blacklisted, display the event data and retutn
  if not isAuthed or isBlacklisted:
    print(EV)
    print("  "+str(E.EventList[EV].Description)+"\n")
    return
  subbed = False
  # If the user is in the list of subscibers, they are subscribed.
  if EV in E.EventList:
    if LXMF_Address and LXMF_Address in E.EventList[EV].Subscribers:
      subbed = True
  # Define links to subscribe/unsubscribe pages
  subcommand = "`[Subscribe`:/page/"+base_URL+"`Subscribe="+EV+"]"
  unsubcommand = "`[Unsubscribe`:/page/"+base_URL+"`Unsubscribe="+EV+"]"
  buffer = str(EV)+"\n`r "
  if(subbed):
    buffer = "`B040" + buffer + unsubcommand
  else:
    buffer = buffer + subcommand
    
  # Finish generating output
  print(buffer)
  print("`a  "+str(E.EventList[EV].Description)+"\n`b\n")
    

# Graphical functions
def DemoDisclaimer():
  D = "`cThis is a demonstration of functionality.\nThere is no guarantee of suitability or stability.\nDo not use for life-saving activities\nwithout knowing and mitigating the risks.\n\n`a"
  return D


## Defines the page header
def MakeHeader():
  H = "--\n`cAlert System\n--\n`a"
  return H

## Defines page banner
def MakeBanner():
  B = """*********************
*Between the Borders*
*    Node Romeo     *
*   Alert System    *
*********************"""
  return B

## Displays on page if link is not identified, and thus is not authenticated
def UnidentifiedBanner():
  B = "`B008`cYou are unidentified.\nYou must identify yourself to this system (in the Saved Nodes or Announce window) to change your status.\n`a`b"
  return B
  
## Displays if user has requested to be blacklisted by this server
def BlacklistBanner():
  B = "`B400`cYou have asked to be blacklisted from this server and will never receive messages from it. There is no automated way to reverse this. Please contact the sysop for options.\n`a`b
  return B

base_URL = "SignUp.mu"
useBanner = True
isDemo = True

# Collect environment / POST equivalent data
isAuthed = False
LXMF_Address = None
LXMF_Address_bytes = None
ID_hex = None
ID_bytes = None
Sub_Me = None
Unsub_Me = None
isBlacklisted = False

# Runs through environemnt variables where NN stores the equivalent of POST data
for e in os.environ:
#  print(e+", "+os.environ[e])
  if e == "remote_identity":
    ID_hex = os.environ[e]
    isAuthed = True
    ID_bytes = bytes.fromhex(ID_hex)
    LXMF_Address_bytes = RNS.Destination.hash_from_name_and_identity("lxmf.delivery",ID_bytes)
    # This makes a string of the hex address and removes the <>. Could just be hexrep to avoid replacement
    LXMF_Address = RNS.prettyhexrep(LXMF_Address_bytes)
    LXMF_Address = LXMF_Address.replace("<","")
    LXMF_Address = LXMF_Address.replace(">","")
  if e == "var_Subscribe":
#    print("I should be subscribing to "+os.environ[e]+" right now!")
     Sub_Me = os.environ[e]

  if e == "var_Unsubscribe":
#    print("I should be unsubscribing to "+os.environ[e]+" right now!")
     Unsub_Me = os.environ[e]

## Debug! - Forces the page to run as if the user was authenticated.
## THIS WILL BREAK ALL INTERACTIONS THAT USE AN ADDRESS
#isAuthed = True


##### The Micron page collects from the program output. This generates
##### the page itself. The logic should be self explanatory


print(MakeHeader())
if isDemo:
  print(DemoDisclaimer())
if useBanner:
  print(MakeBanner())
if not isAuthed:
  print(UnidentifiedBanner())

E = Events.LXMEventHandler("Testbed Handler")
E.LoadEvents()
if LXMF_Address in E.blacklist:
  isBlacklisted = True
if isBlacklisted:
  print(BlacklistBanner())
if Sub_Me:
  if LXMF_Address:
    S = Events.Subscriber(LXMF_Address)
    E.AddSubscriber(Sub_Me,S)
if Unsub_Me:
  if LXMF_Address:
    S = Events.Subscriber(LXMF_Address)
    E.RemoveSubscriber(Unsub_Me,S)



print("`c`B008Available event lists\n`b`a\n")
for Ev in E.ListEvents():
  DisplayEventClass(Ev)
