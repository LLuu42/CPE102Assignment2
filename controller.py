import pygame
import worldview
import worldmodel
import point

KEY_DELAY = 400
KEY_INTERVAL = 100

TIMER_FREQUENCY = 100

def on_keydown(event):
   x_delta = 0
   y_delta = 0
   if event.key == pygame.K_UP: y_delta -= 1
   if event.key == pygame.K_DOWN: y_delta += 1
   if event.key == pygame.K_LEFT: x_delta -= 1
   if event.key == pygame.K_RIGHT: x_delta += 1

   return (x_delta, y_delta)


def mouse_to_tile(pos, tile_width, tile_height):
   return point.Point(pos[0] // tile_width, pos[1] // tile_height)


def activity_loop(view, world):
   pygame.key.set_repeat(KEY_DELAY, KEY_INTERVAL)
   pygame.time.set_timer(pygame.USEREVENT, TIMER_FREQUENCY)

   while 1:
      for event in pygame.event.get():
         if event.type == pygame.QUIT:
            return
         elif event.type == pygame.USEREVENT:
            world.handle_timer_event(view)
         elif event.type == pygame.MOUSEMOTION:
            view.handle_mouse_motion(event)
         elif event.type == pygame.KEYDOWN:
            view.handle_keydown(event)

