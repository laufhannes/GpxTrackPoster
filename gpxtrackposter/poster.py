# Copyright 2016-2018 Florian Pigorsch & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.

import svgwrite
from .value_range import ValueRange
from .xy import XY
from .year_range import YearRange


class Poster:
    def __init__(self):
        self.athlete = None
        self.title = "My Poster"
        self.tracks_by_date = {}
        self.tracks = []
        self.length_range = None
        self.length_range_by_date = None
        self.units = "metric"
        self.colors = {"background": "#222222", "text": "#FFFFFF", "special": "#FFFF00", "track": "#4DD2FF"}
        self.statistics = {"label": "Runs", "num": 0, "total": 0.0, "min": 6.0, "max": 9.0, "avg": 0.0}
        self.width = 200
        self.height = 300
        self.years = None
        self.tracks_drawer = None

    def set_tracks(self, tracks):
        self.tracks = tracks
        self.tracks_by_date = {}
        self.length_range = ValueRange()
        self.length_range_by_date = ValueRange()
        self.__compute_years(tracks)
        for track in tracks:
            if not self.years.contains(track.start_time):
                continue
            text_date = track.start_time.strftime("%Y-%m-%d")
            if text_date in self.tracks_by_date:
                self.tracks_by_date[text_date].append(track)
            else:
                self.tracks_by_date[text_date] = [track]
            self.length_range.extend(track.length)
        for tracks in self.tracks_by_date.values():
            length = sum([t.length for t in tracks])
            self.length_range_by_date.extend(length)

    def draw(self, drawer, output):
        self.tracks_drawer = drawer
        d = svgwrite.Drawing(output, ('{}mm'.format(self.width), '{}mm'.format(self.height)))
        d.viewbox(0, 0, self.width, self.height)
        d.add(d.rect((0, 0), (self.width, self.height), fill=self.colors['background']))
        self.__draw_header(d)
        self.__draw_footer(d)
        self.__draw_tracks(d, XY(self.width - 20, self.height - 30 - 30), XY(10, 30))
        d.save()

    def m2u(self, m):
        if self.units == "metric":
            return 0.001 * m
        else:
            return 0.001 * m / 1.609344

    def u(self):
        if self.units == "metric":
            return "km"
        else:
            return "mi"

    def __draw_tracks(self, d, size: XY, offset: XY):
        self.tracks_drawer.draw(d, size, offset)

    def __draw_header(self, d):
        if self.title:
            text_color = self.colors["text"]
            title_style = "font-size:12px; font-family:Arial;"
            d.add(d.text(self.title, insert=(10, 20), fill=text_color, style=title_style))
        d.add(d.image("img/runalyze.svg", insert=(105, 7.66), size=(95, 15)))

    def __draw_footer(self, d):
        text_color = self.colors["text"]
        header_style = "font-size:4px; font-family:Arial"
        value_style = "font-size:9px; font-family:Arial"
        small_value_style = "font-size:3px; font-family:Arial"

        (total_length, average_length, min_length, max_length, weeks) = self.__compute_track_statistics()

        d.add(d.text(self.athlete, insert=(22, self.height-10), fill=text_color, style=value_style))
        d.add(d.text("STATISTICS", insert=(100, self.height-20), fill=text_color, style=header_style))
        d.add(d.text("ACTIVITIES: {}".format(self.statistics['num']), insert=(100, self.height - 15), fill=text_color,
                     style=small_value_style))
        d.add(d.text("Weekly: {:.1f}".format(len(self.tracks) / weeks), insert=(100, self.height - 10), fill=text_color,
                     style=small_value_style))
        d.add(d.text("Total: {:.1f} {}".format(self.m2u(self.statistics['total']), self.u()), insert=(130, self.height-15),
                     fill=text_color, style=small_value_style))
        d.add(d.text("Avg: {:.1f} {}".format(self.m2u(average_length), self.u()), insert=(130, self.height-10),
                     fill=text_color, style=small_value_style))
        d.add(d.text("Min: {:.1f} {}".format(self.m2u(self.statistics['min']), self.u()), insert=(157, self.height-15),
                     fill=text_color, style=small_value_style))
        d.add(d.text("Max: {:.1f} {}".format(self.m2u(self.statistics['max']), self.u()), insert=(157, self.height-10),
                     fill=text_color, style=small_value_style))
        d.add(d.image("img/athlete.svg", insert=(3, self.height-26.7), size=(77,9.2448)))

    def __compute_track_statistics(self):
        length_range = ValueRange()
        total_length = 0
        weeks = {}
        for t in self.tracks:
            total_length += t.length
            length_range.extend(t.length)
            # time.isocalendar()[1] -> week number
            weeks[(t.start_time.year, t.start_time.isocalendar()[1])] = 1

        self.statistics['num'] = len(self.tracks) if self.statistics['num'] == 0 else self.statistics['num']
        self.statistics['total'] = total_length if self.statistics['total'] == 0 else self.statistics['total']
        self.statistics['min'] = length_range.lower() if self.statistics['min'] == 0.0 else self.statistics['min']
        self.statistics['max'] = length_range.upper() if self.statistics['max'] == 0.0 else self.statistics['max']
        #self.statistics['avg'] = total_length / len(self.tracks) if self.statistics['avg'] == 0 else self.statistics['avg']

        return total_length, total_length / len(self.tracks), length_range.lower(), length_range.upper(), len(weeks)

    def __compute_years(self, tracks):
        if self.years is not None:
            return
        self.years = YearRange()
        for t in tracks:
            self.years.add(t.start_time)
