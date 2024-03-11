<!-- ABOUT THE PROJECT -->
## About Honeypwned

[![Product Name Screen Shot][product-screenshot]](https://example.com)

Honeypwned is designed to counter the vulnerabilities and misuse of Virtual Private Networks (VPNs). 
As VPNs have gained popularity for enhancing online security and privacy, they've also been utilized by malicious actors to conceal their identities. 
Positioned strategically within the DMZ, Honeypwned operates as a honeypot, luring in these threat actors with enticing files. 
Once engaged, Honeypwned exposes their true identities, effectively mitigating cybersecurity risks

<!-- GETTING STARTED -->
## Getting Started

This is an example of how you can set up your project locally.
Download a local copy up and follow these steps below.

### Prerequisites

* Linux OS

### Usage and Setting up

_Below is how you can start honeypwned._

1. Download the repo as a zip
2. Extract the files
3. Open config.ini to change the ports you want to open for the honeypot(make sure port 80 and 8888 are open)
4. Save the config file
5. Run the honeypot(make sure to run as root)
   ```python
   sudo python3 honeypwned.py
   ```
6. Listen to any traffic interacting with ports that you set open
