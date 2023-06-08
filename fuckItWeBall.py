import math
from sailbot.eventUtils import Waypoint, has_reached_waypoint, EventFinished
from sailbot.GPS import gps

class bad_search():
    def __init__(self):
        self.search_center = Waypoint(ENTER, ENTER)
        self.search_radius = 100
        self.gps = gps.gps()
        self.pattern = self.create_search_pattern()

    def next_gps(self):
        if has_reached_waypoint(self.pattern[0]):
            self.pattern.pop(0)
            if len(self.pattern) == 0:
                return EventFinished
            return self.pattern[0]

    def create_search_pattern(self):
        pattern = []

        d_lat = self.gps.latitude - self.search_center.lat
        d_lon = self.gps.longitude - self.search_center.lon
        ang = math.atan(d_lon / d_lat)
        ang *= 180 / math.pi

        if (d_lat < 0): ang += 180

        tar_angs = [ang, ang + 72, ang - 72, ang - (72 * 3), ang - (72 * 2)]
        for i in range(0, 5):
            pattern.append(
                Waypoint(lat=self.search_center.lat + self.search_radius * math.cos(tar_angs[i] * (math.pi / 180)),
                         lon=self.search_center.lon + self.search_radius * math.sin(tar_angs[i] * (math.pi / 180)))
            )

        return pattern
