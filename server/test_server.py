"""Clash Royale 1.9.2 experimental login server."""
import argparse
import asyncio
import hashlib
import logging
import secrets
import struct
from pathlib import Path
from nacl.public import PrivateKey, PublicKey, Box
from nacl.exceptions import CryptoError
from nacl.secret import SecretBox
from home import login_ok, own_home

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
PRIVATE_KEY = PrivateKey((Path(__file__).resolve().parent.parent / 'build/server-private.key').read_bytes())
PUBLIC_KEY = bytes(PRIVATE_KEY.public_key)

def frame(mid, payload, version=0):
    return mid.to_bytes(2, 'big') + len(payload).to_bytes(3, 'big') + version.to_bytes(2, 'big') + payload

def sc_string(value):
    if value is None:
        return struct.pack('>i', -1)
    data = value.encode('utf-8')
    return struct.pack('>i', len(data)) + data

class Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def take(self, count):
        if count < 0 or self.pos + count > len(self.data):
            raise ValueError('Truncated login packet')
        value = self.data[self.pos:self.pos + count]
        self.pos += count
        return value

    def integer(self):
        return int.from_bytes(self.take(4), 'big', signed=True)

    def string(self):
        size = self.integer()
        if size == -1:
            return None
        if size < 0 or size > 900000:
            raise ValueError('Invalid string length')
        return self.take(size).decode('utf-8')

    def vint(self):
        byte = self.take(1)[0]
        sign, value, shift = byte & 0x40, byte & 0x3f, 6
        while byte & 0x80:
            if shift > 27:
                raise ValueError('Invalid VInt')
            byte = self.take(1)[0]
            value |= (byte & 0x7f) << shift
            shift += 7
        return value - (1 << shift) if sign else value

async def handle(reader, writer):
    peer = writer.get_extra_info('peername')
    logging.info('Connected: %s', peer)
    token = secrets.token_bytes(24)
    session = None
    try:
        while True:
            header = await reader.readexactly(7)
            mid = int.from_bytes(header[:2], 'big')
            length = int.from_bytes(header[2:5], 'big')
            if length > 1048576:
                raise ValueError('Packet too large')
            payload = await reader.readexactly(length)
            logging.info('Received message %d, length %d', mid, length)
            if mid == 10100:
                writer.write(frame(20100, struct.pack('>i', len(token)) + token))
                await writer.drain()
                logging.info('Sent ServerHello 20100')
            elif mid == 10101:
                client_key = payload[:32]
                box = Box(PRIVATE_KEY, PublicKey(client_key))
                nonce = hashlib.blake2b(client_key + PUBLIC_KEY, digest_size=24).digest()
                plain = box.decrypt(payload[32:], nonce)
                if plain[:24] != token:
                    raise ValueError('Login session token mismatch')
                logging.info('Login decrypted successfully; application payload length %d', len(plain) - 48)
                login = Reader(plain[48:])
                if len(plain) - 48 >= 12:
                    login.take(8)  # account id
                    login.string()  # account token; never log credentials
                    version = (login.vint(), login.vint(), login.vint())
                    logging.info('Client login version: %s.%s.%s', *version)
                snonce = plain[24:48]
                rnonce, session_key = secrets.token_bytes(24), secrets.token_bytes(32)
                nonce = hashlib.blake2b(snonce + client_key + PUBLIC_KEY, digest_size=24).digest()
                encrypted = box.encrypt(rnonce + session_key + login_ok('local-private-server'), nonce).ciphertext
                writer.write(frame(20104, encrypted, 1))
                outgoing_nonce = (int.from_bytes(rnonce, 'little') + 2).to_bytes(24, 'little')
                writer.write(frame(24101, SecretBox(session_key).encrypt(own_home(), outgoing_nonce).ciphertext))
                session = {'box': SecretBox(session_key), 'incoming': int.from_bytes(snonce, 'little'), 'outgoing': int.from_bytes(outgoing_nonce, 'little')}
                await writer.drain()
                logging.info('Sent LoginOk 20104 and experimental OwnHomeData 24101')
            else:
                if session is None:
                    raise ValueError('Message before login')
                session['incoming'] += 2
                decoded = session['box'].decrypt(payload, session['incoming'].to_bytes(24, 'little'))
                logging.info('Decrypted message %d, application length %d', mid, len(decoded))
                if mid in (10108, 14405):
                    response_id = 20108 if mid == 10108 else 24411
                    response = b'' if mid == 10108 else b'\x00'
                    session['outgoing'] += 2
                    encrypted = session['box'].encrypt(response, session['outgoing'].to_bytes(24, 'little')).ciphertext
                    writer.write(frame(response_id, encrypted))
                    await writer.drain()
                    logging.info('Sent message %d', response_id)
    except (asyncio.IncompleteReadError, ConnectionError):
        logging.info('Disconnected: %s', peer)
    except (CryptoError, ValueError, IndexError) as exc:
        logging.warning('Protocol error from %s: %s', peer, exc)
    finally:
        writer.close()
        await writer.wait_closed()

async def main(port):
    server = await asyncio.start_server(handle, '0.0.0.0', port)
    logging.info('Listening on %s', server.sockets[0].getsockname())
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9339)
    asyncio.run(main(parser.parse_args().port))
