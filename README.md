# LXMEvent
[Bleeding Edge] LXM mass messaging system/mailing list

This is not finalized or really ready, but is reasonably feeature complete for testing.

Commenting, documentation, and API creation in progress.

This creates a distribution list for event-trigged announcements. Better documentation later

## Setup:

This is the demo implementation:

```
E = Events.LXMEventHandler("Testbed Handler")
GH = Events.BuiltIn.GitHubRelease

print("Initializing")
E.AddEvent("RNodeFirmware",EventCallback = GH,Description = "Updates to the RNode Firmware")
E.AddEvent("LXMF",EventCallback = GH, Description = "LXMF Router Updates")
E.AddEvent("RNS",EventCallback = GH, Description = "New verions of the Reticulum Network Stack")
E.AddEvent("NomadNet",EventCallback = GH, Description = "Nomad Network Updates")
E.AddEvent("Sideband",EventCallback = GH, Description = "Updates to the Sideband client")
E.SaveEvents()
print("Initialization complete. Standing by.")

while True:
  time.sleep(360)
  E.Announce()
  E.LoadEvents()
  E.SweepTriggers()
```

The handler is initialized with a name and will either use an identity found in ~/.lxmevent/idendity or create a new one. Events are added using AddEvent(Name) with Description describing the mailing list, EventCallback defining a callback, and Text being the text sent if no EventCallback is defined.

Callbacks receive the JSON contents of the trigger file.

## Triggers:

Any file placed in .lxmevent/triggers will be read, its JSON contents, if any, sent to the callback, if any, and then deleted. A file name must match the event to be fired or it will be ignored.

## Callbacks:

Callbacks are arbitrary, recieve a JSON object and return an EventReturn, which contains a string to be sent as a message. There is currently a default GitHub callback internally, with more to be added as utility is found, but the contents of the callback are arbitrary so long as it returns an EventReturn with a message string.

## Messages:

The string in the event or the callback's return will be sent to the subscribers on the list. The list name is sent as the message title, and it is possible to pass telemetry in the EventReturn, but if none is provided it will be ignored.

## Signing up:

It's possible to programatically add users using a Subscriber object, which currently contains its hash address and a boolean to ignore test messages. However, the primary intention is to use either the NomadNet interface or the Sideband commands to sign up/unsubscribe from messages. The NomadNet page needs to have any custom callbacks defined, even if they're dummied out (it's a pickle requirement) and, of course, receiving LXMFs requires announces.

The NomadNet interface requires the user to be identified to sign up to increase security and prevent spam or griefing.

## Blacklisting:

While there should be no way to be signed up against your will, the system allows users to blacklist themselves, permanently disabling their ability to receive messages from the server. This can only be undone by manually removing their hash from the blacklist file.
