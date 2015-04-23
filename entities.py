import point
import actions
import worldmodel
import pygame
import math
import random
import point
import image_store
import save_load

"""
Sorting Method:
- Background
- Entity
   - Entity children
- Movable
   - Moveable children
- Animation
   - Animation children
- Miner
"""

BLOB_RATE_SCALE = 4
BLOB_ANIMATION_RATE_SCALE = 50
BLOB_ANIMATION_MIN = 1
BLOB_ANIMATION_MAX = 3

ORE_CORRUPT_MIN = 20000
ORE_CORRUPT_MAX = 30000

QUAKE_STEPS = 10
QUAKE_DURATION = 1100
QUAKE_ANIMATION_RATE = 100

VEIN_SPAWN_DELAY = 500
VEIN_RATE_MIN = 8000
VEIN_RATE_MAX = 17000

class Background(object):
   def __init__(self, name, imgs):
      self.name = name
      self.imgs = imgs
      self.current_img = 0
      
   def get_images(self):
      return self.imgs

   def get_image(self):
      return self.imgs[self.current_img]
   
   def get_name(self):
      return self.get_name
      
   def next_image(self):
      self.current_img = (self.current_img + 1) % len(self.imgs)


######################### ENTITY #################################

      
class Entity(Background):
      
   def __init__(self, name, position, imgs):
      self.position = position
      super(Entity, self).__init__(name, imgs)

   def set_position(self, point):
      self.position = point

   def get_position(self):
      return self.position

   def create_entity_death_action(self, world):
      def action(current_ticks):
         self.remove_pending_action(action)
         pt = self.get_position()
         self.remove_entity(world)
         return [pt]
      return action
            
   def remove_entity(self, world):
      for action in self.get_pending_actions():
         world.unschedule_action(action)
      self.clear_pending_actions()
      world.remove_entity(self)

      
class Blacksmith(Entity):
   def __init__(self, name, position, imgs, resource_limit, rate,
                resource_distance=1):
      self.current_img = 0
      self.resource_limit = resource_limit
      self.resource_count = 0
      self.rate = rate
      self.resource_distance = resource_distance
      self.pending_actions = []
      super(Blacksmith, self).__init__(name, position, imgs)
   
   def get_rate(self):
      return self.rate
   
   def set_resource_count(self, n):
      self.resource_count = n
      
   def get_resource_count(self):
      return self.resource_count
   
   def get_resource_limit(self):
      return self.resource_limit
   
   def get_resource_distance(self):
      return self.resource_distance
   
   def entity_sting(self):
      return ' '.join(['blacksmith', self.name, str(self.position.x),
                        str(self.position.y), str(self.resource_limit),
                        str(self.rate), str(self.resource_distance)])

   
class Obstacle(Entity):
   def __init__(self, name, position, imgs):
      self.name = name
      self.position = position
      self.imgs = imgs
      self.current_img = 0
      
   def entity_string(self):
      return ' '.join(['obstacle', self.name, str(self.position.x),
                        str(self.position.y)])

   
######################## MOVEABLE #############################
                 # ACTION-TYPE CLASSES #

   
class Moveable(Entity):

      
   def get_rate(self):
      return self.rate
                        
   def schedule_action(self, world, action, time):
      self.add_pending_action(action)
      world.schedule_action(action, time)
   
   def remove_pending_action(self, action):
      if hasattr(self, "pending actions"):
         self.pending_actions.remove(action)
         
   def add_pending_action(self, action):
      if hasattr(self, "pending actions"):
         self.pending_actions.append(action)
         
   def get_pending_actions(self):
      if hasattr(self, "pending_actions"):
         return self.pending_actions
      else:
         return[]
      
   def clear_pending_actions(self):
      if hasattr(self, "pending actions"):
         self.pending_actions = []

#
   
class Vein(Moveable):
   def __init__(self, name, rate, position, imgs, resource_distance=1):
      self.rate = rate
      self.current_img = 0
      self.resource_distance = resource_distance
      self.pending_actions = []
      super(Vein, self).__init__(name, position, imgs)

   
   def get_resource_distance(self):
      return self.resource_distance

   def entity_string(self):
      return ' '.join(['vein', self.name, str(self.position.x),
                        str(self.position.y), str(self.rate),
                        str(self.resource_distance)])
      
   def create_vein_action(self, world, i_store):
      def action(current_ticks):
         self.remove_pending_action(action)

         open_pt = world.find_open_around(self.get_position(),
            self.get_resource_distance())
         if open_pt:
            ore = world.create_ore(
               "ore - " + str(self.get_name()) + " - " + str(current_ticks),
               open_pt, current_ticks, i_store)
            world.add_entity(ore)
            tiles = [open_pt]
         else:
            tiles = []

         self.schedule_action(world,
            self.create_vein_action(world, i_store),
            current_ticks + self.get_rate())
         return tiles
      return action

         
   def schedule_vein(self, world, ticks, i_store):
      self.schedule_action(world, self.create_vein_action(world, i_store),
                           ticks + self.get_rate())

      
class Ore(Moveable):
   def __init__(self, name, position, imgs, rate=5000):
      self.current_img = 0
      self.rate = rate
      self.pending_actions = []
      super(Ore, self).__init__(name, position, imgs)

   def entity_string(self):
      return ' '.join(['ore', self.name, str(self.position.x),
         str(self.position.y), str(self.rate)])

   def create_ore_transform_action(self, world, i_store):
      def action(current_ticks):
         self.remove_pending_action(action)
         blob = world.create_blob(str(self.get_name()) + " -- blob",
                                  self.get_position(),
                                  self.get_rate() // BLOB_RATE_SCALE,
                                  current_ticks, i_store)

         self.remove_entity(world)
         world.add_entity(blob)

         return [blob.get_position()]
      return action
         
   def schedule_ore(self, world, ticks, i_store):
      self.schedule_action(world, 
                           self.create_ore_transform_action(world, i_store),
                           ticks + self.get_rate())


########################## ANIMATED ###############################
              # OBJECTS THAT ARE ANIMATED ONSCREEN #

class Animated(Moveable):
   def __init__(self, name, position, imgs, animation_rate):
      self.animation_rate = animation_rate
      super(Animated, self).__init__(name, position, imgs)
      
   def get_animation_rate(self):
      return self.animation_rate
            
   def create_animation_action(self, world, repeat_count):
      def action(current_ticks):
         self.remove_pending_action(action)

         self.next_image()

         if repeat_count != 1:
            self.schedule_action(world,
               self.create_animation_action(world, max(repeat_count - 1, 0)),
               current_ticks + self.get_animation_rate())

         return [self.get_position()]
      return action
                     
   def schedule_animation(self, world, repeat_count=0):
      self.schedule_action(world,
                           self.create_animation_action(world, repeat_count),
                           self.get_animation_rate())

#
   
class OreBlob(Animated):
   def __init__(self, name, position, rate, imgs, animation_rate):
      self.rate = rate
      self.current_img = 0
      self.pending_actions = []
      super(OreBlob, self).__init__(name, position, imgs, animation_rate)

   def blob_to_vein(self, world, vein):
      entity_pt = self.get_position()
      if not vein:
         return ([entity_pt], False)
      vein_pt = vein.get_position()
      if entity_pt.adjacent(vein_pt):
         vein.remove_entity(world)
         return ([vein_pt], True)
      else:
         new_pt = world.blob_next_position(entity_pt, vein_pt)
         old_entity = world.get_tile_occupant(new_pt)
         if isinstance(old_entity, Ore):
            old_entity.remove_entity(world)
         return (world.move_entity(self, new_pt), False)
      
   def create_ore_blob_action(self, world, i_store):
      def action(current_ticks):
         self.remove_pending_action(action)

         entity_pt = self.get_position()
         vein = world.find_nearest(entity_pt, Vein)
         (tiles, found) = self.blob_to_vein(world, vein)

         next_time = current_ticks + self.get_rate()
         if found:
            quake = world.create_quake(tiles[0], current_ticks, i_store)
            world.add_entity(quake)
            next_time = current_ticks + self.get_rate() * 2

         self.schedule_action(world,
                              self.create_ore_blob_action(world, i_store),
                              next_time)

         return tiles
      return action

   def schedule_blob(self, world, ticks, i_store):
      self.schedule_action(world, self.create_ore_blob_action(world, i_store),
                           ticks + self.get_rate())
      self.schedule_animation(world)


class Quake(Animated):
   def __init__(self, name, position, imgs, animation_rate):
      self.current_img = 0
      self.pending_actions = []
      super(Quake, self).__init__(name, position, imgs, animation_rate)

   def schedule_quake(self, world, ticks):
      self.schedule_animation(world, QUAKE_STEPS) 
      self.schedule_action(world, self.create_entity_death_action(world),
                           ticks + QUAKE_DURATION)


####################### MINER #########################

class Miner(Animated):
   def __init__(self, name, resource_limit, position, rate, imgs,
                animation_rate):
      self.rate = rate
      self.resource_limit = resource_limit
      super(Miner, self).__init__(name, position, imgs, animation_rate)      

   def set_resource_count(self, n):
      self.resource_count = n
      
   def get_resource_count(self):
      return self.resource_count
   
   def get_resource_limit(self):
      return self.resource_limit

   def entity_string(self):
      return ' '.join(['miner', self.name, str(self.position.x),
                      str(self.position.y), str(self.resource_limit),
                      str(self.rate), str(self.animation_rate)])

   def create_miner_action(self, world, image_store):
      return self.create_miner_type_action(world, image_store)
               
   def schedule_miner(self, world, ticks, i_store):
      self.schedule_action(world, self.create_miner_action(world, i_store),
                           ticks + self.get_rate())
      self.schedule_animation(world)

#

class MinerNotFull(Miner):
   def __init__(self, name, resource_limit, position, rate, imgs,
                animation_rate):
      self.current_img = 0
      self.resource_count = 0
      self.pending_actions = []
      super(MinerNotFull, self).__init__(name, resource_limit, position,
                                         rate, imgs, animation_rate)
   
   def miner_to_ore(self, world, ore):
      entity_pt = self.get_position()
      if not ore:
         return ([entity_pt], False)
      ore_pt = ore.get_position()
      if entity_pt.adjacent(ore_pt):
         self.set_resource_count(1 + self.get_resource_count())
         ore.remove_entity(world)
         return ([ore_pt], True)
      else:
         new_pt = world.next_position(entity_pt, ore_pt)
         return (world.move_entity(self, new_pt), False)
      
   def create_miner_type_action(self, world, i_store):
      def action(current_ticks):
         self.remove_pending_action(action)

         entity_pt = self.get_position()
         ore = world.find_nearest(entity_pt, Ore)
         (tiles, found) = self.miner_to_ore(world, ore)

         new_entity = self
         if found:
            new_entity = actions.try_transform_miner(world, self,
               actions.try_transform_miner_not_full)

         new_entity.schedule_action(world,
                         new_entity.create_miner_action(world, i_store),
            current_ticks + new_entity.get_rate())
         return tiles
      return action
               
      
class MinerFull(Miner):
   def __init__(self, name, resource_limit, position, rate, imgs,
                animation_rate):
      self.current_img = 0
      self.resource_count = 0
      self.pending_actions = []
      super(MinerFull, self).__init__(name, resource_limit, position,
                                      rate, imgs, animation_rate)
   
   def miner_to_smith(self, world, smith):
      entity_pt = self.get_position()
      if not smith:
         return ([entity_pt], False)
      smith_pt = smith.get_position()
      if entity_pt.adjacent(smith_pt):
         smith.set_resource_count(
            smith.get_resource_count() +
            self.get_resource_count())
         self.set_resource_count(0)
         return ([], True)
      else:
         new_pt = world.next_position(entity_pt, smith_pt)
         return (world.move_entity(self, new_pt), False)
   
   def create_miner_type_action(self, world, i_store):
      def action(current_ticks):
         self.remove_pending_action(action)

         entity_pt = self.get_position()
         smith = world.find_nearest(entity_pt, Blacksmith)
         (tiles, found) = self.miner_to_smith(world, smith)

         new_entity = self
         if found:
            new_entity = actions.try_transform_miner(world, self,
               actions.try_transform_miner_full)

         new_entity.schedule_action(world,
            new_entity.create_miner_action(world, i_store),
            current_ticks + new_entity.get_rate())
         return tiles
      return action
   




