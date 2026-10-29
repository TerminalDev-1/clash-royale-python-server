import asyncio
import hashlib
import secrets
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import test_server as server
from nacl.public import PrivateKey, Box
from nacl.secret import SecretBox

class HandshakeTest(unittest.IsolatedAsyncioTestCase):
    async def test_login_exchange(self):
        listener = await asyncio.start_server(server.handle, '127.0.0.1', 0)
        port = listener.sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        async def receive():
            h = await reader.readexactly(7)
            return int.from_bytes(h[:2], 'big'), await reader.readexactly(int.from_bytes(h[2:5], 'big'))
        try:
            writer.write(server.frame(10100, b''))
            await writer.drain()
            mid, hello = await receive()
            self.assertEqual(mid, 20100)
            self.assertEqual(int.from_bytes(hello[:4], 'big'), 24)
            token = hello[4:]
            client = PrivateKey.generate()
            client_key = bytes(client.public_key)
            box = Box(client, server.PRIVATE_KEY.public_key)
            snonce = secrets.token_bytes(24)
            nonce = hashlib.blake2b(client_key + server.PUBLIC_KEY, digest_size=24).digest()
            login = client_key + box.encrypt(token + snonce + b'login', nonce).ciphertext
            writer.write(server.frame(10101, login))
            await writer.drain()
            mid, response = await receive()
            self.assertEqual(mid, 20104)
            nonce = hashlib.blake2b(snonce + client_key + server.PUBLIC_KEY, digest_size=24).digest()
            decoded = box.decrypt(response, nonce)
            self.assertIn(b'local-private-server', decoded[56:])
            rnonce, key = decoded[:24], decoded[24:56]
            mid, response = await receive()
            self.assertEqual(mid, 24101)
            next_nonce = (int.from_bytes(rnonce, 'little') + 2).to_bytes(24, 'little')
            self.assertGreater(len(SecretBox(key).decrypt(response, next_nonce)), 300)
        finally:
            writer.close()
            await writer.wait_closed()
            listener.close()
            await listener.wait_closed()

if __name__ == '__main__':
    unittest.main()
