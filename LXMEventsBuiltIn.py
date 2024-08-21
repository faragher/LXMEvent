
def BIT():
  print("GO")
  
  
# Demonstration event: A new GitHub release - See Collect.py
def GitHubRelease(J):
  R = "There's been a new release at the "+str(J["event"])+" repository: "+str(J["name"])
  return Events.EventReturn(R)