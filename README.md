# dc32-ics-ais
Resources for the AIS SDR workshop at the DEF CON 32 ICS village.

# Instructions
Here are some brief instructions to get you going. Please ask if you have any questions.

## WARNING
TRANSMITTING MALICIOUS AIS TRAFFIC OVER THE AIR IS VERY ILLEGAL AND AUTHORITIES WILL BE VERY UPSET WITH YOU. PLEASE USE A WIRED CONNECTION FOR TESTING OR LOWER THE GAIN TO THE MINIMUM VIABLE SETTING IF YOU MUST USE AN ANTENNA (`./ais-simulator/ais-simulator.py:57`).

## Preamble
To begin, initiatilize the `ais-simulator` submodule:

```git submodule update --init --recursive```

Then, download the AIS utilities:

```./download_garys_tools.sh```

To receive a copy of the neccessary `apate.pl` script, please ask one of the presenters, as we are not distributing this file on GitHub currently.

## SDR Setup
The relevant GNURadio code has been tested with Ubuntu 20.04 and Fedora 6.5.12. We strongly recommend Ubuntu 20.04, as this is the distro the `ais-simulator` repository has troubleshooting documentation for.

Navigate to `./ais-simulator/README.md` and follow the initial instructions to install dependencies. Next, navigate to `./ais-simulator/gr-ais_simulator/README.md` and follow the instructions to build the GNURadio AIS blocks. Please refer to troubleshooting steps in the README, and ask for help if stuck.

Now, run the `ais-simulator.py` script as described in the README to initialize the SDR WebSocket server. You can navigate to the `webapp/ais-simulator.html` page to craft messages for transmission.

## AIS Setup
Go ahead and install OpenCPN to plot AIS traffic from a receiver: `https://www.opencpn.org/OpenCPN/info/quickstart.html`

After downloading the AIS tooling, read the instructions and skim through the scripts themselves to get a feel for how they operate. Then, run `apate.pl` and follow the necessary dialog prompts. This will generate your `DATA_replay.txt` file, which we will transmit.

## Transmission
First, run `pip install -r requirements.txt` to get the required Python libraries installed.

Now that you have a `DATA_replay.txt` file, go ahead and run `dispatch_apate.py` (providing the replay file as an argument). This will connect to the running `ais-simulator.py` server and transmit the AIS messages over your SDR. Observe the logs and check to see if you (or your lab partner) are able to receive the transmitted messages. Don't hesitate to reach out for help if you're running into issues on this step.

# TODO
- Examples directory for `apate.pl` output
- Link to VirtualBox image
