# Clash Royale Python private server

Early development experiment targeting the Clash Royale 1.9.2 Android client. The Python server handles the encrypted handshake, sends a prototype login and home-state packet, and responds to keepalives and avatar-stream requests. A test client has reached the home screen over a LAN.

**Current limitations:** This is a single-player prototype. Free chests give fixed rewards and have a four-hour cooldown; their rewards and cooldown persist locally. The Battle button starts an experimental trainer match simulated by the client, not an authoritative server simulation. Match results and progression are not persisted; multiplayer, multiple accounts, and most requests are not implemented. The example APK release contains a placeholder address and must be rebuilt for your server.

## Setup

Install Python dependencies with `python -m pip install -r requirements.txt`, then create a local server key with `python tools/generate_key.py`. Start the listener with `python server/test_server.py` (default TCP port 9339). Run the protocol test with `python -m unittest discover -s tests -v`.

To make a matching client, supply your own original 1.9.2 APK and run `python tools/patch_client.py original.apk build/patched-unsigned.apk YOUR_LAN_IP`. Sign the resulting APK with your own Android signing key before installing it. The patcher replaces the original hostname and public key; the client and server must use the same generated key pair. Keep `build/server-private.key` and your APK signing key private. The IP must fit within the original hostname's byte length.

## Credits and licensing

The home and avatar serialization follows [HashRoyale](https://github.com/qillasoft/HashRoyale), which is licensed under GPL-3.0-or-later; this source is distributed under the same license, in [LICENSE](LICENSE). Protocol investigation also used [cr-proxy](https://github.com/royale-proxy/cr-proxy) as a reference. Clash Royale and its assets are owned by Supercell. This independent project is not affiliated with Supercell; the source license does not grant rights to game assets.
