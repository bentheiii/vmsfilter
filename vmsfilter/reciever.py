import asyncio
import json
from datetime import datetime
import socket
import argparse

import websockets

from vmsfilter.path_store import PathStorage

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='hostile_areas', help='path for vector file with hostile areas polygons',
                        required=True)
    parser.add_argument('-b', dest='habitat_areas', help='path for vector file with habitat areas polygons',
                        required=True)
    parser.add_argument('-g', dest='ignore_areas', help='path for vector file with ignore areas polygons',
                        required=True)
    parser.add_argument('-e', dest='eyes_ws_path', help='websocket path to the eyes server (without the /vms/... path)',
                        required=True)
    parser.add_argument('-t', dest='targeter_tcp_ip', help='tcp ip of the targeter server', required=True)
    parser.add_argument('-p', dest='targeter_tcp_port', type=int, help='tcp port of the targeter server', required=True)
    args = parser.parse_args()

    hostile_areas_path = args.hostile_areas  # r"D:\git\vmsfilter\resources\hostile.shp"
    habitat_area_path = args.habitat_areas  # r"D:\git\vmsfilter\resources\habitat.shp"
    ignore_areas_path = args.ignore_areas  # r"D:\git\vmsfilter\resources\ignore.shp"

    eyes_path = args.eyes_ws_path  # "ws://192.168.20.102:7225"  # ws path
    targeter_path = args.targeter_tcp_ip, args.targeter_tcp_port  # ('192.168.20.104', 11235)  # TCP path

    path_store = PathStorage()
    path_store.load_areas(hostile_areas_path, habitat_area_path, ignore_areas_path)
    print(path_store.hostile_areas)
    print(path_store.ignore_areas)
    print(path_store.habitat_area)


    async def connect(path):
        while True:
            try:
                async with websockets.connect(path + "/vms/VmsStatus/SetSystemState") as ws:
                    while ws:
                        print('connected to eyes')
                        message = await ws.recv()
                        data = json.loads(message)
                        moi = data.get('Moving Objects Info')
                        if not moi:
                            continue
                        objects = moi['Objects']
                        print(f"{datetime.now().time()}: got {len(objects)} new sightings!")
                        for obj in objects:
                            path_store.add_object(obj)
            except (ConnectionRefusedError, TimeoutError, socket.timeout):
                print('connection to eyes refused, retrying...')
                await asyncio.sleep(2)
                continue
            except ConnectionError:
                print('connection to eyes closed unexpectedly, retrying...')
                await asyncio.sleep(2)
                continue


    async def con(path):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    # Connect to server and send data
                    sock.settimeout(5)
                    sock.connect(path)
                    sock.settimeout(0.1)
                    print('connected to targeter')
                    cur_target_id = -1
                    while True:
                        try:
                            r = sock.recv(1024)
                        except (socket.timeout, BlockingIOError):
                            if cur_target_id == -1:
                                t = path_store.get_most_suspicious()
                                if t:
                                    cur_target_id = t.id
                            loc = path_store.location_for(cur_target_id)
                            if loc:
                                x, y = loc
                            else:
                                x = y = 'null'
                            d = {'id': cur_target_id, 'x': x, 'y': y}
                            sock.send(bytes(json.dumps(d) + '\n', 'utf-8'))
                        else:
                            print('retargeting')
                            target = path_store.get_most_suspicious()
                            if not target:
                                cur_target_id = -1
                            else:
                                cur_target_id = target.id
                        await asyncio.sleep(0.15)
            except (ConnectionRefusedError, TimeoutError, socket.timeout):
                print('connection to targeter refused, retrying...')
                await asyncio.sleep(2)
                continue
            except ConnectionError:
                print('connection to targeter closed unexpectedly, retrying...')
                await asyncio.sleep(2)
                continue


    asyncio.get_event_loop().run_until_complete(asyncio.gather(
        con(targeter_path),
        connect(eyes_path)
    ))
    asyncio.get_event_loop().run_forever()
