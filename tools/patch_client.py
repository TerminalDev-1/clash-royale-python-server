"""Patch the original client endpoint while preserving native library sizes."""
import argparse
from pathlib import Path
import zipfile
from nacl.public import PrivateKey

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("host")
args = parser.parse_args()
public_key = bytes(PrivateKey(Path('build/server-private.key').read_bytes()).public_key)
original_key = bytes.fromhex('ac30dcbea27e213407519bc05be8e9d930e63f873858479946c144895fa3a26b')
old = b"game.clashroyaleapp.com"
new = args.host.encode("ascii")
if len(new) > len(old) or not new:
    parser.error("host must fit in the existing hostname")
with zipfile.ZipFile(args.source) as src, zipfile.ZipFile(args.output, "w") as dst:
    for info in src.infolist():
        if info.filename.upper().startswith("META-INF/"):
            continue
        data = src.read(info.filename)
        if info.filename in ("lib/armeabi-v7a/libg.so", "lib/x86/libg.so"):
            if data.count(old) != 1:
                raise ValueError(f"Unexpected hostname count in {info.filename}")
            data = data.replace(old, new.ljust(len(old), b"\0"))
            if data.count(original_key) != 1:
                raise ValueError(f"Unexpected public key count in {info.filename}")
            data = data.replace(original_key, public_key)
            print("Patched", info.filename)
        dst.writestr(info, data)
