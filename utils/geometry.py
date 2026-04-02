import pygame

def get_diamond_footprint(rect):
    """
    Returns a list of 4 Vector2 points representing the diamond footprint
    at the bottom of a rectangle in a 2.5D isometric view.
    """
    w = rect.width
    h = rect.height / 4
    
    center_x = rect.centerx
    bottom_y = rect.bottom
    center_y = bottom_y - h / 2
    
    p1 = pygame.math.Vector2(center_x, bottom_y - h) # Top point of diamond
    p2 = pygame.math.Vector2(center_x + w/2, center_y) # Right
    p3 = pygame.math.Vector2(center_x, bottom_y) # Bottom
    p4 = pygame.math.Vector2(center_x - w/2, center_y) # Left
    
    return [p1, p2, p3, p4]

def point_in_polygon(point, poly):
    x, y = point.x, point.y
    n = len(poly)
    inside = False

    p1x, p1y = poly[0].x, poly[0].y
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n].x, poly[i % n].y
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside

def polygons_intersect(poly1, poly2):
    for point in poly1:
        if point_in_polygon(point, poly2):
            return True
    for point in poly2:
        if point_in_polygon(point, poly1):
            return True
    return False
