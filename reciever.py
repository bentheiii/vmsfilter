import asyncio
import json

import websockets

from vmsfilter.path_store import PathStorage

hostile_areas_path = r"D:\git\vmsfilter\resources\hostile.shp"
habitat_area_path = r"D:\git\vmsfilter\resources\habitat.shp"
ignore_areas_path = r"D:\git\vmsfilter\resources\ignore.shp"

if __name__ == '__main__':
    path_store = PathStorage()
    path_store.load_areas(hostile_areas_path, habitat_area_path, ignore_areas_path)
    print(path_store.hostile_areas)
    print(path_store.ignore_areas)
    print(path_store.habitat_area)


    async def echo(websocket, path):
        try:
            if path == "/vms/VmsStatus/SetSystemState":
                async for message in websocket:
                    data = json.loads(message)
                    objects = data['Moving Objects Info']['Objects']
                    for obj in objects:
                        path_store.add_object(obj)
            if path == "/manual_set":
                async for message in websocket:
                    id_, x, y = message.split()
                    obj = {
                        'global_object_id': id_,
                        'Location': {'VmsCoordinateFootprint': {'Center': {'VmsCoordinate': {'x': x, 'y': y}}}}
                    }
                    path_store.add_object(obj)
            if path == "/get_target":
                async for _ in websocket:
                    target = path_store.get_most_suspicious()
                    if not target:
                        tid = -1
                    else:
                        tid = target.id
                    await websocket.send(str(tid))
        except websockets.ConnectionClosed:
            pass


    asyncio.get_event_loop().run_until_complete(websockets.serve(echo, 'localhost', 80))
    asyncio.get_event_loop().run_forever()
