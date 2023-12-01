#! /usr/bin/python3

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
  
  
# Utility Functions

def DisplayEventClass(EV):
  if not isAuthed or isBlacklisted:
    print(EV)
    print("  "+str(E.EventList[EV].Description)+"\n")
    return
  subbed = False
  if EV in E.EventList:
    if LXMF_Address and LXMF_Address in E.EventList[EV].Subscribers:
      subbed = True
  subcommand = "`[Subscribe`:/page/"+base_URL+"`Subscribe="+EV+"]"
  unsubcommand = "`[Unsubscribe`:/page/"+base_URL+"`Unsubscribe="+EV+"]"
  buffer = str(EV)+"\n`r "
  if(subbed):
    buffer = "`B040" + buffer + unsubcommand
  else:
    buffer = buffer + subcommand
  print(buffer)
  print("`a  "+str(E.EventList[EV].Description)+"\n`b\n")
    

# Graphical functions
def DemoDisclaimer():
  D = "`cThis is a demonstration of functionality.\nThere is no guarantee of suitability or stability.\nDo not use for life-saving activities\nwithout knowing and mitigating the risks.\n\n`a"
  return D

def MakeHeader():
  H = "--\n`cAlert System\n--\n`a"
  return H

def MakeBanner():
  B = """*********************
*Between the Borders*
*    Node Romeo     *
*   Alert System    *
*********************"""
  return B

def UnidentifiedBanner():
  B = "`B008`cYou are unidentified.\nYou must identify yourself to this system (in the Saved Nodes or Announce window) to change your status.\n`a`b"
  return B
  
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
for e in os.environ:
#  print(e+", "+os.environ[e])
  if e == "remote_identity":
    ID_hex = os.environ[e]
    isAuthed = True
    ID_bytes = bytes.fromhex(ID_hex)
    LXMF_Address_bytes = RNS.Destination.hash_from_name_and_identity("lxmf.delivery",ID_bytes)
    LXMF_Address = RNS.prettyhexrep(LXMF_Address_bytes)
    LXMF_Address = LXMF_Address.replace("<","")
    LXMF_Address = LXMF_Address.replace(">","")
  if e == "var_Subscribe":
#    print("I should be subscribing to "+os.environ[e]+" right now!")
     Sub_Me = os.environ[e]

  if e == "var_Unsubscribe":
#    print("I should be unsubscribing to "+os.environ[e]+" right now!")
     Unsub_Me = os.environ[e]

## Debug!
#isAuthed = True

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
