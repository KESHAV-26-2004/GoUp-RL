import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pygame
import random
from os import listdir
from os.path import isfile, join
from threading import Timer
import time
import sys

pygame.init()
pygame.mixer.init()

pygame.display.set_caption("GO UP")

bg_color=(255,255,255)
WIDTH,HEIGHT=1650,950
fps=60
player_vel=6
e=0
score=0
score1=str(score)
y1_score=0
d=0
c=0

clock=pygame.time.Clock()

window=pygame.display.set_mode((WIDTH,HEIGHT))

font1=pygame.font.SysFont("araiblack",200)
font2=pygame.font.SysFont("araiblack",50)
font3=pygame.font.SysFont("araiblack",85)
text_col1=(80,100,170)
text_col2=(0,0,0)
text_col3=(255,20,20)
text_col4=(190,0,0)
text_col5=(0,50,50)
a_yaxis=[]
c_xaxis=[]
side1_l=[]
y_axis=854
side1_y=854

for i in range(150):
    y_axis-=192
    a_yaxis.append(y_axis)
#print(a_yaxis)

for i in range(400):
    side1_y-=96
    side1_l.append(side1_y)

for i in range(150):
    b=[]
    x0=random.randint(40,120)
    x1=random.randint(230,420)
    x2=random.randint(570,780)
    x3=random.randint(910,1070)
    x4=random.randint(1220,1500)
    x5=random.randint(40,300)
    x6=random.randint(396,685)
    x7=random.randint(781,925)
    x8=random.randint(1121,1532)
    x9=random.randint(40,500)
    x10=random.randint(596,960)
    x11=random.randint(1050,1500)

    b.append(x0)
    b.append(x1)
    b.append(x2)
    b.append(x3)
    b.append(x4)
    b.append(x5)
    b.append(x6)
    b.append(x7)
    b.append(x8)
    b.append(x9)
    b.append(x10)
    b.append(x11)
    c_xaxis.append(b)

#Import button from png
class Button():
    def __init__(self,x,y,image,scale):
        width=image.get_width()
        height=image.get_height()
        self.image=pygame.transform.scale(image,
            (int((width*scale)*3/2),int((height*scale)*3/2)))
        #print(width*scale,height*scale)
        self.rect=self.image.get_rect()
        self.rect.topleft=(x,y)
        self.clicked=False

    def draw(self,surface):
        action=False
        #get mouse postion
        pos=pygame.mouse.get_pos()

        #chech mouseover and clicked condtions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0]==1 and self.clicked==False:
                self.clicked=True
                action=True

        if pygame.mouse.get_pressed()[0]==0:
            self.clicked=False

        #drawbutton on screen
        surface.blit(self.image, (self.rect.x, self.rect.y))

        return action

    def draw2(self,surface):
        surface.blit(self.image,(self.rect.x,self.rect.y))

def draw_b(text,font,text_col,x,y):
    img=font.render(text,True,text_col)
    window.blit(img,(x,y))

#load buttons images
start_img=pygame.image.load("assets//images//start_btn.png").convert_alpha()
start_img=pygame.transform.scale(start_img,((418.5/2),(189/2)))
options_img=pygame.image.load("assets//images//button_options.png").convert_alpha()
exit_img=pygame.image.load("assets//images//exit_btn.png").convert_alpha()
exit_img=pygame.transform.scale(exit_img,((360/2),(189/2)))
#quit_img=pygame.image.load("button_quit.png").convert_alpha()
#audio_img=pygame.image.load("button_audio.png").convert_alpha()
#video_img=pygame.image.load("button_video.png").convert_alpha()
back_img=pygame.image.load("assets//images//button_back.png").convert_alpha()

Blue_img=pygame.image.load("assets//images//Blue_k.png").convert_alpha()
Blue_img=pygame.transform.scale(Blue_img,((1612/8),(676/10)))

Yellow_img=pygame.image.load("assets//images//Yellow_k.png").convert_alpha()
Yellow_img=pygame.transform.scale(Yellow_img,((1610/8),(677/10)))

Green_img=pygame.image.load("assets//images//Green_k.png").convert_alpha()
Green_img=pygame.transform.scale(Green_img,((1611/8),(676/10)))

Pink_img=pygame.image.load("assets//images//Pink_k.png").convert_alpha()
Pink_img=pygame.transform.scale(Pink_img,((1609/8),(676/10)))

resume_img=pygame.image.load("assets//images//resume_b.png").convert_alpha()
resume_img=pygame.transform.scale(resume_img,((676/3),(225/(5/2))))

Back_img=pygame.image.load("assets//images//Back_b.png").convert_alpha()
Back_img=pygame.transform.scale(Back_img,((435/2),(131/(2))))

Audio_img=pygame.image.load("assets//images//Audio_b.png").convert_alpha()
Audio_img=pygame.transform.scale(Audio_img,((546/2),(133/(2))))

Character_img=pygame.image.load("assets//images//Character_b.png").convert_alpha()
Character_img=pygame.transform.scale(Character_img,((676/2),(133/(2))))

Background_img=pygame.image.load("assets//images//Background_b.png").convert_alpha()
Background_img=pygame.transform.scale(Background_img,((698/2),(131/(2))))

VIRTUAL_img=pygame.image.load("assets//images//Virtual_m.png").convert_alpha()
VIRTUAL_img=pygame.transform.scale(VIRTUAL_img,((594/2),(130/(2))))

FROG_img=pygame.image.load("assets//images//Frog_m.png").convert_alpha()
FROG_img=pygame.transform.scale(FROG_img,((600/2),(133/(2))))

MASK_img=pygame.image.load("assets//images//Mask_m.png").convert_alpha()
MASK_img=pygame.transform.scale(MASK_img,((601/2),(135/(2))))

PINK_img=pygame.image.load("assets//images//Pink_m.png").convert_alpha()
PINK_img=pygame.transform.scale(PINK_img,((598/2),(135/(2))))

info_img=pygame.image.load("assets//images//button_info.png").convert_alpha()
info_img=pygame.transform.scale(info_img,((512/8),(512/8)))

Off_img=pygame.image.load("assets//images//Off_b1.png").convert_alpha()
Off_img=pygame.transform.scale(Off_img,((512/5),(512/5)))

On_img=pygame.image.load("assets//images//On_b1.png").convert_alpha()
On_img=pygame.transform.scale(On_img,((512/5),(512/5)))

Start_img=pygame.image.load("assets//images//Start_b.png").convert_alpha()
Start_img=pygame.transform.scale(Start_img,((512//8),(512//8)))

#create button instances
start_button=Button(1200,300,start_img,1)
options_button=Button(1200,500,options_img,1)
exit_button=Button(1200,700,exit_img,1)
#quit_button=Button(1200,700,quit_img,1)
#audio_button=Button(1000,300,audio_img,1)
#video_button=Button(1000,500,video_img,1)
back_button=Button(1000,700,back_img,1)
Blue_button=Button(1100,200,Blue_img,1)
Yellow_button=Button(1100,300,Yellow_img,1)
Green_button=Button(1100,400,Green_img,1)
Pink_button=Button(1100,500,Pink_img,1)
Off_button=Button(1100,400,Off_img,1)
On_button=Button(1100,400,On_img,1)
resume_button=Button(1200,300,resume_img,1)
Back_button=Button(1000,700,Back_img,1)
Audio_button=Button(1000,250,Audio_img,1)
Character_button=Button(1000,400,Character_img,1)
Background_button=Button(1000,550,Background_img,1)
VIRTUAL_button=Button(1000,200,VIRTUAL_img,1)
FROG_button=Button(1000,300,FROG_img,1)
MASK_button=Button(1000,400,MASK_img,1)
PINK_button=Button(1000,500,PINK_img,1)
Info_button=Button(1530,0,info_img,1)

def start_back():
    with open("assets//images//y_score.txt","w") as f:
        f.write(str(854))

    Exit_g=False
    time1=0
    global e

    while not Exit_g:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                Exit_g=True

        background1=pygame.image.load("assets//images//logo.png")
        background1=pygame.transform.scale(background1,
            (1650,950)).convert_alpha()
        window.blit(background1,(0,0))
        pygame.display.update()
        if e==0:
            time.sleep(2)
            e=1
            start_back1()
            Exit_g=True
        clock.tick(30)
    pygame.quit()
    sys.exit()



def start_back1():
    global score
    Exit_g=False
    game_pause=False
    global c
    #c=0

    while not Exit_g:
        window.fill((230,250,200))

        if not game_pause:
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    Exit_g=True
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE:
                        Exit_g=True

            if start_button.draw(window):
                time.sleep(0.2)
                interval()
                Exit_g=True
            if options_button.draw(window):
                options()
                Exit_g=True
            if exit_button.draw(window):
                Exit_g=True

            if Info_button.draw(window):
                info_1()
                Exit_g=True

            background1=pygame.image.load("assets//images//Wallp.png")
            background1=pygame.transform.scale(background1,
                (500,500)).convert_alpha()
            window.blit(background1,(150,350))
            draw_b("KESHAV",font2,text_col1,5,915)

        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                Exit_g=True

        draw_b("GO UP",font1,text_col1,150,150)
        pygame.display.update()
        clock.tick(30)
    pygame.quit()
    sys.exit()

def audio():
    Exit_g=False
    global c
    while not Exit_g:
        window.fill((230,250,200))
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                Exit_g=True
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    options()
                    Exit_g=True
                if event.key==pygame.K_m:
                    c=1
                if event.key==pygame.K_u:
                    c=0
        if c==0:
            if On_button.draw(window):
                c=1
        if c==1:
            if Off_button.draw(window):
                c=0
        if back_button.draw(window):
            options()
            Exit_g=True
        draw_b("Audio Settings",font3,text_col1,1000,300)
        draw_b("Press M for mute",font2,text_col1,200,400)
        draw_b("Press U for Unmute",font2,text_col1,200,500)
        draw_b("GO UP",font1,text_col1,150,150)
        pygame.display.update()
        clock.tick(60)
    pygame.quit()
    sys.exit()

def background():
    Exit_g=False
    while not Exit_g:
        window.fill((230,250,200))
        for event in pygame.event.get():
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    options()
                    Exit_g=True
        if back_button.draw(window):
            options()
            Exit_g=True
        if Blue_button.draw(window):
            with open("assets//images//Color_c.txt","w") as f:
                f.write("Blue")
            options()
            Exit_g=True
        if Yellow_button.draw(window):
            with open("assets//images//Color_c.txt","w") as f:
                f.write("Brown")
            options()
            Exit_g=True
        if Green_button.draw(window):
            with open("assets//images//Color_c.txt","w") as f:
                f.write("Green")
            options()
            Exit_g=True
        if Pink_button.draw(window):
            with open("assets//images//Color_c.txt","w") as f:
                f.write("Pink")
            options()
            Exit_g=True
        draw_b("GO UP",font1,text_col1,150,150)
        pygame.display.update()
        clock.tick(30)
    pygame.quit()
    sys.exit()

def character():
    Exit_g=False
    exit_state="back"
    while not Exit_g:
        window.fill((230,250,200))
        if exit_state=="back":
            for event in pygame.event.get():
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE:
                        options()
            if back_button.draw(window):
                options()
                Exit_g=True
            if VIRTUAL_button.draw(window):
                with open("assets//images//character.txt","w") as f:
                    f.write("VirtualGuy")
                exit_state="exit"
            if FROG_button.draw(window):
                with open("assets//images//character.txt","w") as f:
                    f.write("NinjaFrog")
                exit_state="exit"
            if MASK_button.draw(window):
                with open("assets//images//character.txt","w") as f:
                    f.write("MaskDude")
                exit_state="exit"
            if PINK_button.draw(window):
                with open("assets//images//character.txt","w") as f:
                    f.write("PinkMan")
                exit_state="exit"
        if exit_state=="exit":
            for event in pygame.event.get():
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE:
                        exit_state="back"
                    if event.key==pygame.K_RETURN:
                        Exit_g=True
            draw_b("NEED TO RESTART THE GAME",font3,text_col3,400,400)
            draw_b("PRESS ENTER TO PROCEED",font3,text_col3,412,500)
            if back_button.draw(window):
                exit_state="back"
        draw_b("GO UP",font1,text_col1,150,150)
        pygame.display.update()
        clock.tick(30)
    pygame.quit()
    sys.exit()

def options():
    Exit_g=False
    while not Exit_g:
        window.fill((230,250,200))
        for event in pygame.event.get():
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    start_back1()
                if event.key==pygame.K_b:
                    background()
                if event.key==pygame.K_a:
                    audio()
                if event.key==pygame.K_c:
                    character()

        draw_b("Press A for Audio settings",font2,text_col1,200,400)
        draw_b("Press C for Character settings",font2,text_col1,200,500)
        draw_b("Press Esc to go Back",font2,text_col1,200,700)
        draw_b("Press B for Background settings",font2,text_col1,200,600)
        if Audio_button.draw2(window):
            audio()
        if Character_button.draw2(window):
            character()
        if Background_button.draw2(window):
            background()
        if Back_button.draw2(window):
            start_back1()
        draw_b("GO UP",font1,text_col1,150,150)
        pygame.display.update()
        clock.tick(30)
    pygame.quit()
    sys.exit()

def info_1():
    exit_g=False
    while not exit_g:
        window.fill((150,180,255))
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                exit_g=True
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    start_back1()
        if back_button.draw(window):
            start_back1()
        draw_b("~~HOLD LEFT RIGHT ARROW TO MOVE THE CHARACTER IN LEFT RIGHT DIRECTION",
            font2,text_col2,100,200)
        draw_b("~~TAP 1 TIME SPACE FOR SINGLE JUMP AND 2 TIME SPACE FOR DOUBLE JUMP",
            font2,text_col2,100,270)
        draw_b("~~ONCE YOU TOUCH THE BOTTOM OF SCREEN, YOU DIE",
            font2,text_col2,100,340)
        draw_b("~~REACH THE HIGHEST POINT TO WIN THE GAME",font2,text_col2,100,480)
        draw_b("~~THE SPEED OF BLOCK INCREASES AS YOU GO UP IN THE GAME",font2,text_col2,100,410)
        draw_b("KESHAV ",font3,text_col5,10,880)
        pygame.display.update()
        clock.tick(30)
    pygame.quit()
    sys.exit()

def out_1():
    exit_g=False
    while not exit_g:
        window.fill((220,230,255))
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                exit_g=True

            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_RETURN:
                    start_back1()
                    exit_g=True
                if event.key==pygame.K_ESCAPE:
                    exit_g=True

        with open("assets//images//y_score.txt","r") as f:
            y_score=float(f.read())
            y12_score=abs((y_score//100)-8)
            y13_score=str(y12_score)

        draw_b("GAME OVER",font1,text_col3,400,200)
        draw_b("SCORE :",font1,text_col3,400,500)
        draw_b(y13_score,font1,text_col3,1010,500)
        draw_b("Press Enter to Continue",font3,text_col2,440,820)

        pygame.display.update()
        clock.tick(30)
    pygame.quit()
    sys.exit()

def win_1():
    exit_game=False
    while not exit_game:
        window.fill((255,200,150))
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                exit_game=True
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    exit_game=True
                if event.key==pygame.K_RETURN:
                    start_back1()
                    exit_game=True

        win_image=pygame.image.load("assets//images//winning.png").convert_alpha()
        win_image=pygame.transform.scale(win_image,((512/3),(512/3)))
        window.blit(win_image,(720,150))
        draw_b("Congratulations",font1,text_col2,290,400)
        draw_b("You Reached the Highest Point in Game",font3,text_col2,300,600)
        draw_b("Press Enter to Continue",font2,text_col4,650,750)

        pygame.display.update()
        clock.tick(30)
    pygame.quit()
    sys.exit()

def interval():
    c=0
    exit_g=False
    while not exit_g:
        window.fill((255,200,150))
        clock.tick(30)
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                exit_g=True
        draw_b("REACH THE HIGHEST POINT TO WIN THE GAME",font3,text_col2,120,400)
        pygame.display.update()
        if c==0:
            time.sleep(0.1)
            c=1
            main()
            exit_g=True
    pygame.quit()
    sys.exit()

def flip(sprites):
    return[pygame.transform.flip(sprite,True,False) for sprite in sprites]

#Load the Character
def load_sprite_sheets(dir1,dir2,width,height,direction=False):
    path=join("assets",dir1,dir2)
    images=[f for f in listdir(path) if isfile(join(path,f))]

    all_sprites={}

    for image in images:
        sprite_sheet=pygame.image.load(join(path,image)).convert_alpha()

        sprites=[]
        for i in range(sprite_sheet.get_width()//width):
            surface=pygame.Surface((width,height),pygame.SRCALPHA,32)
            rect=pygame.Rect(i*width,0,width,height)
            surface.blit(sprite_sheet,(0,0),rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png","")+"_right"]=sprites
            all_sprites[image.replace(".png","")+"_left"]=flip(sprites)
        else:
            all_sprites[image.replace(".png","")]=sprites
    return all_sprites


#design the charcter and movement
class Player(pygame.sprite.Sprite):
    with open("assets//images//character.txt","r") as f:
        cc=f.read()
    color=(255,0,0)
    GRAVITY=1
    ANIMATON_DELAY=2
    SPRITES=load_sprite_sheets("MainCharacters",(cc+".chr"),32,32,True)

    def __init__(self,x,y,width,height):
        super().__init__()
        self.rect=pygame.Rect(x,y,width,height)
        self.x_vel=0
        self.y_vel=0
        self.mask=None
        self.direction="left"
        self.animation_count=0
        self.fall_count=0
        self.jump_count=0
        self.hit=False
        self.hit_count=0

#Jump the player and jump_count is how many times you click jump buttton
    def jump(self):
        self.y_vel=-self.GRAVITY*8
        self.animation_count=0
        self.jump_count+=1
        if self.jump_count==1:
            self.fall_count=0

    def move(self,dx,dy):
        self.rect.x+=dx
        self.rect.y+=dy
        global y1_score
        y1_score=self.rect.y
        with open("assets//images//y_score.txt","w") as f:
            f.write(str(y1_score))

#hit to fire trap animation
    def make_hit(self):
        self.hit=True
        self.hit_count=0

    def move_left(self,vel):
        if self.rect.x>-190:
            self.x_vel=-vel
            if self.direction!= "left":
                self.direction="left"
                self.animation_count=0

    def move_right(self,vel):
        if self.rect.x<1600:
            self.x_vel=vel
            if self.direction!= "right":
                self.direction="right"
                self.animation_count=0

#Gravity
    def loop(self,fps):
        self.y_vel+=min(1,(self.fall_count/fps)*self.GRAVITY)
        self.move(self.x_vel,self.y_vel)

        #hit command
        if self.hit:
            self.hit_count+=1
        if self.hit_count>fps*2:
            self.hit=False
            self.hit_count=0

        self.fall_count+=1
        self.update_sprite()

#what happen when player on object
    def landed(self):
        self.fall_count=0
        self.y_vel=0
        self.jump_count=0

#what happen when player hit the object form bottom,hit head on object
    def hit_head(self):
        self.count=0
        self.y_vel*=-1

#ANIMATION adding in Game of differnt action
    def update_sprite(self):
        sprite_sheet="idle"

        #Hit Fire
        if self.hit:
            sprite_sheet="hit"

        if self.y_vel<0:
            if self.jump_count==1:
                sprite_sheet="jump"
            elif self.jump_count==2:
                sprite_sheet="double_jump"
                self.animation_count+=2
        elif self.y_vel>self.GRAVITY*2:
            sprite_sheet="fall"

        if self.x_vel !=0 and 0<=self.y_vel<(self.GRAVITY*2):
            sprite_sheet="run"

        sprite_sheet_name=sprite_sheet+"_"+self.direction
        sprites=self.SPRITES[sprite_sheet_name]
        sprite_index=(self.animation_count//self.ANIMATON_DELAY)%len(sprites)
        self.sprite=sprites[sprite_index]
        self.animation_count+=1
        self.update()

#update the surface rectangle according the charcter size
    def update(self):
        self.rect=self.sprite.get_rect(topleft=(self.rect.x,self.rect.y))
        self.mask=pygame.mask.from_surface(self.sprite)

    def draw(self,win,offset_x,offset_y):
        win.blit(self.sprite,(self.rect.x-offset_x,self.rect.y-offset_y))

#adding object
class Object(pygame.sprite.Sprite):
    def __init__(self,x,y,width,height,name=None):
        super().__init__()
        self.rect=pygame.Rect(x,y,width,height)
        self.image=pygame.Surface((width,height),pygame.SRCALPHA)
        self.width=width
        self.height=height
        self.name=name

    def draw(self,win,offset_x,offset_y):
        win.blit(self.image,(self.rect.x-offset_x,self.rect.y-offset_y))

class Block(Object):
    def __init__(self,x,y,sizex,sizey,x1,y1):
        super().__init__(x,y,sizex,sizey)
        block=get_block(sizex,sizey,x1,y1)
        self.image.blit(block,(0,0))
        self.mask=pygame.mask.from_surface(self.image)

#adding traps
class Fire(Object):
    Animation_Delay=3
    def __init__(self,x,y,width,height):
        super().__init__(x,y,width,height,"fire")
        self.fire=load_sprite_sheets("Traps","Fire",width,height)
        self.image=self.fire["off"][0]
        self.mask=pygame.mask.from_surface(self.image)
        self.animation_count=0
        self.animation_name="off"

    def on(self):
        self.animation_name="on"

    def off(self):
        self.animation_name="off"

    def loop(self):
        sprites=self.fire[self.animation_name]
        sprite_index=(self.animation_count//self.Animation_Delay)%len(sprites)
        self.image=sprites[sprite_index]
        self.animation_count+=1

        self.rect=self.image.get_rect(topleft=(self.rect.x,self.rect.y))
        self.mask=pygame.mask.from_surface(self.image)

        #this help to not increase the animation count at very high value
        if self.animation_count//self.Animation_Delay>len(sprites):
            self.animation_count=0

# Give image and list of tiles
def get_background(name):
    image=pygame.image.load(join("assets","Background",name))
    _,_,width,height=image.get_rect()
    tiles=[]

    for i in range(WIDTH//width+1):
        for j in range(HEIGHT//height+1):
            pos=[i*width,j*height]
            tiles.append(pos)
    return tiles,image

#Getting block from png
def get_block(sizex,sizey,x1,y1):
    path=join("assets","Terrain","Terrain.png")
    image=pygame.image.load(path).convert_alpha()
#creating a surface to append the image
    surface=pygame.Surface((sizex,sizey),pygame.SRCALPHA,32)
#coordinates the smaller block in the image
    rect=pygame.Rect(x1,y1,sizex,sizey)
#add that smaller block on the top of the surface
    surface.blit(image,(0,0),rect)
    return pygame.transform.scale2x(surface)

#Take item and draw it on window screen
class Item(pygame.sprite.Sprite):
    def __init__(self,x,y,width,height,name=None):
        super().__init__()
        self.rect=pygame.Rect(x,y,width,height)
        self.image=pygame.Surface((width,height),pygame.SRCALPHA)
        item1=get_item(128)
        self.image.blit(item1,(0,0))
        self.width=width
        self.height=height
        self.name=name

    def draw(self,win,offset_x,offset_y):
        win.blit(self.image,(self.rect.x-offset_x,self.rect.y-offset_y))

#Give the item by extracting it from image
def get_item(size):
    surface=pygame.Surface((size,size),pygame.SRCALPHA)
    rect=pygame.Rect(0,0,size,size)
    surface.blit(Start_img,(0,0),rect)
    return pygame.transform.scale2x(surface)

#draw the bckground
def draw(window,background,bg_image,player,objects,offset_x,offset_y,item_x1):
    for tile in background:
        window.blit(bg_image,tile)

    for obj in objects:
        obj.draw(window,offset_x,offset_y)

    item_x1.draw(window,offset_x,offset_y)

    player.draw(window,offset_x,offset_y)
    pygame.display.update()

#collision between player and object
def handle_vertical_collision(player,objects,dy):
    collided_objects=[]
    for obj in objects:
        if pygame.sprite.collide_mask(player,obj):
            if dy>0:
                player.rect.bottom=obj.rect.top
                player.landed()
            elif dy<0:
                player.rect.top=obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)
    return collided_objects

#collision in horizontal direction
def collide(player,objects,dx):
    player.move(dx,0)
    player.update()
    collided_object=None
    for obj in objects:
        if pygame.sprite.collide_mask(player,obj):
            collided_object=obj
            break

    player.move(-dx,0)
    player.update()
    return collided_object

#Handle movement
def handle_move(player,objects):
    #global life_1
    #life_1=2
    keys=pygame.key.get_pressed()

    player.x_vel=0
    collide_left=collide(player,objects,-player_vel*(3))
    collide_right=collide(player,objects,player_vel*(3))

    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not collide_left:
        player.move_left(player_vel)
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not collide_right:
        player.move_right(player_vel)

    vertical_collide = handle_vertical_collision(player,objects,player.y_vel)

    #It will check all the object which collides with our player
    to_check=[collide_left,collide_right,*vertical_collide]
    #If that object is fire this will work
    for obj in to_check:
        if obj and obj.name=="fire":
            if c==0:
                pygame.mixer.music.load("assets//images//over.wav")
                pygame.mixer.music.play()
            player.make_hit()
            time.sleep(0.2)
            out_1()

#Game loop
def main():
    global score
    global y_out
    global y1_score
    global d
    global speed_inc

    x_m=1
    y_out=900
    speed_inc=1.000

    fire_list=[]

    with open("assets//images//Color_c.txt","r") as f:
        a=f.read()
    exit_game=False
    background,bg_image=get_background(a+".png")
    block_size=96
    player=Player(300,850,50,50)
    fireyp6=[Fire((c_xaxis[(i)*3][6])+28,(a_yaxis[(i)*3])-62,16,32)
             for i in range(8,19,2)]

    fireyp7=[Fire((c_xaxis[(i)*2][7])+28,(a_yaxis[(i)*2])-62,16,32)
             for i in range(10,30,2)]

    fireyp77=[Fire((c_xaxis[(i)*3][7])+28,(a_yaxis[(i)*3])-62,16,32)
             for i in range(7,20,2)]

    fireyp66=[Fire((c_xaxis[(i)*3][6])+28,(a_yaxis[(i)*3])-62,16,32)
             for i in range(8,20,3)]

    fireyp8=[Fire((c_xaxis[(i)*3][8])+28,(a_yaxis[(i)*3])-62,16,32)
             for i in range(7,15,3)]

    fireg1=[Fire((c_xaxis[(i)*2][1])+28,(a_yaxis[(i)*2])-62,16,32)
            for i in range(1,10,2)]

    fireg2=[Fire((c_xaxis[(i)*2][2])+28,(a_yaxis[(i)*2])-62,16,32)
            for i in range(2,10,2)]

    fireg3=[Fire((c_xaxis[(i)*3][3])+28,(a_yaxis[(i)*3])-62,16,32)
            for i in range(1,6,2)]

    fireg4=[Fire((c_xaxis[(i)*2][0])+28,(a_yaxis[(i)*2])-62,16,32)
            for i in range(2,10,3)]

    fireg5=[Fire((c_xaxis[(i)*2][4])+28,(a_yaxis[(i)*2])-62,16,32)
            for i in range(1,10,3)]

    #fire_b=[Fire((c_xaxis[(i)*3][])+28)]

    fire_all=[*fireyp6,*fireyp7,*fireyp77,*fireg1,*fireg2,*fireg3,*fireyp66,
       *fireyp8,*fireg4,*fireg5]
    for obj in fire_all:
        obj.on()

    floor=[Block(i*block_size,HEIGHT-block_size,block_size,96,0,0)
            for i in range(-WIDTH//block_size,(WIDTH*2)//block_size)]

    Side1=[Block(0,side1_l[i],32,96,240,64) for i in range(400)]

    Side2=[Block(1618,side1_l[i],32,96,240,64) for i in range(400)]

    blocks_gx1=[Block(c_xaxis[i][0],a_yaxis[i],block_size,96,96,0)
                for i in range(0,20)]

    blocks_yx1=[Block(c_xaxis[i][5],a_yaxis[i],block_size,96,96,64)
                for i in range(20,40)]

    blocks_px1=[Block(c_xaxis[i][5],a_yaxis[i],block_size,96,96,128)
                for i in range(40,60)]

    blocks_sx1=[Block(c_xaxis[i][9],a_yaxis[i],block_size,96,0,128)
                for i in range(60,80)]

    blocks_bx1=[Block(c_xaxis[i][9],a_yaxis[i],64,64,320,64)
                for i in range(80,105)]

    blocks_spx1=[Block(c_xaxis[i][5],a_yaxis[i],96,32,192,64)
                for i in range(105,120)]

    blocks_spx11=[Block(c_xaxis[i][9],a_yaxis[i],96,32,192,64)
                for i in range(120,130)]

    blocks_slimx1=[Block(c_xaxis[i][5],a_yaxis[i],100,16,270,0)
                for i in range(130,150)]

    blocks_gx2=[Block(c_xaxis[i][1],a_yaxis[i],block_size,96,96,0)
                for i in range(0,20)]

    blocks_yx2=[Block(c_xaxis[i][6],a_yaxis[i],block_size,96,96,64)
                for i in range(20,40)]

    blocks_px2=[Block(c_xaxis[i][6],a_yaxis[i],block_size,96,96,128)
                for i in range(40,60)]

    blocks_sx2=[Block(c_xaxis[i][10],a_yaxis[i],block_size,96,0,128)
                for i in range(60,80)]

    blocks_bx2=[Block(c_xaxis[i][10],a_yaxis[i],64,64,320,64)
                for i in range(80,105)]

    blocks_spx2=[Block(c_xaxis[i][6],a_yaxis[i],96,32,192,64)
                for i in range(105,120)]

    blocks_spx22=[Block(c_xaxis[i][10],a_yaxis[i],96,32,192,64)
                for i in range(120,130)]

    blocks_slimx2=[Block(c_xaxis[i][6],a_yaxis[i],100,16,270,0)
                for i in range(130,150)]

    blocks_gx3=[Block(c_xaxis[i][2],a_yaxis[i],block_size,96,96,0)
                for i in range(0,20)]

    blocks_yx3=[Block(c_xaxis[i][7],a_yaxis[i],block_size,96,96,64)
                for i in range(20,40)]

    blocks_px3=[Block(c_xaxis[i][7],a_yaxis[i],block_size,96,96,128)
                for i in range(40,60)]

    blocks_sx3=[Block(c_xaxis[i][11],a_yaxis[i],block_size,96,0,128)
                for i in range(60,80)]

    blocks_bx3=[Block(c_xaxis[i][11],a_yaxis[i],64,64,320,64)
                for i in range(80,105)]

    blocks_spx3=[Block(c_xaxis[i][7],a_yaxis[i],96,32,192,64)
                for i in range(105,120)]

    blocks_spx33=[Block(c_xaxis[i][11],a_yaxis[i],96,32,192,64)
                for i in range(120,130)]

    blocks_slimx3=[Block(c_xaxis[i][7],a_yaxis[i],100,16,270,0)
                for i in range(130,150)]

    blocks_gx4=[Block(c_xaxis[i][3],a_yaxis[i],block_size,96,96,0)
                for i in range(0,20)]

    blocks_yx4=[Block(c_xaxis[i][8],a_yaxis[i],block_size,96,96,64)
                for i in range(20,40)]

    blocks_px4=[Block(c_xaxis[i][8],a_yaxis[i],block_size,96,96,128)
                for i in range(40,60)]

    #blocks_sx4=[Block(c_xaxis[i][8],a_yaxis[i],block_size,96,0,128)
                #for i in range(100,135)]

    blocks_spx4=[Block(c_xaxis[i][8],a_yaxis[i],96,32,192,64)
                for i in range(105,120)]

    blocks_slimx4=[Block(c_xaxis[i][8],a_yaxis[i],100,16,270,0)
                for i in range(130,150)]

    blocks_gx5=[Block(c_xaxis[i][4],a_yaxis[i],block_size,96,96,0)
                for i in range(0,20)]

    #blocks_yx5=[Block(c_xaxis[i][4],a_yaxis[i],block_size,96,96,64)
                #for i in range(30,65)]

    #blocks_px5=[Block(c_xaxis[i][4],a_yaxis[i],block_size,96,96,128)
                #for i in range(65,100)]

    item_x1=Item(100,758,128,97)

    objects=[*floor,*blocks_gx1,*blocks_yx1,*blocks_px1,*blocks_sx1,*blocks_gx2,
        *blocks_yx2,*blocks_px2,*blocks_sx2,*blocks_gx3,*blocks_yx3,*blocks_px3,
        *blocks_sx3,*blocks_gx4,*blocks_yx4,*blocks_px4,*blocks_gx5,*Side1,
        *Side2,*blocks_spx1,*blocks_spx2,*blocks_spx3,*blocks_spx4,*blocks_bx1,
        *blocks_bx2,*blocks_bx3,*blocks_slimx1,*blocks_slimx2,*blocks_slimx3,
        *blocks_slimx4,*blocks_spx11,*blocks_spx22,*blocks_spx33,
        *fireyp6,*fireyp7,*fireyp77,*fireg1,*fireg2,*fireg3,*fireyp66,*fireyp8,*fireg4,
        *fireg5]

    offset_x=0
    offset_y=0
    scroll_area_width=200

    while not exit_game:
        clock.tick(fps)
        if player.rect.y<500:
            y_out-=2*speed_inc

        if y_out < player.rect.y:
            exit_game=True
            if c==0:
                pygame.mixer.music.load("assets//images//over.wav")
                pygame.mixer.music.play()
            out_1()
        '''if 44>=player.rect.x:
            exit_game=True
            out_1()
        if 1540<=player.rect.x:
            exit_game=True
            out_1()'''

        if player.rect.y<(-28020): #37600 #28000
            exit_game=True
            if c==0:
                pygame.mixer.music.load("assets//images//Win_1.mp3")
                pygame.mixer.music.play()
            win_1()

        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                exit_game=True
                break
            #command for Jump
            if event.type==pygame.KEYDOWN:
                if (event.key==pygame.K_SPACE or event.key==pygame.K_w) and player.jump_count<2:
                    player.jump()

                    if player.jump_count==1 and c==0:
                        pygame.mixer.music.load('assets//images//Jump_s.mp3')
                        pygame.mixer.music.play()

                    if player.jump_count==2:
                        speed_inc+=0.005

                if event.key==pygame.K_ESCAPE:
                    d=0
                    exit_game=True
                    #start_back1()

        player.loop(fps)
        for obj in fire_all:
            obj.loop()
        handle_move(player,objects)
        draw(window,background,bg_image,player,objects,
            offset_x,offset_y,item_x1)

        if ((player.rect.right-offset_x>=WIDTH - scroll_area_width and
                 player.x_vel>0) or (player.rect.left-offset_x<=
                 scroll_area_width and player.x_vel<0)):
            offset_x += 0 #player.x_vel
        if player.rect.y<500:
            offset_y-=2*speed_inc


        pygame.display.update()
    pygame.quit()
    sys.exit()

start_back()