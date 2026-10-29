# Clash Royale Python private server

Early development experiment targeting the Clash Royale 1.9.2 Android client. The Python server handles the encrypted handshake, sends a prototype login and home-state packet, and responds to keepalives and avatar-stream requests. A test client has reached the home screen over a LAN.

**Current limitations:** Home and account data are fixed prototype values. Battles, progression, persistent accounts, chests, and most requests are not implemented. The first APK release is configured for the author's LAN address and server key; it is a development snapshot, not a plug-and-play client for other servers.

## Setup

Install Python dependencies with `python -m pip install -r requirements.txt`, then create a local server key with `python tools/generate_key.py`. Start the listener with `python server/test_server.py` (default TCP port 9339). Run the protocol test with `python -m unittest discover -s tests -v`.

To make a matching client, supply your own original 1.9.2 APK and run `python tools/patch_client.py original.apk build/patched-unsigned.apk YOUR_LAN_IP`. Sign the resulting APK with your own Android signing key before installing it. The patcher replaces the original hostname and public key; the client and server must use the same generated key pair. Keep `build/server-private.key` and your APK signing key private. The IP must fit within the original hostname's byte length.

## Credits and licensing

The home and avatar serialization follows [HashRoyale](https://github.com/qillasoft/HashRoyale), which is licensed under GPL-3.0-or-later; this source is distributed under the same license, in [LICENSE](LICENSE). Protocol investigation also used [cr-proxy](https://github.com/royale-proxy/cr-proxy) as a reference. Clash Royale and its assets are owned by Supercell. This independent project is not affiliated with Supercell; the source license does not grant rights to game assets.
