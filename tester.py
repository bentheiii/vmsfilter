import asyncio
import websockets

obj_uri = "ws://localhost/manual_set"
get_uri = "ws://localhost/get_target"

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


async def aget_id(expv=None):
    async with websockets.connect(get_uri) as websocket:
        await websocket.send(f'')
        ret = int(await websocket.recv())
    if expv is not None:
        if ret != expv:
            raise AssertionError(f"{ret} vs {expv}")


def get_id(expv=None):
    asyncio.run(aget_id(expv))


send_obj(0, hostile_point)
send_obj(1, habitat_point)

get_id(0)
get_id(1)

send_obj(2, habitat_point)
send_obj(3, habitat_point)
send_obj(4, habitat_point)
send_obj(2, outside_point)
send_obj(4, hostile_point)
send_obj(4, ignore_point)
send_obj(5, hostile_point)

get_id(5)
get_id(2)
get_id(3)
get_id(4)
