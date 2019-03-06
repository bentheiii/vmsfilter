import asyncio
import json
from datetime import datetime
import socket
import argparse
from time import time

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
    parser.add_argument('-l', required=False, type=float, dest='time_to_lose', default=None,
                        help='time to lose a path, in seconds (optional)')
    args = parser.parse_args()

    hostile_areas_path = args.hostile_areas
    habitat_area_path = args.habitat_areas
    ignore_areas_path = args.ignore_areas

    eyes_path = args.eyes_ws_path
    targeter_path = args.targeter_tcp_ip, args.targeter_tcp_port

    time_to_lose = args.time_to_lose

    path_store = PathStorage()
    path_store.load_areas(hostile_areas_path, habitat_area_path, ignore_areas_path)
    print(path_store.hostile_areas)
    print(path_store.ignore_areas)
    print(path_store.habitat_area)


    async def connect(path):
        while True:
            try:
                async with websockets.connect(path + "/vms/VmsStatus/SetSystemState", timeout=5) as ws:
                    print('connected to eyes')
                    index = 0
                    while ws:
                        message = await ws.recv()
                        index += 1
                        print(f"{datetime.now().time()}: from eyes msg_num: {index}")
                        data = json.loads(message)
                        moi = data.get('Moving Objects Info')
                        if not moi:
                            continue
                        objects = moi['Objects']
                        print(f"{datetime.now().time()}: got {len(objects)} new sightings!")
                        for obj in objects:
                            path_store.add_object(obj)

                        mark = data.get('VmsMatchingState', {}).get('VmsRegistrationMark')
                        if mark:
                            path_store.additional_info['VmsRegistrationMark'] = mark
            except (ConnectionRefusedError, TimeoutError, socket.timeout) as e:
                print(f'connection to eyes refused, retrying... error: {e!r}')
                await asyncio.sleep(2)
                continue
            except (ConnectionError, Exception) as e:
                print(f'connection to eyes closed unexpectedly, retrying... error: {e!r}')
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
                            got = False
                        else:
                            got = len(r) > 0

                        if got:
                            # definetly retarget
                            print('retargeting')
                            target = path_store.get_most_suspicious()
                            if not target:
                                cur_target_id = -1
                            else:
                                cur_target_id = target.id
                        else:
                            # maybe retarget
                            while True:
                                timeout_retarget = False
                                if time_to_lose is not None and cur_target_id != -1:
                                    data = path_store.data_for(cur_target_id)
                                    t = time()
                                    last_seen = data.get('time')
                                    if last_seen and (last_seen - t) > time_to_lose:
                                        timeout_retarget = True

                                if cur_target_id == -1 or timeout_retarget:
                                    t = path_store.get_most_suspicious()
                                    if t:
                                        cur_target_id = t.id
                                    else:
                                        break
                                else:
                                    break

                        data = path_store.data_for(cur_target_id)
                        d = {'id': cur_target_id, **data, **path_store.additional_info}
                        sock.send(bytes(json.dumps(d) + '\n', 'utf-8'))
                        await asyncio.sleep(0.15)
            except (ConnectionRefusedError, TimeoutError, socket.timeout):
                print('connection to targeter refused, retrying...')
                await asyncio.sleep(2)
                continue
            except (ConnectionError, Exception):
                print('connection to targeter closed unexpectedly, retrying...')
                await asyncio.sleep(2)
                continue


    asyncio.get_event_loop().run_until_complete(asyncio.gather(
        con(targeter_path),
        connect(eyes_path)
    ))
    asyncio.get_event_loop().run_forever()
