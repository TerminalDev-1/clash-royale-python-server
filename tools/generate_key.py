"""Create the local key pair used by the server and APK patcher."""
from pathlib import Path
from nacl.public import PrivateKey

path = Path(__file__).resolve().parent.parent / 'build' / 'server-private.key'
path.parent.mkdir(parents=True, exist_ok=True)
if path.exists():
    print(f'Keeping existing key: {path}')
else:
    path.write_bytes(bytes(PrivateKey.generate()))
    print(f'Created key: {path}')
print('Client public key:', bytes(PrivateKey(path.read_bytes()).public_key).hex())
