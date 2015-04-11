import entities
import pygame
import ordered_list
import actions
import occ_grid
import point
import entities
import worldmodel
import pygame
import math
import random
import point
import image_store
import save_load

BLOB_RATE_SCALE = 4
BLOB_ANIMATION_RATE_SCALE = 50
BLOB_ANIMATION_MIN = 1
BLOB_ANIMATION_MAX = 3

ORE_CORRUPT_MIN = 20000
ORE_CORRUPT_MAX = 30000

QUAKE_STEPS = 10
QUAKE_DURATION = 1100
QUAKE_ANIMATION_RATE = 100
"""
VEIN_SPAWN_DELAY = 500
VEIN_RATE_MIN = 8000
VEIN_RATE_MAX = 17000

BGND_KEY = 'background'
BGND_NUM_PROPERTIES = 4
BGND_NAME = 1
BGND_COL = 2
BGND_ROW = 3


VEIN_REACH = 5
"""
class WorldModel:
   def __init__(self, num_rows, num_cols, background):
      self.background = occ_grid.Grid(num_cols, num_rows, background)
      self.num_rows = num_rows
      self.num_cols = num_cols
      self.occupancy = occ_grid.Grid(num_cols, num_rows, None)
      self.entities = []
      self.action_queue = ordered_list.OrderedList()
      
   def within_bounds(self, pt):
      return (pt.x >= 0 and pt.x < self.num_cols and
              pt.y >= 0 and pt.y < self.num_rows)

   def is_occupied(self, pt):
      return (self.within_bounds(pt) and
              self.occupancy.get_cell(pt) != None)

   def find_nearest(self, pt, type):
      oftype = [(e, pt.distance_sq(e.get_position()))
         for e in self.entities if isinstance(e, type)]
      return nearest_entity(oftype)

   def add_entity(self, entity):
      pt = entity.get_position()
      if self.within_bounds(pt):
         old_entity = self.occupancy.get_cell(pt)
         if old_entity != None:
            old_entity.clear_pending_actions()
         self.occupancy.set_cell(pt, entity)
         self.entities.append(entity)

   def move_entity(self, entity, pt):
      tiles = []
      if self.within_bounds(pt):
         old_pt = entity.get_position()
         self.occupancy.set_cell(old_pt, None)
         tiles.append(old_pt)
         self.occupancy.set_cell(pt, entity)
         tiles.append(pt)
         entity.set_position(pt)
      return tiles

   def remove_entity(self, entity):
      self.remove_entity_at(entity.get_position())
         
   def remove_entity_at(self, pt):
      if (self.within_bounds(pt) and
         self.occupancy.get_cell(pt) != None):
         entity = self.occupancy.get_cell(pt)
         entity.set_position(point.Point(-1, -1))
         self.entities.remove(entity)
         self.occupancy.set_cell(pt, None)

   def schedule_action(self, action, time):
      self.action_queue.insert(action, time)
      
   def unschedule_action(self, action):
      self.action_queue.remove(action)
      
   def update_on_time(self, ticks):
      tiles = []

      next = self.action_queue.head()
      while next and next.ord < ticks:
         self.action_queue.pop()
         tiles.extend(next.item(ticks))  # invoke action function
         next = self.action_queue.head()
      return tiles

   def get_background_image(self, pt):
      if self.within_bounds(pt):
         return self.background.get_cell(pt).get_image()
         
   def get_background(self, pt):
      if self.within_bounds(pt):
         return self.background.get_cell(pt)
         
   def set_background(self, pt, bgnd):
      if self.within_bounds(pt):
         self.background.set_cell(pt, bgnd)
            
   def add_background(self, properties, i_store):
      if len(properties) >= BGND_NUM_PROPERTIES:
         pt = point.Point(int(properties[BGND_COL]), int(properties[BGND_ROW]))
         name = properties[BGND_NAME]
         self.set_background(pt,
            entities.Background(name, image_store.get_images(i_store, name)))

   def get_tile_occupant(self, pt):
      if self.within_bounds(pt):
         return self.occupancy.get_cell(pt)

   def get_entities(self):
      return self.entities

   def next_position(self, entity_pt, dest_pt):
      horiz = sign(dest_pt.x - entity_pt.x)
      new_pt = point.Point(entity_pt.x + horiz, entity_pt.y)

      if horiz == 0 or self.is_occupied(new_pt):
         vert = sign(dest_pt.y - entity_pt.y)
         new_pt = point.Point(entity_pt.x, entity_pt.y + vert)

         if vert == 0 or self.is_occupied(new_pt):
            new_pt = point.Point(entity_pt.x, entity_pt.y)

      return new_pt

   def blob_next_position(self, entity_pt, dest_pt):
      horiz = sign(dest_pt.x - entity_pt.x)
      new_pt = point.Point(entity_pt.x + horiz, entity_pt.y)

      if horiz == 0 or (self.is_occupied(new_pt) and
         not isinstance(self.get_tile_occupant(new_pt),
         entities.Ore)):
         vert = sign(dest_pt.y - entity_pt.y)
         new_pt = point.Point(entity_pt.x, entity_pt.y + vert)

         if vert == 0 or (self.is_occupied(new_pt) and
            not isinstance(self.get_tile_occupant(new_pt),
            entities.Ore)):
            new_pt = point.Point(entity_pt.x, entity_pt.y)

      return new_pt

   def find_open_around(self, pt, distance):
      for dy in range(-distance, distance + 1):
         for dx in range(-distance, distance + 1):
            new_pt = point.Point(pt.x + dx, pt.y + dy)

            if (self.within_bounds(new_pt) and
               (not self.is_occupied(new_pt))):
               return new_pt

      return None
      
   def create_blob(self, name, pt, rate, ticks, i_store):
      blob = entities.OreBlob(name, pt, rate,
         actions.image_store.get_images(i_store, 'blob'),
         random.randint(BLOB_ANIMATION_MIN, BLOB_ANIMATION_MAX)
         * BLOB_ANIMATION_RATE_SCALE)
      blob.schedule_blob(self, ticks, i_store)
      return blob
   
   def create_ore(self, name, pt, ticks, i_store):
      ore = entities.Ore(name, pt, image_store.get_images(i_store, 'ore'),
         random.randint(ORE_CORRUPT_MIN, ORE_CORRUPT_MAX))
      ore.schedule_ore(self, ticks, i_store)

      return ore
   
   def create_quake(self, pt, ticks, i_store):
      quake = entities.Quake("quake", pt,
         image_store.get_images(i_store, 'quake'), QUAKE_ANIMATION_RATE)
      quake.schedule_quake(self, ticks)
      return quake
   
   def create_vein(self, name, pt, ticks, i_store):
      vein = entities.Vein("vein" + name,
         random.randint(VEIN_RATE_MIN, VEIN_RATE_MAX),
         pt, image_store.get_images(i_store, 'vein'))
      return vein
   
   def clear_pending_actions(self, entity):
      for action in entity.get_pending_actions():
         self.unschedule_action(action)
      entity.clear_pending_actions()

      
   def save_world_controller(self, filename):
      with open(filename, 'w') as file:
         save_load.save_world(self, file)
            
   def load_world_controller(self, i_store, filename):
      with open(filename, 'r') as file:
         save_load.load_world(self, i_store, file)
            
   def on_keydown(self, event, entity_select, i_store):
      x_delta = 0
      y_delta = 0
      if event.key == pygame.K_UP: y_delta -= 1
      if event.key == pygame.K_DOWN: y_delta += 1
      if event.key == pygame.K_LEFT: x_delta -= 1
      if event.key == pygame.K_RIGHT: x_delta += 1
      elif event.key in keys.ENTITY_KEYS:
         entity_select = keys.ENTITY_KEYS[event.key]
      elif event.key == keys.SAVE_KEY: self.save_world(WORLD_FILE_NAME)
      elif event.key == keys.LOAD_KEY: load_world(world, i_store, WORLD_FILE_NAME)

      return ((x_delta, y_delta), entity_select)
            
   def handle_keydown(self, view, event, i_store, entity_select):
      (view_delta, entity_select) = self.on_keydown(event,
         entity_select, i_store)
      view.update_view(view_delta,
         image_store.get_images(i_store, entity_select)[0])

      return entity_select    
      
   def handle_mouse_button(self, view, event, entity_select, i_store):
      mouse_pt = mouse_to_tile(event.pos, view.tile_width, view.tile_height)
      tile_view_pt = view.viewport_to_world(mouse_pt)
      if event.button == mouse_buttons.LEFT and entity_select:
         if is_background_tile(entity_select):
            self.set_background(tile_view_pt,
               entities.Background(entity_select,
                  image_store.get_images(i_store, entity_select)))
            return [tile_view_pt]
         else:
            new_entity = create_new_entity(tile_view_pt, entity_select, i_store)
            if new_entity:
               self.remove_entity_at(tile_view_pt)
               self.add_entity(new_entity)
               return [tile_view_pt]
      elif event.button == mouse_buttons.RIGHT:
         self.remove_entity_at(tile_view_pt)
         return [tile_view_pt]

      return []

   def activity_loop(self, view, i_store):
      pygame.key.set_repeat(keys.KEY_DELAY, keys.KEY_INTERVAL)

      entity_select = None
      while 1:
         for event in pygame.event.get():
            if event.type == pygame.QUIT:
               return
            elif event.type == pygame.MOUSEMOTION:
               view.handle_mouse_motion(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
               tiles = self.handle_mouse_button( view, event, entity_select,
                  i_store)
               view.update_view_tiles(tiles)
            elif event.type == pygame.KEYDOWN:
               entity_select = handle_keydown(view, event, i_store, self,
                  entity_select)
               
                  
   def handle_timer_event(self, view):
      rects = self.update_on_time(pygame.time.get_ticks())
      view.update_view_tiles(rects)

def sign(x):
   if x < 0:
      return -1
   elif x > 0:
      return 1
   else:
      return 0


def nearest_entity(entity_dists):
   if len(entity_dists) > 0:
      pair = entity_dists[0]
      for other in entity_dists:
         if other[1] < pair[1]:
            pair = other
      nearest = pair[0]
   else:
      nearest = None

   return nearest













