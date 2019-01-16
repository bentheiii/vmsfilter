import asyncio
import websockets


async def send(uri):
    async with websockets.connect(uri) as websocket:
        while websocket:
            await websocket.send('please')
            print("waiting")
            reply = await websocket.recv()
            print("got")
            print(reply)


asyncio.get_event_loop().run_until_complete(
    send('ws://localhost/gettarget'))
