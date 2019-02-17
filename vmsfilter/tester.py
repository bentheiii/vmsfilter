import asyncio
import json

import websockets

root = 'ws://192.168.20.100:11235'

obj_uri = root + "/manual_set"
get_uri = root + "/get_target"
loc_uri = root + "/get_location"

hostile_point = 35.16658, 31.80048
habitat_point = 35.16642, 31.80048
ignore_point = 35.16631, 31.79989
outside_point = 35.16360, 31.79991


async def asend_obj(id, x, y):
    async with websockets.connect(obj_uri) as websocket:
        await websocket.send(f'{id} {x} {y}')


def send_obj(id, point):
    x, y = point
    asyncio.run(asend_obj(id, x, y))


async def aget_id(expv):
    async with websockets.connect(get_uri) as websocket:
        await websocket.send(f'')
        ret = int(await websocket.recv())
    if expv is not None:
        if ret != expv:
            raise AssertionError(f"{ret} vs {expv}")
    return ret


async def aget_loc(id, eloc):
    async with websockets.connect(loc_uri) as websocket:
        await websocket.send(str(id))
        ret = json.loads(await websocket.recv())
    if eloc is not None:
        x, y = ret
        ex, ey = eloc
        if x != ex or y != ey:
            raise AssertionError(f"{ret} vs {eloc}")
    return ret


def get_id(expv=None, eloc=None):
    id = asyncio.run(aget_id(expv))
    asyncio.run(aget_loc(id, eloc))


send_obj(0, hostile_point)
send_obj(1, habitat_point)

get_id(0, hostile_point)
get_id(1, habitat_point)

send_obj(2, habitat_point)
send_obj(3, habitat_point)
send_obj(4, habitat_point)
send_obj(2, outside_point)
send_obj(4, hostile_point)
send_obj(4, ignore_point)
send_obj(5, hostile_point)

get_id(5, hostile_point)
get_id(2, outside_point)
get_id(3, habitat_point)
get_id(4, ignore_point)
get_id(-1, None)
