import logging
import math
import time
import matplotlib.pyplot as plt


import sailbot.constants as c
from sailbot.eventUtils import Event, EventFinished, Waypoint, distance_between, has_reached_waypoint
from camera import Camera
from GPS import gps
# from sailbot.transceiver import arduino

"""
# Challenge	Goal:
    - To demonstrate the boat’s ability to autonomously locate an object
    
    # Description:
        - An orange buoy will be placed somewhere within 100 m of a reference position
        - The boat must locate, touch, and signal* such within 10 minutes of entering the search area
        - RC is not allowed after entering the search area
        - 'Signal' means white strobe on boat and/or signal to a shore station and either turn into wind or assume station-keeping mode
    
    # Scoring:
        - 15 pts max
        - 12 pts for touching (w/o signal)
        - 9 pts for passing within 1m
        - 6 pts for performing a search pattern (creeping line, expanding square, direct tracking to buoy, etc)
    
    # Assumptions: (based on guidelines)
        - 
        
    # Strategy:
        - Define a Z-shaped search pattern
        - Travel along the search path while taking panoramas to detect buoys
        
            - If x% buoy detected AND its estimated position is within search bounds:
                - Add to heatmap (combines detections that are near each other for greater accuracy)
                    
            - If heatmap has a high confidence point of interest:
                - Bookmark current position and divert course towards buoy
                - Focus camera on expected buoy position and take pictures
                
                - If that buoy is still a buoy:
                    - Keep moving towards the buoy and ram that shit
                    - Signal that boat touched the buoy when it stops getting closer
                        - NOTE: Use accelerometer instead?
                - Else:
                    - False positive (hopefully VERY rare)! PANIC! Return to previous search course
                    - Blacklist location (NOT IMPLEMENTED)
"""

REQUIRED_ARGS = 2


class Search(Event):
    """
    Attributes:
        - search_center (Waypoint): the center of the search bounds
        - search_radius (float): the radius of the search bounds
        - event_duration (int): the length of the event in seconds
        - start_time (float): the start time of the event (seconds since 1970)

        - state (str): the search event state
            - Either 'SEARCHING', 'TRACKING', or 'RAMMING' the buoy
    """

    def __init__(self, event_info=[Waypoint(0, 0), 100]):
        """
        Args:
            event_info (list[Waypoint(center_lat, center_long), radius]): center and radius of search circle
        """
        if len(event_info) != REQUIRED_ARGS:
            raise TypeError(f"Expected {REQUIRED_ARGS} arguments, got {len(event_info)}")
        super().__init__(event_info)
        logging.info("Search moment")

        # EVENT INFO
        self.search_center = event_info[0]
        self.search_radius = event_info[1]
        self.event_duration = 600
        self.start_time = time.time()
        self.event_started = False

        # BOAT STATE
        self.waypoint_queue = self.create_search_pattern()

        # Boat is either SEARCHING, TRACKING or RAMMING a buoy
        self.state = "SEARCHING"

        # Used to pool together nearby detections for higher accuracy
        self.heatmap = Heatmap(chunk_radius=float(c.config["SEARCH"]["heatmap_chunk_radius"]))
        self.best_chunk = None
        self.divert_confidence_threshold = float(c.config["SEARCH"]["pooled_heatmap_confidence_threshold"])

        # Buffers for buoys that are near the edge of the search radius to account for gps estimation error
        self.search_bounds = self.search_radius + float(c.config["SEARCH"]["search_radius_tolerance"])

        # When to give up on a buoy if its no longer detected
        self.missed_consecutive_detections = 0
        self.tracking_abandon_threshold = int(c.config["SEARCH"]["tracking_abandon_threshold"])

        # When to switch from tracking to ramming mode and when to signal that the boat hit a buoy
        self.ramming_distance = int(c.config["SEARCH"]["ramming_distance"])
        self.collision_sensitivity = float(c.config["SEARCH"]["collision_sensitivity"])

        # SENSORS
        self.camera = Camera()
        self.gps = gps()
        # self.transceiver = arduino(c.config['MAIN']['ardu_port']) TODO: unbug

    def next_gps(self):
        """
        Main event script logic. Executed continuously by boatMain.
        
        Returns either:
            - Waypoint object: The next GPS point that the boat should sail to
            - EventFinished Exception: signals that the event has been completed
        """

        # Either no buoys found yet or boat is gathering more confidence before diverting course
        if not self.event_started:
            if has_reached_waypoint(self.search_center, distance=self.search_radius):
                logging.info("Search event started!")
                self.start_time = time.time()
                self.waypoint_queue.pop(0)
                self.state = "SEARCHING"
            else:
                return self.waypoint_queue[0]

        if self.state == "SEARCHING":
            # Capture panorama of surroundings
            imgs = self.camera.survey(num_images=3, context=True, detect=True)

            # Error check detections & add to heatmap
            detections = 0
            for frame in imgs:
                for detection in frame.detections:
                    distance_from_center = distance_between(self.search_center, detection.gps)

                    if distance_from_center > self.search_bounds:
                        logging.info(f"SEARCHING: Dropped buoy at: {detection.gps}, {distance_from_center}m from center")
                        continue

                    logging.info(f"SEARCHING: Buoy ({detection.conf}%) found at: {detection.gps}")
                    self.heatmap.append(detection)
                    detections += 1

            if detections == 0:
                # No detections, continue along preset search path
                logging.info("SEARCHING: No buoys spotted! Continuing along search path")
                if has_reached_waypoint(self.waypoint_queue[0], distance=2):
                    self.waypoint_queue.pop(0)
                return self.waypoint_queue[0]
            else:
                # Detection! Check if boat is confident enough to move to the buoy
                self.best_chunk = self.heatmap.get_highest_confidence_chunk()

                if self.best_chunk.sum_confidence > self.divert_confidence_threshold:
                    logging.info(f"""SEARCHING: This bitch definitely a buoy! 
                            Bookmarking position and moving towards buoy at {self.best_chunk.average_gps}.""")
                    self.state = "TRACKING"
                    self.waypoint_queue.insert(0, self.gps)
                    self.waypoint_queue.insert(0, self.best_chunk.average_gps)
                    return self.waypoint_queue[0]

        # A buoy is found and boat is heading towards it
        elif self.state == "TRACKING":
            distance_to_buoy = distance_between(self.gps, self.waypoint_queue[0])

            if distance_to_buoy < self.ramming_distance:
                # Boat is near the buoy, TIME TO RAM THAT SHIT
                logging.info(f"TRACKING: {distance_to_buoy}m away from buoy! RAMMING TIME")
                self.state = "RAMMING"
            else:
                # Boat is still far away from buoy
                logging.info(f"TRACKING: {distance_to_buoy}m away from buoy! Closing in!")
                try:
                    self.camera.focus(self.waypoint_queue[0])
                except RuntimeError as e:
                    logging.warning(f"""TRACKING: Exception raised: {e}\n
                    Camera can't focus on target! Going towards last know position!""")
                    return self.waypoint_queue[0]

                frame = self.camera.capture(context=True, detect=True)

                # Abandon if boat can't find buoy multiple times in a row (hopefully VERY rare)
                if len(frame.detections) == 0:
                    logging.info("TRACKING: Lost buoy")
                    self.missed_consecutive_detections += 1

                    if self.missed_consecutive_detections == self.tracking_abandon_threshold:
                        logging.warning("TRACKING: Can't find buoy! Abandoning course and returning to search")
                        self.missed_consecutive_detections = 0
                        # self.heatmap.blacklist(self.waypoint_queue[0])
                        self.state = "SEARCHING"
                else:
                    self.missed_consecutive_detections = 0

                    for detection in frame.detections:
                        distance_from_center = distance_between(self.search_center, detection.gps)

                        if distance_from_center > self.search_bounds:
                            logging.info(f"TRACKING: Dropped buoy at: {detection.gps}, {distance_from_center}m from center")
                            continue

                        logging.info(f"TRACKING: Buoy found at: {detection.gps}")
                        self.heatmap.append(detection)

                    logging.info(f"TRACKING: Continuing course to buoy at: {self.best_chunk.average_gps}")
                    self.waypoint_queue[0] = self.best_chunk.average_gps
                    return self.waypoint_queue[0]

        # Boat is very close to the buoy
        elif self.state == "RAMMING":
            # TODO: GPS is only so accurate. Use accelerometer instead!
            distance_to_buoy = distance_between(self.gps, self.waypoint_queue[0])

            if distance_to_buoy < self.collision_sensitivity:
                logging.info(f"Sailbot touched the buoy! Search event finished!")
                self.transceiver.send("Sailbot touched the buoy!")
                raise EventFinished

        # Times up... fuck it and assume that we touched the buoy
        if time.time() - self.start_time > self.event_duration:
            logging.info(f"Sailbot totally touched the buoy... Search event finished!")
            self.transceiver.send("Sailbot touched the buoy!")
            raise EventFinished

    def create_search_pattern(self, num_points=None):
        """
        Generates a zig-zag search pattern to maximimize area coverage
        Args:
            - num_points (int): how many GPS points to generate (minimum is 2 for a straight line)
                - More points means tighter search lines. Higher success chance but more distance to cover.
                - Default is automatically determined by object detections max detection distance
        Returns:
            - list[Waypoint(lat, long), ...] gps coordinates of the search pattern
        """
        # TODO: Make variable number of points based on distance
        # Metrics used to fine-tune optimal coverage
        # TODO: Use windvane to determine rotation

        if num_points is None:
            max_detection_distance = c.config["SEARCH"]["max_detection_distance"]
            num_points = (2 * self.search_radius) / max_detection_distance

        if num_points < 2:
            raise RuntimeError(f"Invalid number of points {num_points} for create_search_pattern()")

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

        total_distance = 0
        for i in range(len(pattern) - 1):
            total_distance += distance_between(pattern[i], pattern[i+1])
        logging.info(f"Created {num_points}-point search path. Total distance to cover is {total_distance}m")

        return pattern


class Heatmap:
    """Datastructure which splits the search radius into X-meter circular 'chunks'
        - Each detection has its confidence pooled with all others inside the same chunk
            - Decrease chunk radius if two separate buoys are being grouped as one
            - Increase chunk radius if the same buoy is creating multiple chunks (caused by GPS estimation error)
        - NOTE: Chunks can overlap which may cause problems (if so, then extend code to use tri/square/hex chunks instead of circles)

        Attributes:
            - chunks (list[HeatmapChunk])
            - chunk_radius (float)
    """

    def __init__(self, chunk_radius):
        self.chunks = []
        self.chunk_radius = chunk_radius

    def __contains__(self, detection):
        """
        Checks if a detection is inside any of the heatmap's chunks' boundary
            - Invoke using the 'in' keyword ex. 'if detection in heatmap'
        """
        for chunk in self.chunks:
            if detection in chunk:
                return True
        return False

    def append(self, detection):
        for chunk in self.chunks:
            if detection in chunk:
                chunk.append(detection)
        else:
            self.chunks.append(HeatmapChunk(radius=self.chunk_radius,
                                            detection=detection))

    def get_highest_confidence_chunk(self):
        return max(self.chunks, key=lambda heatmap_chunk: heatmap_chunk.sum_confidence)


class HeatmapChunk:
    """
    A circular boundary which combines nearby detections for better accuracy
        - Detections within the chunk's radius are assumed to be from the same buoy and averaged

    Attributes:
        - radius (float): the radial size of the chunk
        - average_gps (Waypoint): the average point between all detections within a chunk
        - detection_count (int): the number of detections within a chunk
        - sum_confidence (float): the combined total of all detections within the chunk
    """

    def __init__(self, radius, detection):
        self.radius = radius
        self.average_gps = detection.gps
        self.detection_count = 1
        self.sum_confidence = detection.conf

        self._sum_lat = detection.gps.latitude
        self._sum_lon = detection.gps.longitude

    def __contains__(self, detection):
        return distance_between(self.average_gps, detection.gps) <= self.radius

    def append(self, detection):
        self.detection_count += 1

        self._sum_lat += detection.gps.latitude
        self._sum_lon += detection.gps.longitude
        self.average_gps = Waypoint(self._sum_lat / self.detection_count, self._sum_lon / self.detection_count)

        self.sum_confidence += detection.conf
