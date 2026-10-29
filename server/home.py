import struct
import time

# Protocol layout follows HashRoyale's 1.9.2 LogicClientHome/Avatar encoders.
def vint(value):
    if not -(1 << 31) <= value < (1 << 31):
        raise ValueError('VInt outside signed 32-bit range')
    flipped = value ^ (value >> 31)
    first = ((value >> 25) & 0x40) | (value & 0x3f)
    value >>= 6
    flipped >>= 6
    result = bytearray([first | (0x80 if flipped else 0)])
    while flipped:
        flipped >>= 7
        result.append((value & 0x7f) | (0x80 if flipped else 0))
        value >>= 7
    return bytes(result)

def string(value):
    if value is None:
        return b'\xff\xff\xff\xff'
    data = value.encode('utf8')
    return struct.pack('>i', len(data)) + data

class Writer:
    def __init__(self): self.data = bytearray()
    def v(self, *values):
        for value in values: self.data.extend(vint(value))
    def s(self, value): self.data.extend(string(value))
    def b(self, value): self.data.append(value)
    def long(self, value): self.data.extend(struct.pack('>q', value))

# Stable local account for the first playable prototype.
def login_ok(token):
    w = Writer()
    w.long(1); w.long(1); w.s(token); w.s(''); w.s('')
    w.v(3, 377, 3); w.s('prod'); w.v(0, 0, 0)
    for s in ('', '', ''): w.s(s)
    w.v(0)
    for s in ('G:1', '', 'GB', '', '', '', ''): w.s(s)
    return bytes(w.data)

def chest_reward():
    w = Writer()
    w.v(210, 1); w.b(0)  # server command, format version, non-draft
    w.v(1)  # one card stack
    w.v(1, 0, 0, 3, 0, 0, 0)  # three copies of card 1
    w.v(0, 50, 2, 1, 2, 2, -1, -1, 0, 0)
    return bytes(w.data)

def own_home(state=None):
    state = state or {'gold': 1000, 'gems': 100, 'card_count': 0, 'next_chest': 0}
    w = Writer(); now = int(time.time())
    available = state['next_chest'] <= now
    w.long(1); w.v(0, 0 if available else 1, 0, 0, 1500268361); w.b(0)
    w.v(5)
    for _ in range(5):
        w.v(8)
        for i in range(8): w.v(26000000+i)
    w.b(255)
    for i in range(8): w.v(i+1, 0, 0, state['card_count'] if i == 0 else 0, 0, 0, 0)
    w.v(0, 0)
    w.v(0, 0, -1, 33, now, 1, 0)
    w.v(1, 1109); w.s('2v2 Button'); w.v(8, now, 1609462800, now, 0, 0, 0, 0, 0, 0, 0, 0)
    w.s('2v2 Button'); w.s('{"HideTimer":false,"HidePopupTimer":false}"')
    w.v(0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1, 1109, 2, 2)
    w.s('{"ID":"CARD_RELEASE","Params":{}})'); w.v(4); w.s('{"ID":"CLAN_CHEST","Params":{}}')
    w.v(4, 0, max(0, state['next_chest'] - now)*20, 0, 0, 0, 0, 0); w.b(0)
    w.v(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 1714640, 1726960, now, 0, 0, 0, -1, 3)
    w.v(*([0]*7), 2, 1)
    w.v(54, 1) # current arena: Goblin Stadium
    w.v(1, 1, 1, 10000, 10000, now, 0, 0) # empty shop
    w.v(*([0]*9), 1,0,1,0,1,0,1,0,0,0,0,23,0,0,0,0)
    w.data.extend(struct.pack('>h', -2041))
    w.v(1,1,0,0,0,11,0, 2,0,0,4,3,17,1, 14,0,0,5,4,14,1, 74,0,0,5,4,1,1, 73,0,0,1,0,5,0, 4,0,0,1,0,9,0, 15,0,now,1,1,6,2, 16,0,now,1,1,6,2, 0, 2,26,46,28,16, 0,0,0,0,0,0,1,now,0,0,0,1,54000001, *([0]*10),7)
    # LogicClientAvatar
    w.v(0,1,0,1,0,1); w.s('Player'); w.b(1)
    w.v(2,0,0,0,100,0,0,0,0,0,100,100,50,1,0,0,8,10)
    w.v(5,0,0, 5,1,state['gold'], 5,3,2, 5,4,0, 5,5,state['gold'], 5,13,0, 5,14,0, 5,16,51, 5,28,0, 5,29,72000006)
    w.v(0,0,0,6, 5,6,30, 5,7,0, 5,8,8, 5,1,26000048, 5,11,32, 5,27,1)
    w.v(0,0,0,state['gems'],state['gems'],0,1,0,7, 0,0,0,0,0,0,7, 0,0,0,0,0,0,now,0,0)
    return bytes(w.data)
