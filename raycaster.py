#Imports
import time
import math
import os
import pygame
from pygame.locals import *

#Classes
class Point:
    def __init__(self,x,y,k=1):
        self.x = x
        self.y = y
        self.k = k
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)
    def inter(self, other):
        dif = self - other
        half = Point(0.5*dif.x, 0.5*dif.y, 0.5*dif.z)
        return self + half
        

def vecLenght(vec):
    return (vec.x*vec.x + vec.y*vec.y)**0.5

def inverse_abs(vec):
    return (vec.x*vec.x + vec.y*vec.y)**(-0.5)

class gamemap:
    def __init__(self, size, a, mapmatrix = []):
        self.size = size
        self.a = a
        self.mapmatrix = mapmatrix
        self.step = size/a
        self.step_inverse = a/size

class character:
    def __init__(self, loc, rot, d, speed):
        self.loc = loc
        self.rot = norm_angle(to_radians(rot))
        self.d = d
        self.speed = speed
    def move(self, speed):
        self.loc.x += speed.x*math.cos(self.rot) + speed.y*math.cos(self.rot - 1.5707)
        self.loc.y += speed.x*math.sin(self.rot) + speed.y*math.sin(self.rot - 1.5707)
    def rotate(self, deltarot):
        rot = self.rot + to_radians(deltarot)
        self.rot = norm_angle(rot)

class camera:
    def __init__(self, aov, f):
        self.aov = to_radians(aov)
        self.f = f
        self.chw  = f*math.tan(0.5*aov) #Camera half width
      
#Functions
def get_index(gamemap,x,y): #Get coords and return matrix index
    step_inverse = gamemap.step_inverse
    xIndex = int(x*step_inverse)
    yIndex = int(y*step_inverse)
    mapIndex = yIndex*gamemap.a+xIndex
    return mapIndex

def check_collision(gamemap, x, y): #Check coillizinon int given coords
    try:
        mapIndex = get_index(gamemap, x, y)
        return gamemap.mapmatrix[mapIndex]
    except:
        return 0
    
def to_radians(angle): #To Radians 
    return angle*0.0174 #0.0174532925199433

def norm_angle(angle): #Normalize an angle
    return angle%6.2831 #6.283185307179586

def ceil(x):
    return int(x)+1

def colorize(image, newColor):
    image = image.copy()
    image.fill(newColor, None, pygame.BLEND_RGBA_MULT)
    return image

def near_grid(locx, locy, cos, sin, step, step_inverse): #Returns intersect point with nearest grid line plus delta
    #Preparing
    delta = 0.5
    #Nearest Y-grid
    if sin==0:
        y_dist = 10000
    else:
        locstepinv = locy*step_inverse #locy*step_inverse
        if sin<0:
            y_dist = abs((locy - (int(locstepinv)*step))/sin)+delta
        else:
            y_dist = abs((locy - (ceil(locstepinv)*step))/sin)+delta
    #Nearest X-grid
    if cos==0:
        x_dist = 10000
    else:
        locxstepinv = locx*step_inverse
        if cos<0:
            x_dist = abs((locx - (int(locxstepinv)*step))/cos)+delta
        else:
            x_dist = abs((locx - (ceil(locxstepinv)*step))/cos)+delta
    #Nearest grid line
    if x_dist<y_dist:
        intersection_point = Point(locx + x_dist*cos, locy + x_dist*sin, abs(cos))
    else: intersection_point = Point(locx + y_dist*cos, locy + y_dist*sin, abs(sin))
    return intersection_point
       
def trace(gamemap, loc, sin, cos, step, step_inverse): #Trace Line
    numb = 0
    intersect = 0
    while (intersect==0)and(numb<10):
        intersection_point = near_grid(loc.x, loc.y, cos, sin, step, step_inverse)
        intersect = check_collision(gamemap, intersection_point.x, intersection_point.y)
        loc = intersection_point
        numb+=1
    if numb==10: return Point(intersection_point.x + 10000*cos, intersection_point.y + 10000*sin)
    else: return intersection_point

def draw_floor(win, i, j, k4, char_loc, cos, sin, step_inverse, half_screen_height, floor_texture, floor_w, floor_h):
    k5 = abs(1-(k4*0.001))
    x_real,y_real = char_loc.x+k4*cos, char_loc.y+k4*sin
    x_relative,y_relative = (x_real*step_inverse)%1, (y_real*step_inverse)%1
    x,y = int(x_relative*floor_w),int(y_relative*floor_h)
    color1 = floor_texture.get_at((x,y))
    col = int(color1.r**k5)
    color2 = (col,col,col)
    try:
        win.set_at((i,j+half_screen_height-1),color2)
        win.set_at((i,j+half_screen_height),color2)
        win.set_at((i+1,j+half_screen_height-1),color2)
        win.set_at((i+1,j+half_screen_height),color2)
    except:
        win.set_at((i,j+half_screen_height-1),color1)
        win.set_at((i,j+half_screen_height),color1)
        win.set_at((i+1,j+half_screen_height-1),color1)
        win.set_at((i+1,j+half_screen_height),color1)
    
              

def draw_image(win, char, gamemap, cam, clay, k, k2, show_sky, textures):
    #Const
    eps = 0.008
    eps2 = 0.992
    #Calculate some params and getting from classes
    screen_width,screen_height = win.get_width(), win.get_height() #Get screen heigth and width
    half_screen_height = int(0.5*screen_height)
    chw = cam.chw
    camf = cam.f
    step = gamemap.step
    step_inverse =  gamemap.step_inverse
    char_rot = char.rot
    char_loc = char.loc
    #Textures sizes
    floor_w = textures[0].get_width()
    floor_h = textures[0].get_height()
    #Drawing sky. If show_sky is true calculate some params, else just draw single color sky.
    if show_sky:
        skw = textures[4].get_width()
        skw6 = skw*0.1591
        sph = textures[4].get_height()
    else:
        sky_y = int(0.25*screen_height)
        pygame.draw.line(win, [127,218,255], [0, sky_y], [screen_width,sky_y], int(half_screen_height))
    #Prepare generators for loop
    
    angles = map(lambda i: math.atan2((chw-k*i),camf), range(0,screen_width,2))
    i_s = range(0,screen_height,2)
    #Main Loop \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    for i,angle in zip(i_s,angles):
        trace_angle = norm_angle(char_rot + angle)
        cos = math.cos(trace_angle)
        sin = math.sin(trace_angle)
        p = trace(gamemap, char_loc, sin, cos, step, step_inverse)
        px = p.x
        py = p.y
        k3 = k2/math.cos(angle)
        segsize = k3*inverse_abs(char_loc - p) #It's half segment size.
        #If show_sky is true draw sky, else do nothing
        if show_sky:
            x_coord = skw6*trace_angle
            if (x_coord>0)and(x_coord<skw):
                sky = pygame.transform.scale(textures[4].subsurface((int(x_coord), 0, 1, sph)), (1, half_screen_height))
                win.blit(sky, (i,0))
                win.blit(sky, (i+1,0))
        #If clay is false draw wall segments with texture, else just draw single color wall segments
        if clay==False:
            wallIndex = check_collision(gamemap, px, py)
            wall = textures[wallIndex]
            wall_w = wall.get_width()
            wall_h = wall.get_height()
            u = (px*step_inverse)%1
            if (u<eps)or(u>eps2):
                u = (py*step_inverse)%1
            sc = textures[5].get_at((int(98.0*p.k),2)) #Shade color
            segment = pygame.transform.scale(wall.subsurface((int(u*wall_w), 0, 1, wall_h)), (1, int(2*segsize)))
            shaded = colorize(segment, sc)
            win.blit(shaded, (i,half_screen_height-segsize))
            win.blit(shaded, (i+1,half_screen_height-segsize))
        else:
            sc = textures[5].get_at((int(98.0*p.k),2))
            pygame.draw.line(win, sc, [i, half_screen_height-segsize], [i,half_screen_height+segsize], 1)
            pygame.draw.line(win, sc, [i+1, half_screen_height-segsize], [i+1,half_screen_height+segsize], 1)
        
        #Draw floor (!complete)
        if segsize < 1: y_start = int(segsize) + 1
        else: y_start = int(segsize)
        j = y_start
        #Sub loop for drawing floor\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        for j in range(y_start, int(half_screen_height),2):
            k4 = k3/j
            draw_floor(win, i, j, k4, char_loc, cos, sin, step_inverse, half_screen_height, textures[0], floor_w, floor_h)
    pygame.display.flip()
    #print(fdc)

                                           
def main():
    #CreateMainWindow
    win_width = 256
    win_hieght = 256
    pygame.init()
    flags = DOUBLEBUF
    win = pygame.display.set_mode((win_width,win_hieght), flags)
    win.set_alpha(None)
    pygame.display.set_caption("My map")
    fps_font = pygame.font.SysFont(None, 24)

    #Game Settings
    map_size = 2048 #In cm
    map_rez = 8
    max_fps = 12
    limit_fps = False
    clay = False
    show_fps = True
    show_sky = True

    #Init Map
    matrix = [1,3,1,2,1,1,1,1, 1,0,3,0,0,0,0,1, 1,0,3,0,0,0,0,1, 1,0,1,0,2,0,3,1, 3,0,0,0,0,0,3,1, 1,0,0,0,0,0,0,1, 1,0,0,0,1,0,0,1, 1,3,2,3,3,1,3,3]
    #matrix = list(map(lambda x: 0, range(map_size*map_size))) #Testing an empty map
    test = gamemap( map_size, map_rez, matrix)
    
    #Importing textures
    textures =[pygame.image.load(os.path.join('D:\Programming\RayCast\data', 'floor.bmp')).convert(),
               pygame.image.load(os.path.join('D:\Programming\RayCast\data', 'brick1.bmp')).convert(),
               pygame.image.load(os.path.join('D:\Programming\RayCast\data', 'brick2.bmp')).convert(),
               pygame.image.load(os.path.join('D:\Programming\RayCast\data', 'brick3.bmp')).convert(),
               pygame.image.load(os.path.join('D:\Programming\RayCast\data', 'sky3.jpg')).convert(),
               pygame.image.load(os.path.join('D:\Programming\RayCast\data', 'mc.jpg')).convert()]
    
    #Init Character
    hero = character(Point(400,400),50,50,4) #Location, rotation, radius, speed
    herospeed = hero.speed
    herospeed_reverse = 0 - hero.speed
    hero.rotate(90)

    #Init Camera
    cam01 = camera(80,70)

    #Run
    run = True
    keypress = False
    rotspeed = 0
    speed = Point(0,0)
   
    
    #Main Cycle
    while run:
        frame_start = time.time()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False
                pygame.quit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    run = False
                    pygame.quit()
                if e.key == pygame.K_RIGHT:
                    rotspeed = 2
                if e.key == pygame.K_LEFT:
                    rotspeed = -2
                if e.key == pygame.K_w:
                    speed.x = herospeed
                if e.key == pygame.K_s:
                    speed.x = herospeed_reverse
                if e.key == pygame.K_a:
                    speed.y = herospeed
                if e.key == pygame.K_d:
                    speed.y = herospeed_reverse
            if e.type == pygame.KEYUP:
                if (e.key == pygame.K_RIGHT)or(e.key == pygame.K_LEFT):
                    rotspeed = 0
                if (e.key == pygame.K_w):
                    speed.x = 0
                if (e.key == pygame.K_s):
                    speed.x = 0
                if (e.key == pygame.K_a):
                    speed.y = 0
                if (e.key == pygame.K_d):
                    speed.y = 0
        if rotspeed!=0:
            hero.rotate(rotspeed)
        if speed.y!=0 or speed.x!=0:
            hd = 2*hero.d + speed.y
        if speed.y>0:
            new_x = hero.loc.x + (hero.d + speed.x)*math.cos(hero.rot) + hd*math.cos(hero.rot - 1.5707)
            new_y = hero.loc.y + (hero.d + speed.x)*math.sin(hero.rot) + hd*math.sin(hero.rot- 1.5707)
            if check_collision(test, new_x, new_y)==False:
                     hero.move(speed)
        elif speed.x>0:
            new_x = hero.loc.x + (hero.d + speed.x)*math.cos(hero.rot) + hd*math.cos(hero.rot + 1.5707)
            new_y = hero.loc.y + (hero.d + speed.x)*math.sin(hero.rot) + hd*math.sin(hero.rot +  1.5707)
            if check_collision(test, new_x, new_y)==False:
                hero.move(speed)
        #Draw Image
        screen_width,screen_height = win.get_width(), win.get_height()
        k = 2*cam01.chw/screen_width
        k2 = 0.5*cam01.f*screen_height
        draw_image(win, hero, test, cam01, clay, k, k2, show_sky, textures)
        frame_end = time.time()
        frame_time = frame_end - frame_start
        if frame_time<(1./max_fps)and limit_fps:
            pygame.time.wait(int(1./max_fps-frame_time))
        elif show_fps:
            text_fps = fps_font.render(str(int(frame_time**-1)), 0, (255,255,255))
            win.blit(text_fps, (20,20))
            pygame.display.update()           
    
if __name__ == "__main__":
    main()
    #cProfile.run('main()')
