import pygame
import math
import numpy
from constants import *
from functions import pythagoras, string_to_int_tuple

class Cell():
    def __init__(self, pos, width, value, colour):
        self.__rect = pygame.Rect(pos, (width+1, width+1))
        self.__value = value
        self.__colour = colour

    def point_collision(self, pos):
        if self.__rect.collidepoint(pos):
            return True
        return False
    
    def get_value(self):
        return self.__value
    
    def get_rect(self):
        return self.__rect
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.__colour, self.__rect)

class Player():
    def __init__(self, pos, angle, wall_width):
        self.__pos = pos
        self.__colour = PLAYER_COLOUR
        self.__width = PLAYER_WIDTH * wall_width
        self.__rect = pygame.Rect((0,0),(self.__width, self.__width))
        self.__rect.center = self.__pos
        self.__new_rect_x = self.__rect.copy()
        self.__new_rect_y = self.__rect.copy()
        self.__speed = PLAYER_MOVEMENT_SPEED * wall_width
        self.__angle_speed = PLAYER_ANGLE_SPEED
        self.__angle = angle

    def __move(self):
        keys = pygame.key.get_pressed()

        velocity = (0,0)

        if keys[pygame.K_w]:
            velocity = (self.__speed * math.cos(math.radians(self.__angle)), self.__speed * math.sin(math.radians(self.__angle)))
        if keys[pygame.K_s]:
            velocity = (self.__speed * -math.cos(math.radians(self.__angle)), self.__speed * -math.sin(math.radians(self.__angle)))
        if keys[pygame.K_a]:
            if keys[pygame.K_LSHIFT]:
                self.__angle -= self.__angle_speed/4
            else:
                self.__angle -= self.__angle_speed
        if keys[pygame.K_d]:
            if keys[pygame.K_LSHIFT]:
                self.__angle += self.__angle_speed/4
            else:
                self.__angle += self.__angle_speed

        return velocity
    
    def __collisions(self, velocity_x, velocity_y, game_grid):
        # check and correct for collisions with each collidable object in the game
        # rects that show where the player is about to move
        # only only taking into account x, one for y, and one for both
        self.__new_rect_x.center = self.__pos + pygame.math.Vector2(velocity_x, 0) 
        self.__new_rect_y.center = self.__pos + pygame.math.Vector2(0, velocity_y)

        x = velocity_x # temporary variables so it doesn't change between loops
        y = velocity_y

        for row in game_grid:
            for cell in row:
                if cell.get_value() > 0:
                    cell_rect = cell.get_rect()
                    collision_x = cell_rect.colliderect(self.__new_rect_x)
                    collision_y = cell_rect.colliderect(self.__new_rect_y)
                    
                    # adjust the motion of the player to the distance between them and the collidable
                    if collision_x:
                        if x < 0:  # moving left
                            velocity_x = -(self.__rect.left - cell_rect.right)
                        elif x > 0:  # moving right
                            velocity_x = cell_rect.left - self.__rect.right

                    if collision_y:
                        if y < 0:  # moving up
                            velocity_y = -(self.__rect.top - cell_rect.bottom)
                        elif y > 0:  # moving down
                            velocity_y = cell_rect.top - self.__rect.bottom

        return (velocity_x, velocity_y)

    def update(self, game_grid):
        velocity = pygame.math.Vector2(self.__move()) 
        velocity = pygame.math.Vector2(self.__collisions(*velocity, game_grid))
        self.__pos += velocity
        self.__rect.center = self.__pos
        self.__angle %= 360

    def get_angle(self):
        return self.__angle
    
    def get_pos(self):
        return self.__pos
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.__colour, self.__rect)
        pygame.draw.line(screen, (0,0,0), self.__pos, (self.__pos[X] + self.__width/2*math.cos(math.radians(self.__angle)), self.__pos[Y] + self.__width/2*math.sin(math.radians(self.__angle))), width=5)

class Game():
    def __init__(self, file_name):
        with open(file_name+".txt") as file:
            num_wall_types = int(file.readline())
            self.__wall_colours = []
            for _ in range(num_wall_types):
                self.__wall_colours.append(string_to_int_tuple(file.readline()))
            self.__grid_width = int(file.readline())
            self.__wall_width = SCREEN_WIDTH//self.__grid_width
            self.__grid = []
            for i in range(self.__grid_width):
                line = file.readline()[:-1].split(", ")
                self.__grid.append([Cell((j*self.__wall_width, i*self.__wall_width), self.__wall_width, int(line[j]), self.__value_to_colour(int(line[j]))) for j in range(len(line))])
            player_x, player_y = string_to_int_tuple(file.readline())
            player_x *= SCREEN_WIDTH/self.__grid_width
            player_y *= SCREEN_WIDTH/self.__grid_width
            angle = int(file.readline())

        self.__player = Player((player_x - self.__wall_width//2, player_y - self.__wall_width//2), angle, self.__wall_width)
    
    def update(self, screen):
        self.__player.update(self.__grid)
        self.__walls = self.__send_rays(screen, NUM_OF_RAYS)
        
    def __send_rays(self, screen, number):
        walls = []
        for angle in numpy.linspace(-FOV/2, FOV/2, number):
            ray_angle = round((self.__player.get_angle() + angle)%360)
            if ray_angle in [0,90,180,270,360]:
                ray_angle += 1
            total_length, wall_value = self.__send_ray(screen, self.__player.get_pos(), ray_angle)
            if wall_value > 0:
                walls.append({"value":wall_value, "distance":total_length, "angle":angle})
        return walls

    def __send_ray(self, screen, start_pos, angle):
        x,y = start_pos

        Xvelocity_x, Xvelocity_y = self.__ray_to_x((x,y), angle)
        Xlength = pythagoras(Xvelocity_x, Xvelocity_y)
        Yvelocity_x, Yvelocity_y = self.__ray_to_y((x,y), angle)
        Ylength = pythagoras(Yvelocity_x, Yvelocity_y)

        if Xlength <= Ylength:
            x += Xvelocity_x
            y += Xvelocity_y
            length = Xlength
        else:
            x += Yvelocity_x
            y += Yvelocity_y
            length = Ylength

        pygame.draw.line(screen, (240,240,0),start_pos,(x,y),width=2)
        collision, wall_value = self.__check_collision((x,y), get_value=True)
        if collision:
            return length, wall_value
        
        if not(0 < x < SCREEN_WIDTH and 0 < y < SCREEN_WIDTH):
            return length, 0
        
        total_length, wall_value = self.__send_ray(screen, (x,y), angle)
        return total_length + length, wall_value

    def __ray_to_x(self, start_pos, angle): # velocities till ray hits next vertical line
        distance_x = start_pos[X] % self.__wall_width
        # 270 is up, 90 is down, 0 is right, 180 is left
        if 90 < angle < 270: # left
            velocity_x = -distance_x
        else:
            velocity_x = self.__wall_width - distance_x
        
        if velocity_x == 0:
            if 90 < angle < 270: 
                velocity_x = -self.__wall_width
            else:
                velocity_x = self.__wall_width
        
        velocity_y = velocity_x * math.tan(math.radians(angle))

        return velocity_x, velocity_y

    def __ray_to_y(self, start_pos, angle): # velocities till ray hits next horizontal line
        distance_y = start_pos[Y] % self.__wall_width
        # 270 is up, 90 is down, 0 is right, 180 is left
        if 180 < angle < 360: # up
            velocity_y = -distance_y
        else:
            velocity_y = self.__wall_width - distance_y

        if velocity_y == 0:
            if 180 < angle < 360: 
                velocity_y = -self.__wall_width
            else:
                velocity_y = self.__wall_width

        velocity_x = velocity_y / math.tan(math.radians(angle))

        return velocity_x, velocity_y

    def __check_collision(self, pos, get_value=False):
        for row in self.__grid:
            for cell in row:
                if cell.get_value() > 0 and cell.point_collision(pos):
                    if get_value:
                        return True, cell.get_value()
                    return True
        if get_value:
            return False, 0
        return False

    def draw_2D(self, screen, draw_grid=False):
        for row in self.__grid:
            for cell in row:
                if cell.get_value() > 0:
                    cell.draw(screen)

        if draw_grid:
            self.__draw_2D_grid(screen)

        self.__player.draw(screen)

    def __draw_2D_grid(self, screen):
        for x_line in range(0, SCREEN_WIDTH, self.__wall_width):
                pygame.draw.line(screen, GRID_COLOUR, (x_line, 0), (x_line, SCREEN_WIDTH), width=1)
        for y_line in range(0, SCREEN_WIDTH, self.__wall_width):
            pygame.draw.line(screen, GRID_COLOUR, (0, y_line), (SCREEN_WIDTH,  y_line), width=1)

    def __value_to_colour(self, value):
        return self.__wall_colours[value - 1]

    def __distance_to_height(self, distance):
        return self.__wall_width * SCREEN_WIDTH / distance
    
    def __fade_out_colour(self, colour, distance):
        change = (distance / self.__wall_width * 30)
        value1 = colour[0] - change
        value2 = colour[1] - change
        value3 = colour[2] - change
        value1 = 0 if value1 < 0 else value1
        value2 = 0 if value2 < 0 else value2
        value3 = 0 if value3 < 0 else value3
        return (value1, value2, value3)

    def __angle_to_x(self, angle):
        return angle * (SCREEN_WIDTH/FOV) + SCREEN_WIDTH/2

    def __convert_to_lines(self):
        lines = []
        for wall in self.__walls:
            colour = self.__fade_out_colour(self.__value_to_colour(wall["value"]), wall["distance"])
            height = self.__distance_to_height(wall["distance"])
            x = self.__angle_to_x(wall["angle"])
            lines.append({"colour":colour, "height":height, "x":x})
        return lines

    def draw_3D(self, screen):
        pygame.draw.rect(screen, CEILING_COLOUR, ((0,0),(SCREEN_WIDTH, SCREEN_WIDTH//2)))
        pygame.draw.rect(screen, FLOOR_COLOUR, ((0,SCREEN_WIDTH//2),(SCREEN_WIDTH, SCREEN_WIDTH//2)))
        to_draw = self.__convert_to_lines()
        for line in to_draw:
            pygame.draw.line(screen, line["colour"], (line["x"], (SCREEN_WIDTH - line["height"]) // 2), (line["x"], (SCREEN_WIDTH + line["height"]) // 2), width=LINE_WIDTH)
