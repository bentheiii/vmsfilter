from enum import Enum
from threading import Lock

import gdal, ogr

from vmsfilter.bucket_dict import BucketDict


class SuspicionState(int, Enum):
    in_hostile = 2
    left_habitat = 1
    in_habitat = 0
    # currently not_suspect are just lowest priority instead of ignored, todo fix?
    not_suspect = -1


class Path:
    def __init__(self, id_):
        self.id: int = id_
        self.suspicion_state: SuspicionState = None


class PathStorage:
    def __init__(self):
        self.tracked_paths: BucketDict[int, Path, int] = BucketDict(lambda x: x.suspicion_state)
        self.blacklist = set()
        self.habitat_area = None
        self.ignore_areas = []
        self.hostile_areas = []
        self.tracked_lock = Lock()

    def _update_suspicion(self, path, point):
        changed = False

        if path.suspicion_state == SuspicionState.in_habitat:
            if not self.habitat_area.Contains(point):
                path.suspicion_state = SuspicionState.left_habitat
                changed = True

        if path.suspicion_state in (SuspicionState.in_habitat, SuspicionState.left_habitat):
            if any(ia.Contains(point) for ia in self.ignore_areas):
                path.suspicion_state = SuspicionState.not_suspect
                changed = True

        if changed:
            self.tracked_paths[path.id] = path

    def add_object(self, data):
        id = int(data["global_object_id"])
        with self.tracked_lock:
            if id in self.blacklist:
                return
            path: Path = self.tracked_paths.get(id)
            point = data["Location"]["VmsCoordinateFootprint"]["Center"]["VmsCoordinate"]
            x, y = float(point["x"]), float(point["y"])
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(x, y)

            if not path:
                path = Path(id)
                if any(ha.Contains(point) for ha in self.hostile_areas):
                    path.suspicion_state = SuspicionState.in_hostile
                elif self.habitat_area and self.habitat_area.Contains(point):
                    path.suspicion_state = SuspicionState.in_habitat
                else:
                    path.suspicion_state = SuspicionState.not_suspect

                self.tracked_paths[path.id] = path
            else:
                self._update_suspicion(path, point)

    def get_most_suspicious(self):
        with self.tracked_lock:
            ret = self.tracked_paths.highest()
            if ret:
                del self.tracked_paths[ret.id]
                self.blacklist.add(ret)
            return ret

    def load_areas(self, hostile_path, habitat_path, ignore_path):
        # load hostile
        if hostile_path:
            ds = gdal.OpenEx(hostile_path, gdal.OF_VECTOR | gdal.OF_READONLY)
            if not ds:
                raise Exception('could not open file for reading')
            layer = ds.GetLayer()
            self.hostile_areas.extend(p.GetGeometryRef().Clone() for p in layer)
            del ds, layer

        if habitat_path:
            ds = gdal.OpenEx(habitat_path, gdal.OF_VECTOR | gdal.OF_READONLY)
            if not ds:
                raise Exception('could not open file for reading')
            layer = ds.GetLayer()
            i = iter(layer)
            p = next(i, None)
            if (not p) or next(i, None):
                raise Exception('habitat file must have exactly one polygon')
            self.habitat_area = p.GetGeometryRef().Clone()
            del ds, layer, i, p

        if ignore_path:
            ds = gdal.OpenEx(ignore_path, gdal.OF_VECTOR | gdal.OF_READONLY)
            if not ds:
                raise Exception('could not open file for reading')
            layer = ds.GetLayer()
            self.ignore_areas.extend(p.GetGeometryRef().Clone() for p in layer)
            del ds, layer
