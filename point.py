class Point:
   def __init__(self, x, y):
      self.x = x
      self.y = y

   def distance_sq(self, p):
      return (self.x - p.x) ** 2 + (self.y - p.y) ** 2

   def adjacent(self, pt):
      return ((self.x == pt.x and abs(self.y - pt.y) == 1) or
         (self.y == pt.y and abs(self.x - pt.x) == 1))
