from shapely.geometry import box, MultiPoint, Point, Polygon, LinearRing, LineString
import numpy as np
import cv2

class Boundingbox(object):

    def __init__(self, x = 10, y=10, points = []):

        if len(points) > 0:
            self.box = MultiPoint(points)
        else:
            self.box = MultiPoint([Point(x-50,y-50), Point(x+50,y-50), Point(x+50,y+50), Point(x-50,y+50)])

    def add_vertex(self,idx, x,y):
        coords = list(self.box.geoms)
        coords.insert(idx+1,(x,y))
        self.box = MultiPoint(coords)

    def remove_vertex(self, idx):
        coords = list(self.box.geoms)
        if len(coords) > 3:
        #Avoid turning the polygon into a line without area.
            coords.pop(idx)
            self.box = MultiPoint(coords)

    def get_vertecies(self):
        return [[coord.x, coord.y] for coord in list(self.box.geoms)]

    def update_vertex(self, idx, x, y):
        new_coords = list(self.box.geoms)
        new_coords[idx] = (x, y)
        self.box = MultiPoint(new_coords)

    def update_closest_vertex(self,x,y):
        distances = [Point(x,y).distance(vertex) for vertex in self.box.geoms]
        pt = distances.index(min(distances))
        self.update_vertex(pt, x, y)

    def closest_vertex(self, x, y):
        distances = [Point(x, y).distance(vertex) for vertex in self.box.geoms]
        pt = distances.index(min(distances))
        return pt

    def closest_point(self, x, y):
        point = Point(x,y)
        poly_ext = LinearRing(self.box.geoms)
        distance = poly_ext.project(point)
        return poly_ext.interpolate(distance)

    def update_position(self, dx, dy):
        coords = list(self.box.geoms)
        new_coords = []
        for coord in coords:
            new_coords.append((coord.x + dx, coord.y + dy))
        self.box = MultiPoint(new_coords)


    def segment(self, x, y):
        #Returns the coordinates of the vertex preceeding the point(x,y)
        #It is assumed that (x,y) lies on the border of self.box
        point = Point(x,y).buffer(0.000001)
        lines = LineString(self.box.geoms)
        for i in range(len(lines.coords)-1):
            subline = LineString(lines.coords[i:i+2])
            if subline.intersects(point):
                return i
        return len(lines.coords) - 1

    def overlay_box_scaled(self, image,
                           scale = 1.0,
                           color = (0,255,255),
                           draw_vertecies=False,
                           selected_vertex = None):
        box_coords = [(p.x, p.y) for p in list(self.box.geoms)]
        pts = np.array(box_coords, np.int32)
        pts = np.int32(scale*pts).reshape((-1, 1, 2))

        #cv2.polylines(image, [pts], True, color)
        #background = np.zeros((image.shape),dtype=np.uint8)
        image = cv2.fillPoly(image, [pts], color)
        # image = cv2.addWeighted(image, 0.8, background, 0.2, 0)

        if draw_vertecies:
            for coords in box_coords:
                coords = tuple(scale*c for c in coords)
                cv2.rectangle(image,
                              (int(coords[0]) - 2,int(coords[1])-2),
                              (int(coords[0]) + 2, int(coords[1]) + 2),
                              (255,0,0))
            if not selected_vertex is None:
                coords = box_coords[selected_vertex]
                coords = tuple(scale * c for c in coords)
                cv2.rectangle(image,
                              (int(coords[0]) - 2, int(coords[1]) - 2),
                              (int(coords[0]) + 2, int(coords[1]) + 2),
                              (255, 255, 0))

        return image

    def overlay_label_scaled(self, image, text, scale = 1.0, color = (0,255,255), margin = (0, 5), font_size=1.0):
        text_box = (int((self.box.bounds[0] + margin[0]) * scale), int((self.box.bounds[1] - margin[1]) * scale))
        font_face = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = scale/2
        thickness = 2  # cv2.FILLED
        margin = 2

        txt_size = cv2.getTextSize(text, font_face, font_scale, thickness)

        cv2.putText(image, text, text_box, font_face, font_size*font_scale, color, 1, cv2.LINE_AA)
        return image


    def overlay_box(self, image, color = (0,255,255), draw_vertecies=False, selected_vertex = None, width=1):
        box_coords = [(p.x, p.y) for p in list(self.box.geoms)]
        pts = np.array(box_coords, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(image, [pts], True, color, width)
        if draw_vertecies:
            for coords in box_coords:
                cv2.rectangle(image,
                              (int(coords[0]) - 2,int(coords[1])-2),
                              (int(coords[0]) + 2, int(coords[1]) + 2),
                              (255,0,0))
            if not selected_vertex is None:
                coords = box_coords[selected_vertex]
                cv2.rectangle(image,
                              (int(coords[0]) - 2, int(coords[1]) - 2),
                              (int(coords[0]) + 2, int(coords[1]) + 2),
                              (255, 255, 0))

        return image

    def contains_point(self, x, y):
        point = Point(x, y)
        if Polygon(self.box.geoms).contains(point):
            return True
        else:
            return False


    def export_to_dict(self):
        box_coords = [(b.x, b.y) for b in list(self.box.geoms)]
        return box_coords


    def com_distance(self, box, x, y):
        point = Point(x, y)
        poly_ext = LinearRing(self.box.geoms)
        distance = poly_ext.project(point)#istance(self, box):
        return Polygon(self.box).centroid.distance(Polygon(box.box).centroid)

    def closest_box(self, boxes):
        distances = [self.com_distance(b) for b in boxes]
        return boxes[distances.index(min(distances))]
