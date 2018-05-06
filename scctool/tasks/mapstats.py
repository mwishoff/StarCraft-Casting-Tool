"""Manager and thread to save map stats and keep them up-to-date."""
import json
import logging
import time

from PyQt5.QtCore import pyqtSignal

import scctool.settings
from scctool.tasks.liquipedia import LiquipediaGrabber, MapNotFound
from scctool.tasks.tasksthread import TasksThread

module_logger = logging.getLogger('scctool.tasks.mapstats')


class MapStatsManager:

    def __init__(self, controller):
        self.__controller = controller
        self.loadJson()
        self.__thread = MapStatsThread(self)
        self.__thread.newMapData.connect(self._newData)
        self.__thread.newMapPool.connect(self._newMapPool)
        self.refreshMapPool()
        self.refreshMaps()

    def _getMaps(self):
        return self.__maps.keys()

    def loadJson(self):
        """Read json data from file."""
        try:
            with open(scctool.settings.getJsonFile('mapstats'),
                      'r',
                      encoding='utf-8-sig') as json_file:
                data = json.load(json_file)
        except Exception as e:
            data = dict()

        self.__maps = data.get('maps', dict())
        self.__customMapPool = data.get('custom_mappool', list())
        self.__ladderMapPool = data.get('ladder_mappool', list())
        self.__mappool_refresh = int(data.get('mappool_refresh', 0))
        self.__mappool = int(data.get('mappool', 0))

        if not isinstance(self.__maps, dict):
            self.__maps = dict()
        if not isinstance(self.__customMapPool, list):
            self.__customMapPool = list()
        if not isinstance(self.__ladderMapPool, list):
            self.__ladderMapPool = list()

    def dumpJson(self):
        """Write json data to file."""
        data = dict()
        data['maps'] = self.__maps
        data['custom_mappool'] = self.__customMapPool
        data['ladder_mappool'] = self.__ladderMapPool
        data['mappool'] = self.__mappool
        data['mappool_refresh'] = self.__mappool_refresh

        try:
            with open(scctool.settings.getJsonFile('mapstats'),
                      'w',
                      encoding='utf-8-sig') as outfile:
                json.dump(data, outfile)
        except Exception as e:
            module_logger.exception("message")

    def setMapPoolType(self, id):
        self.__mappool = int(id)

    def getMapPoolType(self):
        return int(self.__mappool)

    def getCustomMapPool(self):
        if len(self.__customMapPool) == 0:
            for map in self.getLadderMapPool():
                yield map
        else:
            for map in self.__customMapPool:
                yield map

    def getLadderMapPool(self):
        for map in self.__ladderMapPool:
            yield map

    def setCustomMapPool(self, maps):
        self.__customMapPool = list(maps)

    def getMapPool(self):
        if self.__mappool == 0:
            for map in self.getLadderMapPool():
                yield map
        elif self.__mappool == 1:
            for map in self.getCustomMapPool():
                yield map
        else:
            for map in self.__controller.matchData.yieldMaps():
                yield map

    def refreshMapPool(self):
        if (not self.__mappool_refresh or
                (time.time() - int(self.__mappool_refresh)) > 24 * 60 * 60):
            self.__thread.activateTask('refresh_mappool')

    def refreshMaps(self):
        for map in scctool.settings.maps:
            if map != 'TBD' and map not in self.__maps.keys():
                self.__maps[map] = dict()
                self.__maps[map]['tvz'] = None
                self.__maps[map]['zvp'] = None
                self.__maps[map]['pvt'] = None
                self.__maps[map]['creator'] = None
                self.__maps[map]['size'] = None
                self.__maps[map]['spawn-positions'] = None
                self.__maps[map]['refreshed'] = None

        maps2refresh = list()
        maps2refresh_full = list()

        for map, data in self.__maps.items():
            is_none = False
            for key in ['creator', 'size', 'spawn-positions']:
                if data.get(key, None) is None:
                    maps2refresh_full.append(map)
                    is_none = True
                    break
            if is_none:
                continue
            last_refresh = data.get('refreshed', None)
            if (not last_refresh or
                    (time.time() - int(last_refresh)) > 24 * 60 * 60):
                maps2refresh.append(map)

        if len(maps2refresh) > 0:
            self.__thread.setMaps(maps2refresh)
            self.__thread.activateTask('refresh_stats')

        if len(maps2refresh_full) > 0:
            self.__thread.setMaps(maps2refresh_full, True)
            self.__thread.activateTask('refresh_data')

    def _newData(self, map, data):
        for key, item in data.items():
            self.__maps[map][key] = item

    def _newMapPool(self, data):
        if len(data) > 0:
            self.__ladderMapPool = data
            self.__mappool_refresh = int(time.time())

    def close(self, save=True):
        self.__thread.terminate()
        if save:
            self.dumpJson()

    def getData(self):
        out_data = dict()
        for map, data in self.__maps.items():
            if map not in self.getMapPool():
                continue
            out_data[map] = dict()
            out_data[map]['map-name'] = map
            for key, item in data.items():
                if key == 'refreshed':
                    continue
                if not item:
                    item = "?"
                key = key.replace('spawn-positions', 'positions')
                out_data[map][key] = item

        return out_data
        
    def sendMapPool(self):
        data = self.getData()
        self.__controller.websocketThread.sendData2Path('mapstats', "MAPSTATS", data)


class MapStatsThread(TasksThread):

    newMapData = pyqtSignal(str, object)
    newMapPool = pyqtSignal(object)

    def __init__(self, manager):
        super().__init__()
        self.__manager = manager
        self.__grabber = LiquipediaGrabber()
        self.setTimeout(30)
        self.addTask('refresh_data', self.__refresh_data)
        self.addTask('refresh_stats', self.__refresh_stats)
        self.addTask('refresh_mappool', self.__refresh_mappool)

    def setMaps(self, maps, full=False):
        if full:
            self.__fullmaps = maps
        else:
            self.__maps = maps

    def __refresh_data(self):
        try:
            map = self.__fullmaps.pop()
            try:
                liquipediaMap = self.__grabber.get_map(map)
                stats = liquipediaMap.get_stats()
                info = liquipediaMap.get_info()
                data = dict()
                data['tvz'] = stats['tvz']
                data['zvp'] = stats['zvp']
                data['pvt'] = stats['pvt']
                data['creator'] = info['creator']
                data['size'] = info['size']
                data['spawn-positions'] = info['spawn-positions']
                data['refreshed'] = int(time.time())
                self.newMapData.emit(map, data)
                module_logger.info('Map {} found.'.format(map))
            except MapNotFound:
                module_logger.info('Map {} not found.'.format(map))
            except ConnectionError:
                module_logger.info('Connection Error for map {}.'.format(map))
            except Exception as e:
                module_logger.exception("message")
        except IndexError:
            self.deactivateTask('refresh_data')

    def __refresh_stats(self):
        try:
            for stats in self.__grabber.get_map_stats(self.__maps):
                map = stats['map']
                data = dict()
                data['tvz'] = stats['tvz']
                data['zvp'] = stats['zvp']
                data['pvt'] = stats['pvt']
                data['refreshed'] = int(time.time())
                module_logger.info('Map {} found.'.format(map))
                self.newMapData.emit(map, data)
        finally:
            self.deactivateTask('refresh_stats')

    def __refresh_mappool(self):
        try:
            mappool = list(self.__grabber.get_ladder_mappool())
            self.newMapPool.emit(mappool)
            module_logger.info('Current map pool found.')
        finally:
            self.deactivateTask('refresh_mappool')