import entities
import worldmodel
import pygame
import math
import random
import point
import image_store

def create_miner_full_action(world, entity, i_store):
   def action(current_ticks):
      entity.remove_pending_action(action)

      entity_pt = entity.get_position()
      smith = world.find_nearest(entity_pt, entities.Blacksmith)
      (tiles, found) = entity.miner_to_smith(world, smith)

      new_entity = entity
      if found:
         new_entity = try_transform_miner(world, entity,
            try_transform_miner_full)

      new_entity.schedule_action(world,
         new_entity.create_miner_action(world, i_store),
         current_ticks + new_entity.get_rate())
      return tiles
   return action


def try_transform_miner_full(world, entity):
   new_entity = entities.MinerNotFull(
      entity.get_name(), entity.get_resource_limit(),
      entity.get_position(), entity.get_rate(),
      entity.get_images(), entity.get_animation_rate())

   return new_entity

   
def try_transform_miner_not_full(world, entity):
   if entity.resource_count < entity.resource_limit:
      return entity
   else:
      new_entity = entities.MinerFull(
         entity.get_name(), entity.get_resource_limit(),
         entity.get_position(), entity.get_rate(),
         entity.get_images(), entity.get_animation_rate())
      return new_entity

      
def try_transform_miner(world, entity, transform):
   new_entity = transform(world, entity)
   if entity != new_entity:
      world.clear_pending_actions(entity)
      world.remove_entity_at(entity.get_position())
      world.add_entity(new_entity)
      new_entity.schedule_animation(world)

   return new_entity


