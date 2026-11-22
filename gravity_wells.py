#!/usr/bin/env python3
"""
Black Holes & Planets — A physics-based puzzle shooter game.
Navigate your probe through gravitational fields of black holes and planets
to reach the beacon and complete all 30 levels across 5 sectors.

Features:
  - 30 built-in levels across 5 themed sectors
  - Black Holes (attractors), Planets (repulsors), Wormholes, Slingshots, Asteroids, Comets
  - Moving / pulsing black holes
  - Full Level Editor with save/load (JSON) + undo/redo
  - Procedural level generator + Endless mode
  - Trajectory preview while aiming
  - Gravity field visualization overlay
  - Speed-run timer with best times
  - Screen shake effects

Controls (Playing):
  Click & drag from probe to aim — release to fire
  R = Restart | N = Skip | F = Toggle gravity field | ESC = Menu

Controls (Editor):
  1-9 = Select tool | Left-click = Place | Right-click = Delete
  Scroll = Adjust mass | Shift+Drag = Resize obstacle/asteroid
  Right-drag slingshot = Set direction | G = Generate | T = Test play
  Ctrl+S = Save | Ctrl+L = Load | Ctrl+N = New | Ctrl+Z/Y = Undo/Redo | ESC = Menu
"""

import pygame, sys, math, random, json, os

pygame.init()

WIDTH, HEIGHT = 1200, 750
FPS = 60
EDITOR_PANEL_W = 160
PLAY_AREA_W = WIDTH - EDITOR_PANEL_W
LEVELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.path.abspath("."), "custom_levels")

# ─── Colors ───
BLACK        = (0, 0, 0)
WHITE        = (255, 255, 255)
DARK_BG      = (5, 5, 15)
LAUNCHER_COL = (0, 200, 255)
TARGET_COL   = (50, 255, 100)
TARGET_GLOW  = (30, 180, 70)
BULLET_COL   = (255, 220, 80)
TRAIL_COL    = (255, 180, 50)
OBSTACLE_COL = (60, 55, 50)
OBSTACLE_EDGE= (100, 90, 80)
TEXT_COL     = (200, 210, 230)
DIM_TEXT     = (100, 110, 130)
SUCCESS_COL  = (80, 255, 140)
FAIL_COL     = (255, 80, 80)
POWER_LOW    = (80, 255, 120)
POWER_HIGH   = (255, 60, 60)
PORTAL_COL   = (0, 255, 200)
BUTTON_COL   = (40, 50, 80)
BUTTON_HOVER = (60, 75, 120)
BUTTON_EDGE  = (100, 120, 180)
STAR_COL     = (200, 200, 220)
BOOSTER_COL  = (255, 160, 0)
BREAKABLE_COL= (140, 110, 70)
BREAKABLE_EDGE=(190, 160, 100)
BONUS_COL    = (255, 215, 0)
BH_CORE      = (5, 0, 15)
BH_ACCRETION = (160, 80, 255)
BH_RING1     = (100, 50, 200)
BH_RING2     = (200, 120, 255)
BH_EVENT_H   = (80, 40, 160)
ED_PANEL_BG  = (15, 15, 30)
ED_TOOL_BG   = (30, 30, 55)
ED_TOOL_SEL  = (60, 50, 100)
ED_TOOL_HOV  = (45, 40, 75)

PLANET_PALETTES = [
    {"body": (180, 100, 60), "atmo": (220, 150, 80), "ring": (200, 130, 70)},
    {"body": (60, 120, 200), "atmo": (80, 160, 240), "ring": (100, 150, 220)},
    {"body": (200, 180, 100), "atmo": (240, 220, 140), "ring": (220, 200, 120)},
    {"body": (80, 180, 120), "atmo": (100, 220, 150), "ring": (90, 200, 140)},
    {"body": (200, 80, 80),  "atmo": (240, 120, 100), "ring": (220, 100, 90)},
    {"body": (160, 130, 200), "atmo": (190, 160, 240), "ring": (175, 145, 220)},
]

# ─── Physics ───
G_CONSTANT      = 800.0
MAX_POWER       = 700.0
MIN_POWER       = 50.0
PROJECTILE_MASS = 1.0
PROJECTILE_RAD  = 5
WELL_MIN_DIST   = 25.0
BOUNCE_DAMPING  = 0.6
TARGET_RADIUS   = 25
SUB_STEPS       = 4
BOOSTER_FORCE   = 600.0
TRAJECTORY_STEPS= 150
TRAJECTORY_DT   = 0.033
SHAKE_DECAY     = 8.0
MAX_SHAKE       = 12.0

# ─── Sector Themes ───
SECTORS = [
    {"name": "Outer Rim",       "bg": (5, 5, 18),   "grid": (12, 12, 30),
     "nebula_colors": [(25,15,60),(15,25,70),(10,10,45)],
     "star_colors": [(200,200,240),(180,180,255),(220,220,255),(150,150,200)], "star_density": 1.0},
    {"name": "Crimson Drift",   "bg": (15, 5, 10),  "grid": (28, 12, 18),
     "nebula_colors": [(70,15,30),(90,10,40),(50,8,25)],
     "star_colors": [(255,200,200),(255,180,180),(240,160,180),(200,150,160)], "star_density": 1.2},
    {"name": "Emerald Expanse", "bg": (4, 14, 10),  "grid": (12, 25, 18),
     "nebula_colors": [(12,50,35),(8,65,45),(18,40,30)],
     "star_colors": [(180,255,200),(160,240,180),(200,255,210),(150,220,170)], "star_density": 1.1},
    {"name": "Solar Corridor",  "bg": (18, 12, 4),  "grid": (30, 22, 12),
     "nebula_colors": [(70,45,8),(90,55,12),(50,30,6)],
     "star_colors": [(255,230,180),(255,220,150),(255,240,200),(240,200,140)], "star_density": 0.9},
    {"name": "Event Horizon",   "bg": (2, 2, 8),    "grid": (8, 8, 16),
     "nebula_colors": [(15,8,40),(8,4,30),(25,12,50)],
     "star_colors": [(220,220,255),(200,200,240),(240,240,255),(180,180,220)], "star_density": 1.5},
]

def sector_for_level(level_idx):
    return SECTORS[min(level_idx // 6, len(SECTORS) - 1)]

# ─── Vector Helpers ───
def vnorm(v):
    l = math.hypot(v[0], v[1])
    return (v[0]/l, v[1]/l) if l > 1e-8 else (0.0, 0.0)
def vlen(v): return math.hypot(v[0], v[1])
def clamp(v, lo, hi): return max(lo, min(hi, v))
def lerp_color(c1, c2, t):
    t = clamp(t, 0, 1)
    return (int(c1[0]+(c2[0]-c1[0])*t), int(c1[1]+(c2[1]-c1[1])*t), int(c1[2]+(c2[2]-c1[2])*t))
def circle_rect_hit(cx, cy, cr, rect):
    rx,ry,rw,rh = rect
    nx, ny = clamp(cx,rx,rx+rw), clamp(cy,ry,ry+rh)
    return (cx-nx)**2+(cy-ny)**2 < cr*cr
def point_in_rect(px, py, rect):
    return rect[0]<=px<=rect[0]+rect[2] and rect[1]<=py<=rect[1]+rect[3]


# ═══════════════════════════════════════════════
# Starry Background
# ═══════════════════════════════════════════════
class StarryBackground:
    def __init__(self):
        self._cache = {}
    def get(self, idx):
        if idx not in self._cache: self._build(idx)
        return self._cache[idx]
    def _build(self, idx):
        s = SECTORS[idx]
        surf = pygame.Surface((WIDTH, HEIGHT)); surf.fill(s["bg"])
        neb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for _ in range(8):
            nx,ny,nr = random.randint(0,WIDTH), random.randint(0,HEIGHT), random.randint(120,350)
            bc = random.choice(s["nebula_colors"])
            for layer in range(nr, 0, -6):
                pygame.draw.circle(neb, (*bc, max(2,int(18*(layer/nr)))), (nx,ny), layer)
        surf.blit(neb, (0,0))
        stars = []
        for _ in range(int(120*s["star_density"])):
            sx,sy = random.randint(0,WIDTH), random.randint(0,HEIGHT)
            br = random.uniform(0.2,1.0)
            sz = 1 if br<0.7 else (2 if br<0.95 else 3)
            col = random.choice(s["star_colors"])
            ts,tp = random.uniform(1.0,4.0), random.uniform(0,math.pi*2)
            stars.append((sx,sy,br,sz,col,ts,tp))
            dim = tuple(max(0,int(c*br*0.5)) for c in col)
            if sz<=1: surf.set_at((sx,sy),dim)
            else: pygame.draw.circle(surf, dim, (sx,sy), sz-1)
        self._cache[idx] = {"surface":surf,"stars":stars,"sector":s}
    def draw(self, surface, idx, time):
        d = self.get(idx); surface.blit(d["surface"],(0,0))
        s = d["sector"]
        for x in range(0,WIDTH,60): pygame.draw.line(surface,s["grid"],(x,0),(x,HEIGHT))
        for y in range(0,HEIGHT,60): pygame.draw.line(surface,s["grid"],(0,y),(WIDTH,y))
        for sx,sy,br,sz,col,sp,ph in d["stars"]:
            tw = 0.4+0.6*(0.5+0.5*math.sin(time*sp+ph)); b=br*tw
            if b<0.35: continue
            c = tuple(min(255,int(v*b)) for v in col)
            if sz<=1: surface.set_at((sx,sy),c)
            else:
                pygame.draw.circle(surface,c,(sx,sy),sz)
                if b>0.85 and sz>=2:
                    fc = tuple(min(255,v//2) for v in c)
                    pygame.draw.line(surface,fc,(sx-4,sy),(sx+4,sy))
                    pygame.draw.line(surface,fc,(sx,sy-4),(sx,sy+4))


# ═══════════════════════════════════════════════
# Game Objects
# ═══════════════════════════════════════════════
class BlackHole:
    def __init__(self, x, y, mass, polarity=1, moving=None, pulsing=None, planet_style=0):
        self.base_x=x; self.base_y=y; self.x=x; self.y=y
        self.mass=mass; self.polarity=polarity
        self.base_radius=int(12+abs(mass)*2)
        self.pulse_phase=random.uniform(0,math.pi*2)
        self.ring_anim=0.0; self.disk_angle=random.uniform(0,math.pi*2)
        self.moving=moving; self.move_angle=random.uniform(0,math.pi*2)
        self.pulsing=pulsing; self.pulse_timer=0.0; self.active=True
        self.planet_palette=PLANET_PALETTES[planet_style%len(PLANET_PALETTES)]
        self.planet_ring_tilt=random.uniform(0.2,0.6)
        self.planet_style=planet_style

    def _update_position(self, dt):
        if not self.moving: self.x,self.y=self.base_x,self.base_y; return
        m=self.moving
        if m["type"]=="orbit":
            self.move_angle+=m["speed"]*dt
            self.x=m["cx"]+math.cos(self.move_angle)*m["radius"]
            self.y=m["cy"]+math.sin(self.move_angle)*m["radius"]
        elif m["type"]=="oscillate":
            self.move_angle+=m["speed"]*dt
            off=math.sin(self.move_angle)*m["radius"]
            if m["axis"]=="x": self.x=self.base_x+off; self.y=self.base_y
            else: self.x=self.base_x; self.y=self.base_y+off

    def _update_pulsing(self, dt):
        if not self.pulsing: self.active=True; return
        self.pulse_timer+=dt; p=self.pulsing["period"]; f=self.pulsing["on_frac"]
        self.active=(self.pulse_timer%p)<p*f

    def force_on(self, px, py):
        if not self.active: return (0.0,0.0)
        dx,dy=self.x-px,self.y-py; dist=math.hypot(dx,dy)
        soft=max(dist,WELL_MIN_DIST)
        mag=min(G_CONSTANT*abs(self.mass)*PROJECTILE_MASS/(soft*soft),3000)
        if dist<1e-8: return (0.0,0.0)
        return (self.polarity*mag*dx/dist, self.polarity*mag*dy/dist)

    def update(self, dt):
        self._update_position(dt); self._update_pulsing(dt)
        self.pulse_phase+=dt*2.0; self.ring_anim+=dt*0.8; self.disk_angle+=dt*0.5

    def draw(self, surface):
        if not self.active and self.pulsing:
            ds=pygame.Surface((40,40),pygame.SRCALPHA)
            c=BH_EVENT_H if self.polarity==1 else (50,40,30)
            pygame.draw.circle(ds,(*c,40),(20,20),16); surface.blit(ds,(int(self.x-20),int(self.y-20)))
            pygame.draw.circle(surface,(50,30,60) if self.polarity==1 else (40,35,25),(int(self.x),int(self.y)),8,2)
            if self.pulsing:
                p=self.pulsing["period"]; f=self.pulsing["on_frac"]; fr=(self.pulse_timer%p)/p
                if fr>f: col=lerp_color((100,50,50),(200,80,80),(fr-f)/(1-f))
                else: col=(80,200,80)
                pygame.draw.circle(surface,col,(int(self.x),int(self.y)),self.base_radius+4,2)
            return
        if self.polarity==1: self._draw_bh(surface)
        else: self._draw_planet(surface)
        if self.moving:
            m=self.moving
            if m["type"]=="orbit": pygame.draw.circle(surface,(50,50,65),(int(m["cx"]),int(m["cy"])),int(m["radius"]),1)
            elif m["type"]=="oscillate":
                if m["axis"]=="x": pygame.draw.line(surface,(50,50,65),(int(self.base_x-m["radius"]),int(self.base_y)),(int(self.base_x+m["radius"]),int(self.base_y)),1)
                else: pygame.draw.line(surface,(50,50,65),(int(self.base_x),int(self.base_y-m["radius"])),(int(self.base_x),int(self.base_y+m["radius"])),1)

    def _draw_bh(self, surface):
        pulse=0.5+0.5*math.sin(self.pulse_phase); r=self.base_radius+int(pulse*3)
        for i in range(5,0,-1):
            ri=r+i*14; gs=pygame.Surface((ri*2,ri*2),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*BH_RING1,max(5,30-i*5)),(ri,ri),ri,2); surface.blit(gs,(int(self.x-ri),int(self.y-ri)))
        dw=r+18; dh=int(dw*0.35); ds=pygame.Surface((dw*2+4,dh*2+4),pygame.SRCALPHA)
        for la in range(3,0,-1):
            w2,h2=dw+la*4,dh+la*2; pygame.draw.ellipse(ds,(*BH_ACCRETION,int(40*pulse/la)),(dw+2-w2,dh+2-h2,w2*2,h2*2),2)
        pygame.draw.ellipse(ds,(*BH_ACCRETION,int(120*pulse)),(2,2,dw*2,dh*2),3)
        pygame.draw.ellipse(ds,(*BH_RING2,int(80*pulse)),(dw//2,dh//2,dw,dh),2)
        surface.blit(ds,(int(self.x-dw-2),int(self.y-dh-2)))
        pygame.draw.circle(surface,BH_EVENT_H,(int(self.x),int(self.y)),r+2,2)
        pygame.draw.circle(surface,BH_CORE,(int(self.x),int(self.y)),r)
        pygame.draw.circle(surface,(20,5,40),(int(self.x),int(self.y)),r,2)
        ip=0.3+0.7*abs(math.sin(self.pulse_phase*1.5))
        pygame.draw.circle(surface,lerp_color(BH_CORE,BH_RING2,0.3*ip),(int(self.x),int(self.y)),max(1,int(2*ip)))
        rr=int(r+(self.ring_anim%1.0)*45); ra=int(100*(1.0-(self.ring_anim%1.0)))
        rs=pygame.Surface((rr*2+4,rr*2+4),pygame.SRCALPHA)
        pygame.draw.circle(rs,(*BH_ACCRETION,ra),(rr+2,rr+2),rr,1); surface.blit(rs,(int(self.x-rr-2),int(self.y-rr-2)))
        fs=pygame.font.SysFont("consolas",12,bold=True)
        t=fs.render("BLACK HOLE",True,(160,120,220)); surface.blit(t,(int(self.x-t.get_width()//2),int(self.y+r+10)))

    def _draw_planet(self, surface):
        pal=self.planet_palette; pulse=0.5+0.5*math.sin(self.pulse_phase); r=self.base_radius+int(pulse*2)
        for i in range(4,0,-1):
            ri=r+i*10; gs=pygame.Surface((ri*2,ri*2),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*pal["atmo"],max(5,22-i*5)),(ri,ri),ri); surface.blit(gs,(int(self.x-ri),int(self.y-ri)))
        rw=r+14; rh=int(rw*self.planet_ring_tilt); rs=pygame.Surface((rw*2+4,rh*2+4),pygame.SRCALPHA)
        pygame.draw.ellipse(rs,(*pal["ring"],int(100*pulse)),(2,2,rw*2,rh*2),2); surface.blit(rs,(int(self.x-rw-2),int(self.y-rh-2)))
        pygame.draw.circle(surface,pal["body"],(int(self.x),int(self.y)),r)
        hr=max(3,r-4); hs=pygame.Surface((hr*2,hr*2),pygame.SRCALPHA)
        hc=lerp_color(pal["body"],WHITE,0.3); pygame.draw.circle(hs,(*hc,60),(hr-2,hr-2),hr)
        ms=pygame.Surface((hr*2,hr*2),pygame.SRCALPHA); pygame.draw.circle(ms,(255,255,255,255),(hr,hr),hr)
        hs.blit(ms,(0,0),special_flags=pygame.BLEND_RGBA_MIN); surface.blit(hs,(int(self.x-hr),int(self.y-hr)))
        pygame.draw.circle(surface,pal["atmo"],(int(self.x),int(self.y)),r,1)
        rr=int(r+(self.ring_anim%1.0)*35); ra=int(80*(1.0-(self.ring_anim%1.0)))
        rs2=pygame.Surface((rr*2+4,rr*2+4),pygame.SRCALPHA)
        pygame.draw.circle(rs2,(*pal["ring"],ra),(rr+2,rr+2),rr,1); surface.blit(rs2,(int(self.x-rr-2),int(self.y-rr-2)))
        fs=pygame.font.SysFont("consolas",12,bold=True)
        t=fs.render("PLANET",True,pal["atmo"]); surface.blit(t,(int(self.x-t.get_width()//2),int(self.y+r+10)))

    def to_dict(self):
        d = {"x":self.base_x,"y":self.base_y,"mass":self.mass,"polarity":self.polarity,"planet_style":self.planet_style}
        if self.moving: d["moving"]=self.moving
        if self.pulsing: d["pulsing"]=self.pulsing
        return d

class GravitySlingshot:
    def __init__(self, x, y, w, h, dx, dy, strength=BOOSTER_FORCE):
        self.rect=(x,y,w,h); self.dx,self.dy=vnorm((dx,dy)); self.strength=strength; self.pulse=random.uniform(0,math.pi*2)
    def applies_to(self, px, py): return point_in_rect(px,py,self.rect)
    def force_on(self): return (self.dx*self.strength, self.dy*self.strength)
    def update(self, dt): self.pulse+=dt*3.0
    def draw(self, surface):
        x,y,w,h=self.rect; p=0.6+0.4*math.sin(self.pulse)
        gs=pygame.Surface((w,h),pygame.SRCALPHA); gs.fill((*BOOSTER_COL,int(22*p))); surface.blit(gs,(x,y))
        pygame.draw.rect(surface,lerp_color((100,70,20),BOOSTER_COL,p),(x,y,w,h),2,border_radius=4)
        cx,cy=x+w//2,y+h//2; ax,ay=self.dx*20,self.dy*20; ex,ey=cx+ax,cy+ay
        pygame.draw.line(surface,BOOSTER_COL,(cx,cy),(int(ex),int(ey)),2)
        px2,py2=-self.dy,self.dx
        pygame.draw.polygon(surface,BOOSTER_COL,[(int(ex),int(ey)),(int(ex-self.dx*8+px2*5),int(ey-self.dy*8+py2*5)),(int(ex-self.dx*8-px2*5),int(ey-self.dy*8-py2*5))])
        fs=pygame.font.SysFont("consolas",11,bold=True); t=fs.render("SLINGSHOT",True,BOOSTER_COL); surface.blit(t,(cx-t.get_width()//2,y-14))
    def to_dict(self):
        return {"x":self.rect[0],"y":self.rect[1],"w":self.rect[2],"h":self.rect[3],"dx":self.dx,"dy":self.dy,"strength":self.strength}

class Asteroid:
    def __init__(self, x, y, w, h, hp=1):
        self.rect=(x,y,w,h); self.hp=hp; self.max_hp=hp; self.alive=True
    def hit(self): self.hp-=1; self.alive=self.hp>0; return self.alive
    def draw(self, surface):
        if not self.alive: return
        x,y,w,h=self.rect; df=self.hp/self.max_hp
        col=lerp_color((80,35,20),BREAKABLE_COL,df); edge=lerp_color((130,55,30),BREAKABLE_EDGE,df)
        pygame.draw.rect(surface,col,(x,y,w,h),border_radius=3); pygame.draw.rect(surface,edge,(x,y,w,h),2,border_radius=3)
        random.seed(int(x*100+y))
        for _ in range(6):
            dx,dy=random.randint(3,max(4,w-3)),random.randint(3,max(4,h-3))
            pygame.draw.circle(surface,lerp_color(col,(40,30,20),0.3),(x+dx,y+dy),random.randint(1,3))
        random.seed()
        if df<1.0:
            cx,cy=x+w//2,y+h//2; random.seed(int(x*200+y))
            for _ in range(int((1-df)*5)+1):
                ddx,ddy=random.randint(-w//2,w//2),random.randint(-h//2,h//2)
                pygame.draw.line(surface,(30,15,10),(cx,cy),(cx+ddx,cy+ddy),1)
            random.seed()
        fs=pygame.font.SysFont("consolas",10,bold=True); t=fs.render("ASTEROID",True,BREAKABLE_EDGE); surface.blit(t,(x+w//2-t.get_width()//2,y-12))
    def to_dict(self):
        return {"x":self.rect[0],"y":self.rect[1],"w":self.rect[2],"h":self.rect[3],"hp":self.max_hp}

class Comet:
    def __init__(self, x, y): self.x=x; self.y=y; self.collected=False; self.radius=12; self.phase=random.uniform(0,math.pi*2)
    def update(self, dt): self.phase+=dt*3.0
    def check_collect(self, px, py):
        if self.collected: return False
        if math.hypot(px-self.x,py-self.y)<self.radius+PROJECTILE_RAD: self.collected=True; return True
        return False
    def draw(self, surface):
        if self.collected: return
        bob=math.sin(self.phase)*4; y=self.y+bob; p=0.7+0.3*math.sin(self.phase*1.5)
        tl=int(20*p); ts=pygame.Surface((tl+10,14),pygame.SRCALPHA)
        for i in range(tl,0,-1):
            a=int(60*(i/tl)*p); c=lerp_color((200,150,50),BONUS_COL,i/tl)
            pygame.draw.circle(ts,(*c,a),(tl+5-i,7),max(1,3-i//7))
        surface.blit(ts,(int(self.x-tl-5),int(y-7)))
        for i in range(3,0,-1):
            r=self.radius+i*5; gs=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(gs,(255,215,0,int(20*p)),(r,r),r); surface.blit(gs,(int(self.x-r),int(y-r)))
        pygame.draw.circle(surface,lerp_color((180,140,40),BONUS_COL,p),(int(self.x),int(y)),self.radius-3)
        pygame.draw.circle(surface,(255,245,200),(int(self.x-2),int(y-2)),3)
    def to_dict(self): return {"x":self.x,"y":self.y}

class Wormhole:
    def __init__(self, x1, y1, x2, y2, cooldown=2.0):
        self.x1,self.y1=x1,y1; self.x2,self.y2=x2,y2; self.radius=22; self.cooldown=cooldown
        self.timer1=0.0; self.timer2=0.0; self.phase=random.uniform(0,math.pi*2)
    def update(self, dt):
        self.timer1=max(0,self.timer1-dt); self.timer2=max(0,self.timer2-dt); self.phase+=dt*3.0
    def check_teleport(self, proj):
        d1=math.hypot(proj.x-self.x1,proj.y-self.y1); d2=math.hypot(proj.x-self.x2,proj.y-self.y2)
        if d1<self.radius and self.timer1<=0: proj.x,proj.y=self.x2,self.y2; self.timer1=self.cooldown; self.timer2=self.cooldown; return True
        elif d2<self.radius and self.timer2<=0: proj.x,proj.y=self.x1,self.y1; self.timer1=self.cooldown; self.timer2=self.cooldown; return True
        return False
    def draw(self, surface):
        p=0.6+0.4*math.sin(self.phase)
        for x,y,timer in [(self.x1,self.y1,self.timer1),(self.x2,self.y2,self.timer2)]:
            for i in range(4,0,-1):
                r=self.radius+i*8; gs=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
                pygame.draw.circle(gs,(0,200,180,int(30*p) if timer<=0 else 10),(r,r),r); surface.blit(gs,(int(x-r),int(y-r)))
            col=PORTAL_COL if timer<=0 else (40,70,65)
            for ao in range(0,360,60):
                a1=math.radians(ao+self.phase*30); a2=math.radians(ao+30+self.phase*30)
                r1,r2=self.radius-4,self.radius+6
                pygame.draw.line(surface,col,(int(x+math.cos(a1)*r1),int(y+math.sin(a1)*r1)),(int(x+math.cos(a2)*r2),int(y+math.sin(a2)*r2)),1)
            pygame.draw.circle(surface,col,(int(x),int(y)),self.radius,3)
            ir=int(self.radius*0.4*p); pygame.draw.circle(surface,col,(int(x),int(y)),ir,2)
            pygame.draw.circle(surface,(5,15,15),(int(x),int(y)),max(2,ir-3))
        fs=pygame.font.SysFont("consolas",10,bold=True); t=fs.render("WORMHOLE",True,(0,180,160)); surface.blit(t,(int(self.x1-t.get_width()//2),int(self.y1+self.radius+6)))
    def to_dict(self): return {"x1":self.x1,"y1":self.y1,"x2":self.x2,"y2":self.y2,"cooldown":self.cooldown}

class Probe:
    def __init__(self, x, y, vx, vy):
        self.x=x; self.y=y; self.vx=vx; self.vy=vy; self.alive=True
        self.trail=[]; self.trail_max=120; self.age=0.0; self.stuck_timer=0.0
    def update(self, dt, wells, obstacles, asteroids, slingshots):
        self.age+=dt; sdt=dt/SUB_STEPS
        for _ in range(SUB_STEPS):
            fx,fy=0.0,0.0
            for w in wells: wfx,wfy=w.force_on(self.x,self.y); fx+=wfx; fy+=wfy
            for s in slingshots:
                if s.applies_to(self.x,self.y): sfx,sfy=s.force_on(); fx+=sfx; fy+=sfy
            self.vx+=fx*sdt; self.vy+=fy*sdt; self.x+=self.vx*sdt; self.y+=self.vy*sdt
            if self.x-PROJECTILE_RAD<0: self.x=PROJECTILE_RAD; self.vx=abs(self.vx)*BOUNCE_DAMPING
            elif self.x+PROJECTILE_RAD>WIDTH: self.x=WIDTH-PROJECTILE_RAD; self.vx=-abs(self.vx)*BOUNCE_DAMPING
            if self.y-PROJECTILE_RAD<0: self.y=PROJECTILE_RAD; self.vy=abs(self.vy)*BOUNCE_DAMPING
            elif self.y+PROJECTILE_RAD>HEIGHT: self.y=HEIGHT-PROJECTILE_RAD; self.vy=-abs(self.vy)*BOUNCE_DAMPING
            for obs in obstacles:
                if circle_rect_hit(self.x,self.y,PROJECTILE_RAD,obs): self._resolve_rect(obs)
            for ast in asteroids:
                if ast.alive and circle_rect_hit(self.x,self.y,PROJECTILE_RAD,ast.rect): self._resolve_rect(ast.rect); ast.hit()
        self.trail.append((self.x,self.y))
        if len(self.trail)>self.trail_max: self.trail.pop(0)
        speed=vlen((self.vx,self.vy))
        if speed<5: self.stuck_timer+=dt
        else: self.stuck_timer=0
        if self.stuck_timer>3.0 or self.age>25.0: self.alive=False

    def _resolve_rect(self, rect):
        rx,ry,rw,rh=rect; cx,cy=clamp(self.x,rx,rx+rw),clamp(self.y,ry,ry+rh)
        dx,dy=self.x-cx,self.y-cy; dist=math.hypot(dx,dy)
        if dist<1e-8:
            ds=[(self.x-rx,-1,0),(rx+rw-self.x,1,0),(self.y-ry,0,-1),(ry+rh-self.y,0,1)]
            ds.sort(key=lambda d:d[0]); _,nx,ny=ds[0]
            self.x+=nx*(PROJECTILE_RAD+2); self.y+=ny*(PROJECTILE_RAD+2)
            if nx: self.vx=nx*abs(self.vx)*BOUNCE_DAMPING
            if ny: self.vy=ny*abs(self.vy)*BOUNCE_DAMPING
        else:
            nx,ny=dx/dist,dy/dist; ov=PROJECTILE_RAD-dist
            self.x+=nx*ov*1.1; self.y+=ny*ov*1.1
            dot=self.vx*nx+self.vy*ny
            if dot<0: self.vx-=2*dot*nx*BOUNCE_DAMPING; self.vy-=2*dot*ny*BOUNCE_DAMPING

    def draw(self, surface):
        if len(self.trail)>1:
            for i in range(1,len(self.trail)):
                w=max(1,int(3*(i/len(self.trail)))); col=lerp_color((80,40,10),TRAIL_COL,i/len(self.trail))
                pygame.draw.line(surface,col,(int(self.trail[i-1][0]),int(self.trail[i-1][1])),(int(self.trail[i][0]),int(self.trail[i][1])),w)
        gs=pygame.Surface((30,30),pygame.SRCALPHA); pygame.draw.circle(gs,(255,220,80,60),(15,15),15)
        surface.blit(gs,(int(self.x-15),int(self.y-15)))
        pygame.draw.circle(surface,BULLET_COL,(int(self.x),int(self.y)),PROJECTILE_RAD+1)
        pygame.draw.circle(surface,WHITE,(int(self.x),int(self.y)),max(1,PROJECTILE_RAD-1))

class Particle:
    def __init__(self, x,y,vx,vy,life,color,size=3):
        self.x=x;self.y=y;self.vx=vx;self.vy=vy;self.life=life;self.max_life=life;self.color=color;self.size=size
    def update(self,dt): self.x+=self.vx*dt;self.y+=self.vy*dt;self.vx*=0.98;self.vy*=0.98;self.life-=dt
    @property
    def alive(self): return self.life>0
    def draw(self,surface):
        a=clamp(self.life/self.max_life,0,1);r=max(1,int(self.size*a))
        pygame.draw.circle(surface,lerp_color((20,20,30),self.color,a),(int(self.x),int(self.y)),r)


def predict_trajectory(lx, ly, vx, vy, wells, obstacles, asteroids, slingshots, wormholes, max_steps=TRAJECTORY_STEPS, dt=TRAJECTORY_DT):
    """Simulate probe forward to get predicted path points."""
    points = [(lx, ly)]
    x, y, pvx, pvy = lx, ly, vx, vy
    wh_timers = {i: 0.0 for i in range(len(wormholes))}
    for _ in range(max_steps):
        sdt = dt / SUB_STEPS
        for _ in range(SUB_STEPS):
            fx, fy = 0.0, 0.0
            for w in wells:
                if not w.active: continue
                wfx, wfy = w.force_on(x, y); fx += wfx; fy += wfy
            for s in slingshots:
                if s.applies_to(x, y): sfx, sfy = s.force_on(); fx += sfx; fy += sfy
            pvx += fx * sdt; pvy += fy * sdt
            x += pvx * sdt; y += pvy * sdt
            if x < PROJECTILE_RAD: x = PROJECTILE_RAD; pvx = abs(pvx) * BOUNCE_DAMPING
            elif x > WIDTH - PROJECTILE_RAD: x = WIDTH - PROJECTILE_RAD; pvx = -abs(pvx) * BOUNCE_DAMPING
            if y < PROJECTILE_RAD: y = PROJECTILE_RAD; pvy = abs(pvy) * BOUNCE_DAMPING
            elif y > HEIGHT - PROJECTILE_RAD: y = HEIGHT - PROJECTILE_RAD; pvy = -abs(pvy) * BOUNCE_DAMPING
            for obs in obstacles:
                if circle_rect_hit(x, y, PROJECTILE_RAD, obs):
                    rx2, ry2, rw2, rh2 = obs
                    cx2, cy2 = clamp(x, rx2, rx2+rw2), clamp(y, ry2, ry2+rh2)
                    ddx, ddy = x-cx2, y-cy2; dd = math.hypot(ddx, ddy)
                    if dd > 1e-8:
                        nx2, ny2 = ddx/dd, ddy/dd
                        dot2 = pvx*nx2 + pvy*ny2
                        if dot2 < 0: pvx -= 2*dot2*nx2*BOUNCE_DAMPING; pvy -= 2*dot2*ny2*BOUNCE_DAMPING
            for ast in asteroids:
                if ast.alive and circle_rect_hit(x, y, PROJECTILE_RAD, ast.rect):
                    rx2, ry2, rw2, rh2 = ast.rect
                    cx2, cy2 = clamp(x, rx2, rx2+rw2), clamp(y, ry2, ry2+rh2)
                    ddx, ddy = x-cx2, y-cy2; dd = math.hypot(ddx, ddy)
                    if dd > 1e-8:
                        nx2, ny2 = ddx/dd, ddy/dd
                        dot2 = pvx*nx2 + pvy*ny2
                        if dot2 < 0: pvx -= 2*dot2*nx2*BOUNCE_DAMPING; pvy -= 2*dot2*ny2*BOUNCE_DAMPING
        # Check wormholes
        for i, wh in enumerate(wormholes):
            wh_timers[i] = max(0, wh_timers[i] - dt)
            d1 = math.hypot(x - wh.x1, y - wh.y1)
            d2 = math.hypot(x - wh.x2, y - wh.y2)
            if d1 < wh.radius and wh_timers[i] <= 0:
                x, y = wh.x2, wh.y2; wh_timers[i] = wh.cooldown; break
            elif d2 < wh.radius and wh_timers[i] <= 0:
                x, y = wh.x1, wh.y1; wh_timers[i] = wh.cooldown; break
        points.append((x, y))
        if vlen((pvx, pvy)) < 3: break
    return points


def draw_gravity_field(surface, wells, slingshots, alpha=60):
    """Draw force field vectors across the play area."""
    gs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    step = 50
    has_attractor = any(w.polarity == 1 and w.active for w in wells)
    for gx in range(step, WIDTH, step):
        for gy in range(step, HEIGHT, step):
            fx, fy = 0.0, 0.0
            for w in wells:
                if not w.active: continue
                wfx, wfy = w.force_on(gx, gy); fx += wfx; fy += wfy
            for s in slingshots:
                if s.applies_to(gx, gy): sfx, sfy = s.force_on(); fx += sfx; fy += sfy
            mag = math.hypot(fx, fy)
            if mag < 5: continue
            intensity = min(1.0, mag / 1500)
            length = min(22, 5 + intensity * 17)
            nx, ny = fx/mag, fy/mag
            ex, ey = gx + nx*length, gy + ny*length
            base = BH_ACCRETION if has_attractor else (200, 150, 80)
            col = lerp_color((20, 20, 40), base, intensity)
            a = int(alpha * intensity)
            pygame.draw.line(gs, (*col, a), (int(gx), int(gy)), (int(ex), int(ey)), 1)
            # Small arrowhead
            px, py = -ny, nx
            pygame.draw.line(gs, (*col, a), (int(ex), int(ey)), (int(ex - nx*4 + px*2), int(ey - ny*4 + py*2)), 1)
            pygame.draw.line(gs, (*col, a), (int(ex), int(ey)), (int(ex - nx*4 - px*2), int(ey - ny*4 - py*2)), 1)
    surface.blit(gs, (0, 0))


# ═══════════════════════════════════════════════
# Serialization
# ═══════════════════════════════════════════════
def level_to_dict(level):
    return {
        "name": level["name"],
        "desc": level["desc"],
        "launcher": list(level["launcher"]),
        "target": list(level["target"]),
        "wells": [w.to_dict() for w in level["wells"]],
        "obstacles": [list(o) for o in level["obstacles"]],
        "asteroids": [a.to_dict() for a in level["asteroids"]],
        "wormholes": [wh.to_dict() for wh in level["wormholes"]],
        "slingshots": [s.to_dict() for s in level["slingshots"]],
        "comets": [c.to_dict() for c in level["comets"]],
    }

def dict_to_level(d):
    BH = BlackHole
    return {
        "name": d.get("name","Custom"),
        "desc": d.get("desc","A custom level."),
        "launcher": tuple(d["launcher"]),
        "target": tuple(d["target"]),
        "wells": [BH(w["x"],w["y"],w["mass"],w.get("polarity",1),
                   w.get("moving"),w.get("pulsing"),w.get("planet_style",0)) for w in d.get("wells",[])],
        "obstacles": [tuple(o) for o in d.get("obstacles",[])],
        "asteroids": [Asteroid(a["x"],a["y"],a["w"],a["h"],a.get("hp",1)) for a in d.get("asteroids",[])],
        "wormholes": [Wormhole(w["x1"],w["y1"],w["x2"],w["y2"],w.get("cooldown",2.0)) for w in d.get("wormholes",[])],
        "slingshots": [GravitySlingshot(s["x"],s["y"],s["w"],s["h"],s["dx"],s["dy"],s.get("strength",BOOSTER_FORCE)) for s in d.get("slingshots",[])],
        "comets": [Comet(c["x"],c["y"]) for c in d.get("comets",[])],
    }


# ═══════════════════════════════════════════════
# Procedural Level Generator
# ═══════════════════════════════════════════════
def generate_procedural_level(difficulty=1, seed=None):
    """Generate a random level. difficulty 1-10."""
    if seed is not None: random.seed(seed)
    diff = clamp(difficulty, 1, 10)

    # Launcher on left, target on right with some vertical variation
    lx, ly = 100, random.randint(150, 600)
    tx, ty = random.randint(950, 1100), random.randint(100, 650)

    wells = []
    obstacles = []
    asteroids_list = []
    wormholes = []
    slingshots = []
    comets = []

    # Number of objects scales with difficulty
    num_bh = random.randint(1, min(diff, 5))
    num_planets = random.randint(0, max(0, diff // 2 - 1))
    num_obstacles = random.randint(0, diff // 2)
    num_asteroids = random.randint(0, diff // 3)
    num_wormholes = 1 if diff >= 4 and random.random() < 0.4 else 0
    num_slingshots = 1 if diff >= 3 and random.random() < 0.4 else 0
    num_comets = random.randint(0, min(diff, 3))

    # Place black holes in the middle area
    for _ in range(num_bh):
        for attempt in range(20):
            wx = random.randint(250, 900)
            wy = random.randint(80, 670)
            mass = random.uniform(2.0, 2.0 + diff * 0.5)
            # Don't place too close to launcher or target
            if math.hypot(wx-lx, wy-ly) < 120: continue
            if math.hypot(wx-tx, wy-ty) < 100: continue
            # Don't overlap other wells
            too_close = False
            for ow in wells:
                if math.hypot(wx-ow.base_x, wy-ow.base_y) < 100: too_close=True; break
            if too_close: continue

            moving = None
            pulsing = None
            # Higher difficulty: chance of moving or pulsing
            if diff >= 5 and random.random() < 0.3:
                mtype = random.choice(["orbit", "oscillate"])
                if mtype == "orbit":
                    moving = {"type":"orbit","cx":wx,"cy":wy,"radius":random.randint(60,120),"speed":random.uniform(0.5,1.5)*random.choice([-1,1])}
                else:
                    axis = random.choice(["x","y"])
                    moving = {"type":"oscillate","cx":0,"cy":0,"radius":random.randint(80,180),"speed":random.uniform(0.8,1.8),"axis":axis}
            elif diff >= 6 and random.random() < 0.25:
                pulsing = {"period":random.uniform(2.0,4.0),"on_frac":random.uniform(0.4,0.6)}

            wells.append(BlackHole(wx, wy, round(mass, 1), 1, moving, pulsing))
            break

    # Place planets
    for _ in range(num_planets):
        for attempt in range(20):
            wx = random.randint(250, 900)
            wy = random.randint(80, 670)
            mass = random.uniform(2.0, 2.0 + diff * 0.3)
            if math.hypot(wx-lx, wy-ly) < 100: continue
            if math.hypot(wx-tx, wy-ty) < 80: continue
            too_close = any(math.hypot(wx-ow.base_x, wy-ow.base_y) < 90 for ow in wells)
            if too_close: continue
            ps = random.randint(0, len(PLANET_PALETTES)-1)
            wells.append(BlackHole(wx, wy, round(mass, 1), -1, planet_style=ps))
            break

    # Place obstacles (vertical or horizontal walls)
    for _ in range(num_obstacles):
        for attempt in range(15):
            if random.random() < 0.5:
                ox = random.randint(250, 900)
                oy = random.randint(80, 600)
                ow, oh = random.randint(15, 25), random.randint(100, 250)
            else:
                ox = random.randint(200, 800)
                oy = random.randint(80, 600)
                ow, oh = random.randint(100, 250), random.randint(15, 25)
            # Don't block launcher or target
            if point_in_rect(lx, ly, (ox-30, oy-30, ow+60, oh+60)): continue
            if point_in_rect(tx, ty, (ox-30, oy-30, ow+60, oh+60)): continue
            obstacles.append((ox, oy, ow, oh))
            break

    # Place asteroids
    for _ in range(num_asteroids):
        for attempt in range(15):
            ax = random.randint(250, 900)
            ay = random.randint(100, 600)
            aw, ah = random.randint(20, 40), random.randint(40, 120)
            if point_in_rect(lx, ly, (ax-20, ay-20, aw+40, ah+40)): continue
            if point_in_rect(tx, ty, (ax-20, ay-20, aw+40, ah+40)): continue
            hp = 2 if diff >= 7 and random.random() < 0.3 else 1
            asteroids_list.append(Asteroid(ax, ay, aw, ah, hp))
            break

    # Place wormholes
    for _ in range(num_wormholes):
        wx1 = random.randint(200, 500)
        wy1 = random.randint(100, 600)
        wx2 = random.randint(600, 1050)
        wy2 = random.randint(100, 600)
        wormholes.append(Wormhole(wx1, wy1, wx2, wy2))

    # Place slingshots
    for _ in range(num_slingshots):
        sx = random.randint(200, 800)
        sy = random.randint(100, 600)
        angle = random.uniform(0, math.pi * 2)
        slingshots.append(GravitySlingshot(sx, sy, 80, 30, math.cos(angle), math.sin(angle), 600))

    # Place comets in interesting spots
    for _ in range(num_comets):
        for attempt in range(15):
            cx = random.randint(200, 1000)
            cy = random.randint(80, 670)
            if math.hypot(cx-lx, cy-ly) < 60: continue
            if math.hypot(cx-tx, cy-ty) < 60: continue
            comets.append(Comet(cx, cy))
            break

    names = ["Anomaly","Drift","Singularity","Nebula","Vortex","Eclipse","Quasar","Pulsar","Nexus","Frontier"]
    name = f"Procedural: {random.choice(names)}-{random.randint(100,999)}"
    desc = f"Auto-generated level (difficulty {diff})."

    random.seed()  # Re-randomize
    return {
        "name": name, "desc": desc,
        "launcher": (lx, ly), "target": (tx, ty),
        "wells": wells, "obstacles": obstacles, "asteroids": asteroids_list,
        "wormholes": wormholes, "slingshots": slingshots, "comets": comets,
    }


# ═══════════════════════════════════════════════
# Level Editor
# ═══════════════════════════════════════════════
TOOLS = [
    ("Black Hole",  "1", BH_ACCRETION),
    ("Planet",      "2", (200,150,80)),
    ("Obstacle",    "3", OBSTACLE_EDGE),
    ("Asteroid",    "4", BREAKABLE_EDGE),
    ("Wormhole A",  "5", PORTAL_COL),
    ("Wormhole B",  "6", PORTAL_COL),
    ("Slingshot",   "7", BOOSTER_COL),
    ("Comet",       "8", BONUS_COL),
    ("Launcher",    "9", LAUNCHER_COL),
    ("Target",      "0", TARGET_COL),
    ("Eraser",      "E", FAIL_COL),
]

def _snapshot_level(level):
    """Take a deep-copy snapshot of level for undo/redo."""
    return level_to_dict(level)

def _restore_level(data):
    """Restore a level from a snapshot dict."""
    return dict_to_level(data)

class LevelEditor:
    def __init__(self):
        self.tool = 0  # index into TOOLS
        self.level = None
        self.wormhole_first = None  # (x,y) of first endpoint
        self.dragging = None  # ("wells", idx) or ("obstacles", idx) etc
        self.drag_offset = (0, 0)
        self.resizing = None  # ("obstacles"|"asteroids", idx, corner)
        self.message = ""
        self.msg_timer = 0.0
        self.gen_difficulty = 3
        self.sector_idx = 0
        self.history = []
        self.history_idx = -1
        self.sling_dir_drag = None  # slingshot index when right-dragging direction
        self.new_level()

    def new_level(self):
        self.level = {
            "name": "Untitled", "desc": "A custom level.",
            "launcher": (100, 375), "target": (1050, 375),
            "wells": [], "obstacles": [], "asteroids": [],
            "wormholes": [], "slingshots": [], "comets": [],
        }
        self.wormhole_first = None
        self.message = "New level created"; self.msg_timer = 2.0
        self._push_history()

    def _push_history(self):
        snap = _snapshot_level(self.level)
        self.history = self.history[:self.history_idx + 1]
        self.history.append(snap)
        self.history_idx = len(self.history) - 1
        if len(self.history) > 50:
            self.history.pop(0); self.history_idx -= 1

    def undo(self):
        if self.history_idx > 0:
            self.history_idx -= 1
            self.level = _restore_level(self.history[self.history_idx])
            self.wormhole_first = None
            self.show_msg("Undo")

    def redo(self):
        if self.history_idx < len(self.history) - 1:
            self.history_idx += 1
            self.level = _restore_level(self.history[self.history_idx])
            self.wormhole_first = None
            self.show_msg("Redo")

    def generate(self, difficulty):
        self.gen_difficulty = difficulty
        self.level = generate_procedural_level(difficulty)
        self.wormhole_first = None
        self.message = f"Generated difficulty {difficulty}"; self.msg_timer = 2.0
        self._push_history()

    def save(self, filename=None):
        os.makedirs(LEVELS_DIR, exist_ok=True)
        if not filename:
            safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in self.level["name"])
            filename = safe + ".json"
        path = os.path.join(LEVELS_DIR, filename)
        with open(path, "w") as f:
            json.dump(level_to_dict(self.level), f, indent=2)
        self.message = f"Saved: {filename}"; self.msg_timer = 2.0

    def load(self, path):
        try:
            with open(path) as f:
                data = json.load(f)
            self.level = dict_to_level(data)
            self.wormhole_first = None
            self.message = f"Loaded: {os.path.basename(path)}"; self.msg_timer = 2.0
            self._push_history()
            return True
        except Exception as e:
            self.message = f"Load error: {e}"; self.msg_timer = 3.0
            return False

    def get_custom_levels(self):
        os.makedirs(LEVELS_DIR, exist_ok=True)
        files = sorted([f for f in os.listdir(LEVELS_DIR) if f.endswith(".json")])
        return [os.path.join(LEVELS_DIR, f) for f in files]

    def show_msg(self, text):
        self.message = text; self.msg_timer = 2.0

    def update(self, dt):
        if self.msg_timer > 0: self.msg_timer -= dt
        # Update wells for animation
        for w in self.level["wells"]: w.update(dt)

    def handle_event(self, event, fonts):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Check if clicking in the panel area
            if mx >= PLAY_AREA_W:
                return self._handle_panel_click(mx, my, fonts)

            if event.button == 1:  # Left click — place or start drag
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT:
                    self._start_resize(mx, my)
                else:
                    self._place_or_drag(mx, my)
            elif event.button == 3:  # Right click — delete or start slingshot dir drag
                self._start_sling_dir(mx, my)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.dragging:
                    self._push_history()
                self.dragging = None
                if self.resizing:
                    self._push_history()
                self.resizing = None
            elif event.button == 3:
                if self.sling_dir_drag is not None:
                    self._push_history()
                self.sling_dir_drag = None

        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self.resizing:
                self._do_resize(mx, my)
            elif self.dragging:
                cat, idx = self.dragging
                ox, oy = self.drag_offset
                if cat == "wells":
                    w = self.level["wells"][idx]
                    w.base_x = mx - ox; w.base_y = my - oy; w.x = w.base_x; w.y = w.base_y
                    if w.moving:
                        if w.moving["type"] == "orbit":
                            w.moving["cx"] = w.base_x; w.moving["cy"] = w.base_y
                elif cat == "obstacles":
                    o = self.level["obstacles"][idx]
                    self.level["obstacles"][idx] = (mx-ox, my-oy, o[2], o[3])
                elif cat == "asteroids":
                    a = self.level["asteroids"][idx]
                    a.rect = (mx-ox, my-oy, a.rect[2], a.rect[3])
                elif cat == "wormholes":
                    wh = self.level["wormholes"][idx]
                    wh.x1 = mx-ox; wh.y1 = my-oy
                elif cat == "slingshots":
                    s = self.level["slingshots"][idx]
                    s.rect = (mx-ox, my-oy, s.rect[2], s.rect[3])
                elif cat == "comets":
                    self.level["comets"][idx].x = mx-ox; self.level["comets"][idx].y = my-oy
                elif cat == "launcher":
                    self.level["launcher"] = (mx-ox, my-oy)
                elif cat == "target":
                    self.level["target"] = (mx-ox, my-oy)
            elif self.sling_dir_drag is not None:
                s = self.level["slingshots"][self.sling_dir_drag]
                cx, cy = s.rect[0] + s.rect[2]//2, s.rect[1] + s.rect[3]//2
                dx, dy = mx - cx, my - cy
                if math.hypot(dx, dy) > 5:
                    s.dx, s.dy = vnorm((dx, dy))

        elif event.type == pygame.MOUSEWHEEL:
            # Adjust mass of nearest black hole/planet
            mx, my = pygame.mouse.get_pos()
            if mx < PLAY_AREA_W:
                for w in self.level["wells"]:
                    if math.hypot(mx-w.x, my-w.y) < w.base_radius + 15:
                        w.mass = clamp(w.mass + event.y * 0.5, 1.0, 8.0)
                        w.mass = round(w.mass, 1)
                        w.base_radius = int(12 + abs(w.mass) * 2)
                        self.show_msg(f"Mass: {w.mass}")
                        break

        elif event.type == pygame.KEYDOWN:
            # Number keys select tools
            key_map = {"1":0,"2":1,"3":2,"4":3,"5":4,"6":5,"7":6,"8":7,"9":8,"0":9}
            if event.unicode in key_map:
                self.tool = key_map[event.unicode]
                self.wormhole_first = None
                self.show_msg(f"Tool: {TOOLS[self.tool][0]}")

    def _start_resize(self, mx, my):
        """Shift+click on obstacle/asteroid corner to resize."""
        for i, o in enumerate(self.level["obstacles"]):
            rx, ry, rw, rh = o
            corners = [(rx, ry, "tl"), (rx+rw, ry, "tr"), (rx, ry+rh, "bl"), (rx+rw, ry+rh, "br")]
            for cx, cy, cid in corners:
                if math.hypot(mx-cx, my-cy) < 15:
                    self.resizing = ("obstacles", i, cid)
                    return
        for i, a in enumerate(self.level["asteroids"]):
            if not a.alive: continue
            rx, ry, rw, rh = a.rect
            corners = [(rx, ry, "tl"), (rx+rw, ry, "tr"), (rx, ry+rh, "bl"), (rx+rw, ry+rh, "br")]
            for cx, cy, cid in corners:
                if math.hypot(mx-cx, my-cy) < 15:
                    self.resizing = ("asteroids", i, cid)
                    return

    def _do_resize(self, mx, my):
        if not self.resizing: return
        cat, idx, corner = self.resizing
        mx = clamp(mx, 5, PLAY_AREA_W - 5)
        my = clamp(my, 5, HEIGHT - 5)
        if cat == "obstacles":
            ox, oy, ow, oh = self.level["obstacles"][idx]
            if corner == "br": self.level["obstacles"][idx] = (ox, oy, max(10, mx-ox), max(10, my-oy))
            elif corner == "bl": self.level["obstacles"][idx] = (mx, oy, max(10, ox+ow-mx), max(10, my-oy))
            elif corner == "tr": self.level["obstacles"][idx] = (ox, my, max(10, mx-ox), max(10, oy+oh-my))
            elif corner == "tl": self.level["obstacles"][idx] = (mx, my, max(10, ox+ow-mx), max(10, oy+oh-my))
        elif cat == "asteroids":
            a = self.level["asteroids"][idx]
            ox, oy, ow, oh = a.rect
            if corner == "br": a.rect = (ox, oy, max(10, mx-ox), max(10, my-oy))
            elif corner == "bl": a.rect = (mx, oy, max(10, ox+ow-mx), max(10, my-oy))
            elif corner == "tr": a.rect = (ox, my, max(10, mx-ox), max(10, oy+oh-my))
            elif corner == "tl": a.rect = (mx, my, max(10, ox+ow-mx), max(10, oy+oh-my))

    def _start_sling_dir(self, mx, my):
        """Right-click on a slingshot to drag its direction."""
        for i, s in enumerate(self.level["slingshots"]):
            if point_in_rect(mx, my, s.rect):
                self.sling_dir_drag = i
                return
        # Fall back to delete
        self._delete_at(mx, my)

    def _handle_panel_click(self, mx, my, fonts):
        # Tool buttons
        y = 200
        for i, (name, key, col) in enumerate(TOOLS):
            btn = pygame.Rect(PLAY_AREA_W + 5, y, EDITOR_PANEL_W - 10, 28)
            if btn.collidepoint(mx, my):
                self.tool = i
                self.wormhole_first = None
                self.show_msg(f"Tool: {name}")
                return
            y += 34

        # Action buttons
        y += 20
        actions = ["Generate","Test Play","Save","Load","Clear","Menu"]
        for i, action in enumerate(actions):
            btn = pygame.Rect(PLAY_AREA_W + 10, y, EDITOR_PANEL_W - 20, 30)
            if btn.collidepoint(mx, my):
                self._do_action(action, mx, my, fonts)
                return
            y += 38

        # Difficulty +/- when generating
        y_diff = 200 + len(TOOLS) * 34 + 20 + 0 * 38  # Generate button row
        # The generate button area
        gen_btn = pygame.Rect(PLAY_AREA_W + 10, y_diff, EDITOR_PANEL_W - 20, 30)
        if gen_btn.collidepoint(mx, my):
            # Check if clicking the + or - part
            third = (EDITOR_PANEL_W - 20) // 3
            if mx < gen_btn.x + third:
                self.gen_difficulty = max(1, self.gen_difficulty - 1)
            elif mx > gen_btn.x + 2 * third:
                self.gen_difficulty = min(10, self.gen_difficulty + 1)
            else:
                self.generate(self.gen_difficulty)

    def _do_action(self, action, mx, my, fonts):
        if action == "Generate":
            self.generate(self.gen_difficulty)
        elif action == "Test Play":
            return "test_play"
        elif action == "Save":
            self.save()
        elif action == "Load":
            return "load_dialog"
        elif action == "Clear":
            self.new_level()
        elif action == "Menu":
            return "menu"
        return None

    def _place_or_drag(self, mx, my):
        lv = self.level
        tool_name = TOOLS[self.tool][0]

        # Try to drag existing object first (except for Wormhole/Eraser)
        if self.tool not in (4, 5, 10):  # not wormhole or eraser
            dragged = self._try_start_drag(mx, my)
            if dragged: return

        # Place new object
        placed = True
        if tool_name == "Black Hole":
            lv["wells"].append(BlackHole(mx, my, 3.0, 1))
        elif tool_name == "Planet":
            ps = random.randint(0, len(PLANET_PALETTES)-1)
            lv["wells"].append(BlackHole(mx, my, 3.0, -1, planet_style=ps))
        elif tool_name == "Obstacle":
            lv["obstacles"].append((mx - 10, my - 60, 20, 120))
        elif tool_name == "Asteroid":
            lv["asteroids"].append(Asteroid(mx - 12, my - 40, 25, 80))
        elif tool_name == "Wormhole A":
            self.wormhole_first = (mx, my)
            self.show_msg("Wormhole A placed. Now click for B.")
            placed = False
        elif tool_name == "Wormhole B":
            if self.wormhole_first:
                x1, y1 = self.wormhole_first
                lv["wormholes"].append(Wormhole(x1, y1, mx, my))
                self.wormhole_first = None
                self.show_msg("Wormhole created!")
            else:
                self.show_msg("Place Wormhole A first!")
                placed = False
        elif tool_name == "Slingshot":
            lv["slingshots"].append(GravitySlingshot(mx - 40, my - 15, 80, 30, 1, 0))
        elif tool_name == "Comet":
            lv["comets"].append(Comet(mx, my))
        elif tool_name == "Launcher":
            lv["launcher"] = (mx, my)
        elif tool_name == "Target":
            lv["target"] = (mx, my)
        elif tool_name == "Eraser":
            before = len(lv["wells"]) + len(lv["obstacles"]) + len(lv["asteroids"]) + len(lv["wormholes"]) + len(lv["slingshots"]) + len(lv["comets"])
            self._delete_at(mx, my)
            after = len(lv["wells"]) + len(lv["obstacles"]) + len(lv["asteroids"]) + len(lv["wormholes"]) + len(lv["slingshots"]) + len(lv["comets"])
            if after < before: self._push_history()
            placed = False
        else:
            placed = False
        if placed:
            self._push_history()

    def _try_start_drag(self, mx, my):
        lv = self.level
        # Check launcher
        lx, ly = lv["launcher"]
        if math.hypot(mx-lx, my-ly) < 25:
            self.dragging = ("launcher", 0); self.drag_offset = (mx-lx, my-ly); return True
        # Check target
        tx, ty = lv["target"]
        if math.hypot(mx-tx, my-ty) < 30:
            self.dragging = ("target", 0); self.drag_offset = (mx-tx, my-ty); return True
        # Check wells
        for i, w in enumerate(lv["wells"]):
            if math.hypot(mx-w.x, my-w.y) < w.base_radius + 10:
                self.dragging = ("wells", i); self.drag_offset = (mx-w.x, my-w.y); return True
        # Check obstacles
        for i, o in enumerate(lv["obstacles"]):
            if point_in_rect(mx, my, o):
                self.dragging = ("obstacles", i); self.drag_offset = (mx-o[0], my-o[1]); return True
        # Check asteroids
        for i, a in enumerate(lv["asteroids"]):
            if a.alive and point_in_rect(mx, my, a.rect):
                self.dragging = ("asteroids", i); self.drag_offset = (mx-a.rect[0], my-a.rect[1]); return True
        # Check wormholes (drag endpoint A)
        for i, wh in enumerate(lv["wormholes"]):
            if math.hypot(mx-wh.x1, my-wh.y1) < 30:
                self.dragging = ("wormholes", i); self.drag_offset = (mx-wh.x1, my-wh.y1); return True
        # Check slingshots
        for i, s in enumerate(lv["slingshots"]):
            if point_in_rect(mx, my, s.rect):
                self.dragging = ("slingshots", i); self.drag_offset = (mx-s.rect[0], my-s.rect[1]); return True
        # Check comets
        for i, c in enumerate(lv["comets"]):
            if math.hypot(mx-c.x, my-c.y) < 20:
                self.dragging = ("comets", i); self.drag_offset = (mx-c.x, my-c.y); return True
        return False

    def _delete_at(self, mx, my):
        lv = self.level
        # Wells
        for i, w in enumerate(lv["wells"]):
            if math.hypot(mx-w.x, my-w.y) < w.base_radius + 10:
                lv["wells"].pop(i); self.show_msg("Deleted"); return
        # Obstacles
        for i, o in enumerate(lv["obstacles"]):
            if point_in_rect(mx, my, o):
                lv["obstacles"].pop(i); self.show_msg("Deleted"); return
        # Asteroids
        for i, a in enumerate(lv["asteroids"]):
            if a.alive and point_in_rect(mx, my, a.rect):
                lv["asteroids"].pop(i); self.show_msg("Deleted"); return
        # Wormholes
        for i, wh in enumerate(lv["wormholes"]):
            if math.hypot(mx-wh.x1, my-wh.y1) < 30 or math.hypot(mx-wh.x2, my-wh.y2) < 30:
                lv["wormholes"].pop(i); self.show_msg("Deleted"); return
        # Slingshots
        for i, s in enumerate(lv["slingshots"]):
            if point_in_rect(mx, my, s.rect):
                lv["slingshots"].pop(i); self.show_msg("Deleted"); return
        # Comets
        for i, c in enumerate(lv["comets"]):
            if math.hypot(mx-c.x, my-c.y) < 20:
                lv["comets"].pop(i); self.show_msg("Deleted"); return

    def draw(self, surface, fonts, time):
        lv = self.level
        # Background
        sector_idx = self.sector_idx

        # Draw play area
        play_surf = surface.subsurface((0, 0, PLAY_AREA_W, HEIGHT))
        # Simple dark bg for editor
        play_surf.fill(SECTORS[sector_idx]["bg"])
        for x in range(0, PLAY_AREA_W, 60):
            pygame.draw.line(play_surf, SECTORS[sector_idx]["grid"], (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 60):
            pygame.draw.line(play_surf, SECTORS[sector_idx]["grid"], (0, y), (PLAY_AREA_W, y))

        # Draw all objects
        for obs in lv["obstacles"]:
            pygame.draw.rect(play_surf, OBSTACLE_COL, obs, border_radius=3)
            pygame.draw.rect(play_surf, OBSTACLE_EDGE, obs, 2, border_radius=3)
        # Draw resize corner handles for obstacles
        mx2, my2 = pygame.mouse.get_pos()
        for i, o in enumerate(lv["obstacles"]):
            rx, ry, rw, rh = o
            corners = [(rx, ry), (rx+rw, ry), (rx, ry+rh), (rx+rw, ry+rh)]
            for cx, cy in corners:
                hov = math.hypot(mx2-cx, my2-cy) < 12
                sz = 5 if hov else 3
                col = WHITE if hov else (150, 140, 120)
                pygame.draw.rect(play_surf, col, (cx-sz, cy-sz, sz*2, sz*2))
        for a in lv["asteroids"]:
            a.draw(play_surf)
        # Draw resize corner handles for asteroids
        for i, a in enumerate(lv["asteroids"]):
            if not a.alive: continue
            rx, ry, rw, rh = a.rect
            corners = [(rx, ry), (rx+rw, ry), (rx, ry+rh), (rx+rw, ry+rh)]
            for cx, cy in corners:
                hov = math.hypot(mx2-cx, my2-cy) < 12
                sz = 5 if hov else 3
                col = WHITE if hov else (150, 140, 120)
                pygame.draw.rect(play_surf, col, (cx-sz, cy-sz, sz*2, sz*2))
        for s in lv["slingshots"]: s.draw(play_surf)
        for w in lv["wells"]: w.draw(play_surf)
        for wh in lv["wormholes"]: wh.draw(play_surf)
        for c in lv["comets"]: c.draw(play_surf)

        # Target
        tx, ty = lv["target"]
        pygame.draw.circle(play_surf, TARGET_GLOW, (int(tx), int(ty)), TARGET_RADIUS, 3)
        pygame.draw.circle(play_surf, TARGET_COL, (int(tx), int(ty)), TARGET_RADIUS-6, 2)
        pygame.draw.circle(play_surf, TARGET_COL, (int(tx), int(ty)), 4)

        # Launcher
        lx, ly = lv["launcher"]
        pygame.draw.circle(play_surf, LAUNCHER_COL, (int(lx), int(ly)), 16)
        pygame.draw.circle(play_surf, WHITE, (int(lx), int(ly)), 8)

        # Wormhole first-point indicator
        if self.wormhole_first:
            wx, wy = self.wormhole_first
            pygame.draw.circle(play_surf, PORTAL_COL, (int(wx), int(wy)), 15, 2)
            fs = fonts["tiny"]
            t = fs.render("A", True, PORTAL_COL)
            play_surf.blit(t, (int(wx - t.get_width()//2), int(wy - t.get_height()//2)))

        # Cursor preview
        mx, my = pygame.mouse.get_pos()
        if mx < PLAY_AREA_W:
            tool_name = TOOLS[self.tool][0]
            tool_col = TOOLS[self.tool][2]
            if tool_name == "Black Hole":
                pygame.draw.circle(play_surf, (*tool_col, 80) if len(tool_col)==3 else tool_col, (mx, my), 18, 2)
            elif tool_name == "Planet":
                pygame.draw.circle(play_surf, tool_col, (mx, my), 16, 2)
            elif tool_name == "Eraser":
                pygame.draw.line(play_surf, FAIL_COL, (mx-8, my-8), (mx+8, my+8), 2)
                pygame.draw.line(play_surf, FAIL_COL, (mx+8, my-8), (mx-8, my+8), 2)
            elif tool_name in ("Wormhole A", "Wormhole B"):
                pygame.draw.circle(play_surf, PORTAL_COL, (mx, my), 18, 2)

        # ── Side Panel ──
        panel = pygame.Rect(PLAY_AREA_W, 0, EDITOR_PANEL_W, HEIGHT)
        pygame.draw.rect(surface, ED_PANEL_BG, panel)
        pygame.draw.line(surface, (60, 50, 90), (PLAY_AREA_W, 0), (PLAY_AREA_W, HEIGHT), 2)

        ft, fs, fss = fonts["med"], fonts["small"], fonts["tiny"]

        # Title
        t = ft.render("EDITOR", True, BH_ACCRETION)
        surface.blit(t, (PLAY_AREA_W + EDITOR_PANEL_W//2 - t.get_width()//2, 10))

        # Level name
        nt = fss.render(f'"{lv["name"]}"', True, TEXT_COL)
        surface.blit(nt, (PLAY_AREA_W + 10, 40))

        # Object counts
        counts = f"BH:{sum(1 for w in lv['wells'] if w.polarity==1)} " \
                 f"PL:{sum(1 for w in lv['wells'] if w.polarity==-1)} " \
                 f"OBS:{len(lv['obstacles'])} AST:{len(lv['asteroids'])} " \
                 f"WH:{len(lv['wormholes'])} SL:{len(lv['slingshots'])} C:{len(lv['comets'])}"
        ct = fss.render(counts, True, DIM_TEXT)
        surface.blit(ct, (PLAY_AREA_W + 10, 58))

        # Sector selector
        sy = 80
        st = fss.render("Sector:", True, DIM_TEXT)
        surface.blit(st, (PLAY_AREA_W + 10, sy))
        sn = fss.render(SECTORS[self.sector_idx]["name"], True, SECTORS[self.sector_idx]["nebula_colors"][0])
        surface.blit(sn, (PLAY_AREA_W + 60, sy))

        # Tools header
        y = 120
        ht = fss.render("── Tools ──", True, DIM_TEXT)
        surface.blit(ht, (PLAY_AREA_W + EDITOR_PANEL_W//2 - ht.get_width()//2, y))
        y += 20

        # Tool buttons
        mx, my2 = pygame.mouse.get_pos()
        for i, (name, key, col) in enumerate(TOOLS):
            btn = pygame.Rect(PLAY_AREA_W + 5, y, EDITOR_PANEL_W - 10, 28)
            is_sel = (i == self.tool)
            is_hov = btn.collidepoint(mx, my2)
            bg = ED_TOOL_SEL if is_sel else (ED_TOOL_HOV if is_hov else ED_TOOL_BG)
            pygame.draw.rect(surface, bg, btn, border_radius=4)
            if is_sel:
                pygame.draw.rect(surface, col, btn, 2, border_radius=4)
            # Color swatch
            pygame.draw.circle(surface, col, (PLAY_AREA_W + 18, y + 14), 6)
            # Label
            tl = fss.render(f"{name} [{key}]", True, WHITE if is_sel else TEXT_COL)
            surface.blit(tl, (PLAY_AREA_W + 30, y + 7))
            y += 34

        # Separator
        y += 10
        pygame.draw.line(surface, (50, 40, 70), (PLAY_AREA_W + 10, y), (PLAY_AREA_W + EDITOR_PANEL_W - 10, y))
        y += 10

        # Action buttons
        actions = [
            ("Generate", f"Diff: {self.gen_difficulty}  [-/+/click]"),
            ("Test Play", "T"),
            ("Save", "Ctrl+S"),
            ("Load", "Ctrl+L"),
            ("Clear", "Ctrl+N"),
            ("Menu", "ESC"),
        ]
        self._action_rects = {}
        for i, (label, hint) in enumerate(actions):
            btn = pygame.Rect(PLAY_AREA_W + 10, y, EDITOR_PANEL_W - 20, 30)
            is_hov = btn.collidepoint(mx, my2)
            bg = ED_TOOL_HOV if is_hov else (35, 30, 55)
            pygame.draw.rect(surface, bg, btn, border_radius=6)
            pygame.draw.rect(surface, (70, 60, 100), btn, 1, border_radius=6)
            tl = fss.render(label, True, WHITE if is_hov else TEXT_COL)
            surface.blit(tl, (btn.centerx - tl.get_width()//2, btn.y + 3))
            ht = fss.render(hint, True, (70, 65, 90))
            surface.blit(ht, (btn.centerx - ht.get_width()//2, btn.y + 17))
            self._action_rects[label] = btn
            y += 38

        # Help text at bottom
        y = HEIGHT - 145
        helps = [
            "LClick: Place/Drag",
            "RClick: Delete / RDrag Slingshot dir",
            "Shift+LClick: Resize corners",
            "Scroll: Adjust mass",
            "Ctrl+Z/Y: Undo/Redo",
            "G: Generate  T: Test",
            "Ctrl+S/L/N: Save/Load/New",
        ]
        for h in helps:
            ht = fss.render(h, True, (60, 55, 80))
            surface.blit(ht, (PLAY_AREA_W + 10, y))
            y += 16

        # Message
        if self.msg_timer > 0 and self.message:
            alpha = min(255, int(self.msg_timer * 200))
            ms = fs.render(self.message, True, SUCCESS_COL)
            ms.set_alpha(alpha)
            surface.blit(ms, (10, HEIGHT - 30))


# ═══════════════════════════════════════════════
# Built-in Levels (30)
# ═══════════════════════════════════════════════
def make_levels():
    L = []
    BH = BlackHole

    # Sector 1: Outer Rim
    L.append({"name":"First Launch","desc":"Pull back from the probe and release to fire!\nNavigate past the black hole to reach the beacon.",
        "launcher":(100,400),"target":(1050,400),"wells":[BH(600,400,3.0,1)],"obstacles":[],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[]})
    L.append({"name":"Gravity Assist","desc":"Use the black hole's gravity to slingshot around the debris wall.",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(500,200,4.0,1)],"obstacles":[(550,300,30,300)],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[]})
    L.append({"name":"Planet Deflection","desc":"The planet pushes your probe away — use it to redirect toward the beacon!",
        "launcher":(100,600),"target":(1050,150),"wells":[BH(400,400,3.5,-1,planet_style=0),BH(750,300,2.0,1)],"obstacles":[],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[]})
    L.append({"name":"Asteroid Belt","desc":"Navigate through the asteroid field using black holes as guides.",
        "launcher":(100,650),"target":(1050,100),"wells":[BH(300,500,3.0,1),BH(600,350,3.0,1),BH(900,200,2.5,1)],"obstacles":[],"asteroids":[Asteroid(250,400,200,20),Asteroid(550,250,20,200),Asteroid(750,100,200,20)],"wormholes":[],"slingshots":[],"comets":[]})
    L.append({"name":"Wormhole Hop","desc":"Enter the wormhole to teleport past the debris field!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(450,500,2.5,1)],"obstacles":[(550,100,30,500)],"asteroids":[],"wormholes":[Wormhole(400,200,800,200)],"slingshots":[],"comets":[Comet(650,500)]})
    L.append({"name":"Rogue Planets","desc":"Multiple planets and black holes — find the path through!",
        "launcher":(100,650),"target":(1100,100),"wells":[BH(300,500,3.0,1),BH(500,300,2.5,-1,planet_style=1),BH(700,500,3.5,1),BH(900,250,2.0,-1,planet_style=2)],"obstacles":[(200,350,150,20),(600,150,20,250),(850,350,150,20)],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[Comet(600,450),Comet(900,400)]})

    # Sector 2: Crimson Drift
    L.append({"name":"Orbital Black Hole","desc":"This black hole orbits — time your launch carefully!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(0,0,4.0,1,moving={"type":"orbit","cx":600,"cy":375,"radius":150,"speed":1.2})],"obstacles":[],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[]})
    L.append({"name":"Break the Asteroids","desc":"Shatter the asteroids to clear a path!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(400,200,2.0,1),BH(800,550,2.0,1)],"obstacles":[],"asteroids":[Asteroid(500,300,25,150),Asteroid(700,300,25,150)],"wormholes":[],"slingshots":[],"comets":[Comet(600,200)]})
    L.append({"name":"Gravity Slingshot","desc":"Hit the slingshot zone to launch at high speed!",
        "launcher":(100,600),"target":(1050,150),"wells":[BH(500,400,3.0,1)],"obstacles":[(400,300,20,200)],"asteroids":[],"wormholes":[],"slingshots":[GravitySlingshot(250,500,100,40,0.7,-0.7,800)],"comets":[Comet(700,300)]})
    L.append({"name":"Dormant Singularity","desc":"The black hole pulses on and off — launch when dormant!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(500,375,5.0,1,pulsing={"period":3.0,"on_frac":0.5})],"obstacles":[(480,200,20,80),(480,470,20,80)],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[Comet(500,150)]})
    L.append({"name":"Twin Planets","desc":"Two planets with different gravities guard the path.",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(400,250,3.0,-1,planet_style=3),BH(800,500,4.0,-1,planet_style=4)],"obstacles":[(550,200,20,150),(650,400,20,150)],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[Comet(600,375)]})
    L.append({"name":"Crimson Gauntlet","desc":"Black holes, planets, wormholes and asteroids in the crimson drift.",
        "launcher":(100,650),"target":(1100,80),"wells":[BH(350,400,3.0,1),BH(700,200,2.5,-1,planet_style=5)],"obstacles":[(300,200,20,250),(600,350,200,20),(900,150,20,300)],"asteroids":[Asteroid(800,100,20,100)],"wormholes":[Wormhole(250,100,750,100)],"slingshots":[GravitySlingshot(550,600,80,30,0.9,-0.4,600)],"comets":[Comet(500,500),Comet(850,500)]})

    # Sector 3: Emerald Expanse
    L.append({"name":"The Wanderer","desc":"A black hole slides back and forth — find the right moment!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(600,375,3.5,1,moving={"type":"oscillate","cx":0,"cy":0,"radius":200,"speed":1.5,"axis":"y"})],"obstacles":[],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[]})
    L.append({"name":"Binary Black Holes","desc":"Two black holes orbit a shared center!",
        "launcher":(100,650),"target":(1100,100),"wells":[BH(0,0,3.5,1,moving={"type":"orbit","cx":600,"cy":375,"radius":120,"speed":1.0}),BH(0,0,3.5,1,moving={"type":"orbit","cx":600,"cy":375,"radius":120,"speed":-1.0})],"obstacles":[],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[]})
    L.append({"name":"Asteroid Fortress","desc":"Break through layered asteroids with black hole assistance.",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(350,200,2.5,1),BH(850,550,2.5,1),BH(600,375,2.0,-1,planet_style=0)],"obstacles":[(350,300,20,150),(830,300,20,150)],"asteroids":[Asteroid(500,250,25,100,hp=2),Asteroid(680,400,25,100,hp=2)],"wormholes":[],"slingshots":[],"comets":[Comet(600,100),Comet(600,650)]})
    L.append({"name":"Slingshot Maneuver","desc":"Use the gravity slingshot to overcome the planet's repulsion!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(600,375,3.0,1)],"obstacles":[],"asteroids":[],"wormholes":[],"slingshots":[GravitySlingshot(200,350,80,50,1,0,500)],"comets":[Comet(400,150),Comet(800,600)]})
    L.append({"name":"Wormhole Maze","desc":"Chain wormholes to navigate an impossible debris field.",
        "launcher":(100,650),"target":(1100,80),"wells":[BH(300,300,2.0,1),BH(900,500,2.0,1)],"obstacles":[(250,150,20,400),(500,200,20,400),(750,150,20,400),(1000,200,20,400)],"asteroids":[],"wormholes":[Wormhole(200,250,550,250),Wormhole(450,500,800,500),Wormhole(700,250,1050,150)],"slingshots":[],"comets":[Comet(350,500)]})
    L.append({"name":"Emerald Maelstrom","desc":"Pulsing black holes, slingshots, and asteroids collide!",
        "launcher":(80,680),"target":(1120,70),"wells":[BH(300,500,3.0,1),BH(600,300,3.5,-1,pulsing={"period":4.0,"on_frac":0.6},planet_style=1),BH(900,500,3.0,1)],"obstacles":[(450,400,20,200),(750,150,20,250)],"asteroids":[Asteroid(550,200,25,80),Asteroid(850,350,25,80)],"wormholes":[],"slingshots":[GravitySlingshot(200,600,80,30,0.8,-0.6,700)],"comets":[Comet(500,600),Comet(700,100)]})

    # Sector 4: Solar Corridor
    L.append({"name":"Triple Orbit","desc":"Three black holes orbit at different speeds — find the gap!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(0,0,3.0,1,moving={"type":"orbit","cx":500,"cy":375,"radius":100,"speed":0.8}),BH(0,0,3.0,1,moving={"type":"orbit","cx":700,"cy":375,"radius":100,"speed":1.2}),BH(0,0,2.5,-1,planet_style=2,moving={"type":"orbit","cx":600,"cy":200,"radius":80,"speed":1.5})],"obstacles":[],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[]})
    L.append({"name":"Planet Corridor","desc":"Navigate a corridor flanked by repelling planets!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(300,280,3.0,-1,planet_style=3),BH(300,470,3.0,-1,planet_style=4),BH(500,280,3.5,-1,planet_style=5),BH(500,470,3.5,-1,planet_style=0),BH(700,280,3.5,-1,planet_style=1),BH(700,470,3.5,-1,planet_style=2),BH(900,280,3.0,-1,planet_style=3),BH(900,470,3.0,-1,planet_style=4)],"obstacles":[(250,320,20,30),(250,400,20,30),(950,320,20,30),(950,400,20,30)],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[Comet(400,375),Comet(600,375),Comet(800,375)]})
    L.append({"name":"Asteroid Chain","desc":"Asteroid chain — black holes pull you off course!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(400,200,3.0,1),BH(400,550,3.0,1),BH(800,375,2.5,-1,planet_style=5)],"obstacles":[],"asteroids":[Asteroid(350,330,20,40),Asteroid(450,330,20,40),Asteroid(550,380,20,40),Asteroid(650,380,20,40),Asteroid(750,330,20,40)],"wormholes":[],"slingshots":[],"comets":[Comet(600,200),Comet(600,550)]})
    L.append({"name":"Slingshot Highway","desc":"Chain multiple gravity slingshots for incredible speed!",
        "launcher":(100,650),"target":(1050,100),"wells":[BH(600,400,2.0,1)],"obstacles":[(350,300,20,200),(700,200,20,250)],"asteroids":[],"wormholes":[],"slingshots":[GravitySlingshot(150,600,80,30,0.9,-0.4,600),GravitySlingshot(500,500,80,30,0.8,-0.6,600),GravitySlingshot(800,300,80,30,0.7,-0.7,600)],"comets":[Comet(350,150),Comet(900,550)]})
    L.append({"name":"The Pendulum","desc":"A massive black hole swings — deadly if you mistime it!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(600,375,5.0,1,moving={"type":"oscillate","cx":0,"cy":0,"radius":250,"speed":0.8,"axis":"y"})],"obstacles":[(450,200,20,100),(450,450,20,100),(750,200,20,100),(750,450,20,100)],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[]})
    L.append({"name":"Solar Gauntlet","desc":"The ultimate solar corridor challenge!",
        "launcher":(80,680),"target":(1120,70),"wells":[BH(300,500,3.0,1,moving={"type":"orbit","cx":300,"cy":500,"radius":60,"speed":1.5}),BH(600,300,3.5,-1,pulsing={"period":3.0,"on_frac":0.5},planet_style=2),BH(900,500,3.0,1)],"obstacles":[(400,400,20,200),(700,100,20,300)],"asteroids":[Asteroid(550,250,25,80,hp=2),Asteroid(850,400,25,80)],"wormholes":[Wormhole(250,150,750,150)],"slingshots":[GravitySlingshot(180,620,80,30,0.85,-0.5,700)],"comets":[Comet(500,600),Comet(800,200)]})

    # Sector 5: Event Horizon
    L.append({"name":"Binary Singularity","desc":"Two massive black holes orbit each other!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(0,0,4.5,1,moving={"type":"orbit","cx":550,"cy":375,"radius":100,"speed":1.0}),BH(0,0,4.5,1,moving={"type":"orbit","cx":650,"cy":375,"radius":100,"speed":-1.0})],"obstacles":[],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[]})
    L.append({"name":"Event Horizon","desc":"Black holes line a narrow corridor — stay centered!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(300,280,3.0,1),BH(300,470,3.0,1),BH(500,280,3.5,1),BH(500,470,3.5,1),BH(700,280,3.5,1),BH(700,470,3.5,1),BH(900,280,3.0,1),BH(900,470,3.0,1)],"obstacles":[(250,320,20,30),(250,400,20,30),(950,320,20,30),(950,400,20,30)],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[Comet(400,375),Comet(600,375),Comet(800,375)]})
    L.append({"name":"The Labyrinth","desc":"Asteroid maze with wormholes and breakable debris.",
        "launcher":(80,680),"target":(1120,70),"wells":[BH(300,500,2.5,1),BH(600,200,2.5,1),BH(900,500,2.5,1)],"obstacles":[(200,150,20,350),(400,300,250,20),(400,500,20,200),(700,100,20,300),(900,300,200,20)],"asteroids":[Asteroid(600,500,20,100),Asteroid(400,200,100,20)],"wormholes":[Wormhole(300,150,600,550),Wormhole(800,200,1000,400)],"slingshots":[],"comets":[Comet(500,100),Comet(800,500)]})
    L.append({"name":"Pulsing Abyss","desc":"Pulsing black holes create rhythmic chaos!",
        "launcher":(100,375),"target":(1050,375),"wells":[BH(400,300,3.5,1,pulsing={"period":2.5,"on_frac":0.5}),BH(800,450,3.5,1,pulsing={"period":3.0,"on_frac":0.5}),BH(600,375,2.0,-1,planet_style=5)],"obstacles":[],"asteroids":[],"wormholes":[],"slingshots":[],"comets":[Comet(350,500),Comet(650,200),Comet(900,500)]})
    L.append({"name":"The Crucible","desc":"Orbiting black holes, asteroids, slingshots, wormholes!",
        "launcher":(80,680),"target":(1120,70),"wells":[BH(0,0,3.5,1,moving={"type":"orbit","cx":350,"cy":400,"radius":80,"speed":1.2}),BH(700,300,3.0,-1,pulsing={"period":3.5,"on_frac":0.5},planet_style=3),BH(0,0,3.0,1,moving={"type":"oscillate","cx":900,"cy":400,"radius":100,"speed":1.0,"axis":"y"})],"obstacles":[(500,250,20,200),(800,350,20,200)],"asteroids":[Asteroid(600,300,25,80,hp=2),Asteroid(900,150,25,100)],"wormholes":[Wormhole(250,200,650,550)],"slingshots":[GravitySlingshot(150,620,80,30,0.9,-0.4,700)],"comets":[Comet(500,500),Comet(800,200),Comet(1000,500)]})
    L.append({"name":"The Final Frontier","desc":"The ultimate test. Everything at once. Good luck, Commander.",
        "launcher":(80,680),"target":(1120,70),"wells":[BH(0,0,4.0,1,moving={"type":"orbit","cx":300,"cy":450,"radius":90,"speed":1.3}),BH(600,250,4.0,-1,pulsing={"period":2.5,"on_frac":0.45},planet_style=4),BH(0,0,3.5,1,moving={"type":"orbit","cx":900,"cy":350,"radius":70,"speed":-1.5}),BH(500,600,3.0,1,pulsing={"period":3.0,"on_frac":0.55})],"obstacles":[(400,300,20,200),(700,150,20,250),(250,200,20,150),(950,300,20,200)],"asteroids":[Asteroid(550,200,25,80,hp=2),Asteroid(850,400,25,80,hp=2),Asteroid(350,500,25,60)],"wormholes":[Wormhole(200,150,700,100),Wormhole(500,650,1000,200)],"slingshots":[GravitySlingshot(130,640,80,30,0.85,-0.5,800),GravitySlingshot(750,600,80,30,0.6,-0.8,600)],"comets":[Comet(400,500),Comet(600,150),Comet(900,550)]})

    return L


# ═══════════════════════════════════════════════
# Main Game Class
# ═══════════════════════════════════════════════
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Black Holes & Planets")
        self.clock = pygame.time.Clock()
        self.fonts = {
            "title": pygame.font.SysFont("consolas", 42, bold=True),
            "large": pygame.font.SysFont("consolas", 30, bold=True),
            "med":   pygame.font.SysFont("consolas", 20),
            "small": pygame.font.SysFont("consolas", 15),
            "tiny":  pygame.font.SysFont("consolas", 12),
        }
        self.built_in_levels = make_levels()
        self.custom_levels = []  # loaded from JSON
        self.all_levels = list(self.built_in_levels)
        self.current_level = 0
        self.score = 0; self.shots_taken = 0
        self.total_stars = 0
        self.stars_per_level = [0] * len(self.built_in_levels)
        self.comets_per_level = [0] * len(self.built_in_levels)

        self.state = "menu"
        self.probe = None; self.particles = []
        self.aiming = False; self.aim_end = (0, 0)
        self.bg = StarryBackground()
        self.time = 0.0
        self.complete_timer = 0.0
        self.message_alpha = 0.0; self.message_text = ""; self.message_color = FAIL_COL

        self.editor = LevelEditor()
        self.editor_return_state = "menu"
        self.load_dialog_open = False
        self.load_dialog_files = []
        self.load_dialog_scroll = 0

        self.btn_play = pygame.Rect(0,0,0,0)
        self.btn_editor = pygame.Rect(0,0,0,0)
        self.btn_next = pygame.Rect(0,0,0,0)
        self.btn_menu = pygame.Rect(0,0,0,0)
        self.btn_endless = pygame.Rect(0,0,0,0)

        # New features
        self.show_gravity = False
        self.shake_amount = 0.0
        self.shake_time = 0.0
        self.level_timer = 0.0
        self.best_times = {}  # level_idx -> best float seconds
        self.endless_score = 0
        self.endless_streak = 0
        self.endless_difficulty = 1
        self.endless_best_streak = 0

    def _refresh_all_levels(self):
        self.all_levels = list(self.built_in_levels) + list(self.custom_levels)
        # Extend star tracking
        while len(self.stars_per_level) < len(self.all_levels):
            self.stars_per_level.append(0)
            self.comets_per_level.append(0)

    def load_custom_levels(self):
        self.custom_levels = []
        for path in self.editor.get_custom_levels():
            try:
                with open(path) as f:
                    data = json.load(f)
                self.custom_levels.append(dict_to_level(data))
            except: pass
        self._refresh_all_levels()

    def save_custom_level(self, level, filename=None):
        os.makedirs(LEVELS_DIR, exist_ok=True)
        if not filename:
            safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in level["name"])
            filename = safe + ".json"
        path = os.path.join(LEVELS_DIR, filename)
        with open(path, "w") as f:
            json.dump(level_to_dict(level), f, indent=2)
        self.load_custom_levels()

    def load_level(self, idx):
        if idx >= len(self.all_levels): idx = 0
        self.current_level = idx
        self.state = "playing"
        self.probe = None; self.particles = []; self.aiming = False; self.shots_taken = 0; self.complete_timer = 0
        self.level_timer = 0.0
        self.shake_amount = 0.0; self.shake_time = 0.0
        level = self.all_levels[idx]
        for w in level["wells"]:
            w.pulse_phase=random.uniform(0,math.pi*2); w.ring_anim=0; w.disk_angle=random.uniform(0,math.pi*2)
            w.move_angle=random.uniform(0,math.pi*2); w.pulse_timer=0; w.active=True
        for p in level["wormholes"]: p.timer1=p.timer2=0
        for c in level["comets"]: c.collected=False
        for a in level["asteroids"]: a.hp=a.max_hp; a.alive=True

    def _start_endless(self):
        self.endless_score = 0
        self.endless_streak = 0
        self.endless_difficulty = 1
        self.endless_best_streak = 0
        self.score = 0; self.total_stars = 0
        self._next_endless_level()

    def _next_endless_level(self):
        lv = generate_procedural_level(self.endless_difficulty)
        lv["name"] = f"Endless #{self.endless_streak + 1} (Diff {self.endless_difficulty})"
        lv["desc"] = f"Procedural level — difficulty {self.endless_difficulty}. Streak: {self.endless_streak}"
        self.all_levels.append(lv)
        self.stars_per_level.append(0)
        self.comets_per_level.append(0)
        self.editor_return_state = "endless"
        self.load_level(len(self.all_levels) - 1)

    def get_level(self): return self.all_levels[self.current_level] if self.current_level < len(self.all_levels) else self.all_levels[0]

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False

            # Load dialog gets priority
            if self.load_dialog_open:
                self._handle_load_dialog_event(event)
                continue

            if self.state == "editor":
                self.editor.handle_event(event, self.fonts)
                # Check for special returns from panel clicks
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if mx >= PLAY_AREA_W and hasattr(self.editor, '_action_rects'):
                        for label, rect in self.editor._action_rects.items():
                            if rect.collidepoint(mx, my):
                                if label == "Test Play":
                                    self._start_test_play()
                                elif label == "Menu":
                                    self.state = "menu"
                                elif label == "Load":
                                    self._open_load_dialog()
                                elif label == "Generate":
                                    third = (EDITOR_PANEL_W - 20) // 3
                                    if mx < rect.x + third:
                                        self.editor.gen_difficulty = max(1, self.editor.gen_difficulty - 1)
                                        self.editor.generate(self.editor.gen_difficulty)
                                    elif mx > rect.x + 2 * third:
                                        self.editor.gen_difficulty = min(10, self.editor.gen_difficulty + 1)
                                        self.editor.generate(self.editor.gen_difficulty)
                                    else:
                                        self.editor.generate(self.editor.gen_difficulty)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t: self._start_test_play()
                    elif event.key == pygame.K_g: self.editor.generate(self.editor.gen_difficulty)
                    elif event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL):
                        self.editor.save()
                    elif event.key == pygame.K_l and (event.mod & pygame.KMOD_CTRL):
                        self._open_load_dialog()
                    elif event.key == pygame.K_n and (event.mod & pygame.KMOD_CTRL):
                        self.editor.new_level()
                    elif event.key == pygame.K_z and (event.mod & pygame.KMOD_CTRL):
                        self.editor.undo()
                    elif event.key == pygame.K_y and (event.mod & pygame.KMOD_CTRL):
                        self.editor.redo()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state in ("playing","level_complete"): self.state = self.editor_return_state
                    else: return False
                if event.key == pygame.K_r and self.state == "playing": self.load_level(self.current_level)
                if event.key == pygame.K_n and self.state == "playing":
                    if self.current_level < len(self.all_levels)-1: self.load_level(self.current_level+1)
                if event.key == pygame.K_f and self.state == "playing":
                    self.show_gravity = not self.show_gravity

            if self.state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_play.collidepoint(event.pos):
                        self.load_custom_levels(); self._refresh_all_levels()
                        self.score=0; self.total_stars=0
                        self.stars_per_level=[0]*len(self.all_levels)
                        self.comets_per_level=[0]*len(self.all_levels)
                        self.editor_return_state = "menu"
                        self.load_level(0)
                    if self.btn_editor.collidepoint(event.pos):
                        self.editor.new_level(); self.state = "editor"
                    if self.btn_endless.collidepoint(event.pos):
                        self.load_custom_levels(); self._refresh_all_levels()
                        self._start_endless()

            elif self.state == "playing":
                level = self.get_level()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.probe is None or not self.probe.alive:
                        lx,ly = level["launcher"]
                        if math.hypot(event.pos[0]-lx, event.pos[1]-ly) < 80:
                            self.aiming=True; self.aim_end=event.pos
                if event.type == pygame.MOUSEMOTION and self.aiming: self.aim_end=event.pos
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.aiming:
                    self.aiming=False; lx,ly=level["launcher"]
                    dx,dy=lx-self.aim_end[0],ly-self.aim_end[1]; power=math.hypot(dx,dy)
                    if power>10:
                        power=clamp(power,MIN_POWER,MAX_POWER); nx,ny=vnorm((dx,dy))
                        self.probe=Probe(lx,ly,nx*power,ny*power); self.shots_taken+=1
                        for _ in range(15):
                            a=random.uniform(0,math.pi*2); s=random.uniform(50,200)
                            self.particles.append(Particle(lx,ly,math.cos(a)*s,math.sin(a)*s,random.uniform(0.3,0.8),LAUNCHER_COL,3))

            elif self.state == "level_complete":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_next.collidepoint(event.pos):
                        if self.editor_return_state == "endless":
                            self._next_endless_level()
                        elif self.current_level < len(self.all_levels)-1:
                            self.load_level(self.current_level+1)
                        else: self.state = "game_complete"
                    if self.btn_menu.collidepoint(event.pos): self.state = self.editor_return_state

            elif self.state == "game_complete":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_menu.collidepoint(event.pos): self.state = "menu"
        return True

    def _start_test_play(self):
        lv = self.editor.level
        self.all_levels.append(lv)
        self.stars_per_level.append(0)
        self.comets_per_level.append(0)
        self.editor_return_state = "editor"
        self.load_level(len(self.all_levels) - 1)

    def _open_load_dialog(self):
        self.load_dialog_open = True
        self.load_dialog_files = self.editor.get_custom_levels()
        self.load_dialog_scroll = 0

    def _handle_load_dialog_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.load_dialog_open = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Close button
            close_rect = pygame.Rect(WIDTH//2+140, HEIGHT//2-130, 30, 30)
            if close_rect.collidepoint(mx, my):
                self.load_dialog_open = False; return
            # File list
            list_rect = pygame.Rect(WIDTH//2-200, HEIGHT//2-80, 400, 200)
            if list_rect.collidepoint(mx, my):
                idx = (my - list_rect.y) // 25 + self.load_dialog_scroll
                if 0 <= idx < len(self.load_dialog_files):
                    self.editor.load(self.load_dialog_files[idx])
                    self.load_dialog_open = False
            # Cancel
            cancel_rect = pygame.Rect(WIDTH//2-60, HEIGHT//2+140, 120, 35)
            if cancel_rect.collidepoint(mx, my):
                self.load_dialog_open = False
            # Scroll
            if event.button == 4: self.load_dialog_scroll = max(0, self.load_dialog_scroll - 1)
            if event.button == 5: self.load_dialog_scroll = min(max(0, len(self.load_dialog_files)-7), self.load_dialog_scroll+1)

    def update(self, dt):
        self.time += dt
        # Screen shake decay
        if self.shake_time > 0:
            self.shake_time -= dt
            self.shake_amount = MAX_SHAKE * (self.shake_time / 0.3) if self.shake_time > 0 else 0
        else:
            self.shake_amount = 0
        if self.state == "editor":
            self.editor.update(dt)
            return
        if self.state == "playing":
            self.level_timer += dt
            level = self.get_level()
            for w in level["wells"]: w.update(dt)
            for p in level["wormholes"]: p.update(dt)
            for s in level["slingshots"]: s.update(dt)
            for c in level["comets"]: c.update(dt)
            if self.probe and self.probe.alive:
                old_alive_asteroids = [a.alive for a in level["asteroids"]]
                self.probe.update(dt,level["wells"],level["obstacles"],level["asteroids"],level["slingshots"])
                # Check if any asteroid was just destroyed -> screen shake
                for i, a in enumerate(level["asteroids"]):
                    if old_alive_asteroids[i] and not a.alive:
                        self.shake_time = 0.2
                        self.shake_amount = 6
                        for _ in range(10):
                            ang=random.uniform(0,math.pi*2); spd=random.uniform(60,180)
                            self.particles.append(Particle(a.rect[0]+a.rect[2]//2,a.rect[1]+a.rect[3]//2,math.cos(ang)*spd,math.sin(ang)*spd,random.uniform(0.3,0.7),BREAKABLE_EDGE,random.randint(2,4)))
                for wh in level["wormholes"]:
                    if wh.check_teleport(self.probe):
                        self.shake_time = 0.15
                        self.shake_amount = 4
                        for _ in range(20):
                            a=random.uniform(0,math.pi*2); s=random.uniform(30,150)
                            self.particles.append(Particle(self.probe.x,self.probe.y,math.cos(a)*s,math.sin(a)*s,random.uniform(0.2,0.6),PORTAL_COL,2))
                for c in level["comets"]:
                    if c.check_collect(self.probe.x,self.probe.y):
                        self.comets_per_level[self.current_level]+=1; self.score+=50
                        for _ in range(15):
                            a=random.uniform(0,math.pi*2); s=random.uniform(40,120)
                            self.particles.append(Particle(c.x,c.y,math.cos(a)*s,math.sin(a)*s,random.uniform(0.3,0.8),BONUS_COL,2))
                tx,ty=level["target"]
                if math.hypot(self.probe.x-tx,self.probe.y-ty)<TARGET_RADIUS+PROJECTILE_RAD:
                    self._on_level_complete()
                if not self.probe.alive:
                    self.message_text="Probe lost! Try again (R)"; self.message_color=FAIL_COL
        elif self.state == "level_complete": self.complete_timer+=dt
        for p in self.particles: p.update(dt)
        self.particles=[p for p in self.particles if p.alive]
        if self.message_text: self.message_alpha=min(255,self.message_alpha+400*dt)
        else: self.message_alpha=max(0,self.message_alpha-400*dt)

    def _on_level_complete(self):
        self.state="level_complete"; self.complete_timer=0
        self.shake_time = 0.3; self.shake_amount = MAX_SHAKE
        shots=self.shots_taken; stars=3 if shots==1 else (2 if shots<=3 else 1)
        if self.current_level < len(self.stars_per_level):
            self.stars_per_level[self.current_level]=max(self.stars_per_level[self.current_level],stars)
        self.total_stars=sum(self.stars_per_level); self.score+=stars*100+max(0,(5-shots)*50)
        # Track best time for built-in levels
        if self.current_level < 30:
            prev = self.best_times.get(self.current_level, 9999)
            if self.level_timer < prev:
                self.best_times[self.current_level] = self.level_timer
        # Endless mode tracking
        if self.editor_return_state == "endless":
            self.endless_streak += 1
            self.endless_best_streak = max(self.endless_best_streak, self.endless_streak)
            self.endless_difficulty = min(10, 1 + self.endless_streak // 3)
            self.endless_score += stars * 100 + max(0, (5 - shots) * 50)
        tx,ty=self.get_level()["target"]
        for _ in range(50):
            a=random.uniform(0,math.pi*2); s=random.uniform(80,300)
            c=random.choice([SUCCESS_COL,BULLET_COL,TARGET_COL,LAUNCHER_COL,WHITE])
            self.particles.append(Particle(tx,ty,math.cos(a)*s,math.sin(a)*s,random.uniform(0.5,1.5),c,random.randint(2,5)))
        # If we were testing from editor, also save the level
        if self.editor_return_state == "editor" and self.current_level == len(self.all_levels) - 1:
            self.save_custom_level(self.editor.level)

    # ── Drawing ──
    def draw(self):
        if self.state == "editor":
            self.editor.draw(self.screen, self.fonts, self.time)
            if self.load_dialog_open: self._draw_load_dialog()
            pygame.display.flip(); return

        # Apply screen shake offset
        shake_ox, shake_oy = 0, 0
        if self.shake_amount > 0.5:
            shake_ox = random.uniform(-self.shake_amount, self.shake_amount)
            shake_oy = random.uniform(-self.shake_amount, self.shake_amount)

        if self.state == "menu": si = 0
        else: si = SECTORS.index(sector_for_level(self.current_level)) if self.current_level < 30 else 0
        self.bg.draw(self.screen, si, self.time)

        if self.state == "menu": self._draw_menu()
        elif self.state in ("playing","level_complete"): self._draw_game(shake_ox, shake_oy)
        elif self.state == "game_complete": self._draw_game_complete()
        pygame.display.flip()

    def _draw_menu(self):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,80)); self.screen.blit(ov,(0,0))
        ft,fs,fss=self.fonts["title"],self.fonts["med"],self.fonts["tiny"]
        title="BLACK HOLES & PLANETS"; go=math.sin(self.time*2)*3
        shadow=ft.render(title,True,(20,5,40)); self.screen.blit(shadow,(WIDTH//2-shadow.get_width()//2+3,110+go+3))
        t=ft.render(title,True,BH_ACCRETION); self.screen.blit(t,(WIDTH//2-t.get_width()//2,110+go))
        sub=fs.render("Navigate gravitational fields — 30 built-in levels + editor & procedural generation",True,DIM_TEXT)
        self.screen.blit(sub,(WIDTH//2-sub.get_width()//2,165))

        # Decorative
        bh_x,bh_y=450+math.cos(self.time*0.7)*60,280+math.sin(self.time*0.7)*20
        for i in range(3,0,-1):
            r=14+i*8; gs=pygame.Surface((r*2,r*2),pygame.SRCALPHA); pygame.draw.circle(gs,(*BH_ACCRETION,20),(r,r),r,2); self.screen.blit(gs,(int(bh_x-r),int(bh_y-r)))
        pygame.draw.circle(self.screen,BH_CORE,(int(bh_x),int(bh_y)),12); pygame.draw.circle(self.screen,BH_EVENT_H,(int(bh_x),int(bh_y)),14,2)
        pl_x,pl_y=750-math.cos(self.time*0.5)*50,280+math.sin(self.time*0.5)*25
        pal=PLANET_PALETTES[2]
        for i in range(2,0,-1):
            r=16+i*8; gs=pygame.Surface((r*2,r*2),pygame.SRCALPHA); pygame.draw.circle(gs,(*pal["atmo"],20),(r,r),r); self.screen.blit(gs,(int(pl_x-r),int(pl_y-r)))
        pygame.draw.circle(self.screen,pal["body"],(int(pl_x),int(pl_y)),14)
        pygame.draw.ellipse(self.screen,pal["ring"],(int(pl_x-22),int(pl_y-5),44,10),2)

        features = [("Black Holes","Massive gravity bending your path"),("Planets","Repulsive fields to redirect you"),
                     ("Wormholes","Teleport across the sector"),("Gravity Slingshots","Boost your probe's speed"),
                     ("Asteroids","Breakable debris fields"),("Level Editor","Create & save custom levels"),
                     ("Procedural Gen","Auto-generate infinite levels"),("Endless Mode","Escalating difficulty streak"),
                     ("Trajectory Preview","See predicted path while aiming"),("Gravity Overlay","Press F to visualize fields"),
                     ("Speed-Run Timer","Track your best times"),("Comets","Collect for bonus points")]
        y=330
        for i,(feat,desc) in enumerate(features):
            cx = 120 + (i // 4) * 340
            ry = y + (i % 4) * 24
            ft2=fss.render(f"  {feat}",True,TEXT_COL); dt2=fss.render(f"  — {desc}",True,DIM_TEXT)
            self.screen.blit(ft2,(cx,ry)); self.screen.blit(dt2,(cx+ft2.get_width(),ry))

        mx,my=pygame.mouse.get_pos()
        bw,bh2=240,50
        self.btn_play=pygame.Rect(WIDTH//2-bw-10,470,bw,bh2)
        hov=self.btn_play.collidepoint(mx,my)
        pygame.draw.rect(self.screen,BUTTON_HOVER if hov else BUTTON_COL,self.btn_play,border_radius=12)
        pygame.draw.rect(self.screen,BH_ACCRETION,self.btn_play,2,border_radius=12)
        pt=fs.render("PLAY",True,WHITE); self.screen.blit(pt,(self.btn_play.centerx-pt.get_width()//2,self.btn_play.centery-pt.get_height()//2))

        self.btn_editor=pygame.Rect(WIDTH//2+10,470,bw,bh2)
        hov=self.btn_editor.collidepoint(mx,my)
        pygame.draw.rect(self.screen,BUTTON_HOVER if hov else BUTTON_COL,self.btn_editor,border_radius=12)
        pygame.draw.rect(self.screen,TARGET_COL,self.btn_editor,2,border_radius=12)
        et=fs.render("EDITOR",True,WHITE); self.screen.blit(et,(self.btn_editor.centerx-et.get_width()//2,self.btn_editor.centery-et.get_height()//2))

        # Endless mode button
        self.btn_endless=pygame.Rect(WIDTH//2-bw//2,535,bw,bh2)
        hov=self.btn_endless.collidepoint(mx,my)
        pygame.draw.rect(self.screen,BUTTON_HOVER if hov else BUTTON_COL,self.btn_endless,border_radius=12)
        pygame.draw.rect(self.screen,BONUS_COL,self.btn_endless,2,border_radius=12)
        elt=fs.render("ENDLESS",True,WHITE); self.screen.blit(elt,(self.btn_endless.centerx-elt.get_width()//2,self.btn_endless.centery-elt.get_height()//2))

        custom_count = len(self.editor.get_custom_levels())
        if custom_count > 0:
            ct = fss.render(f"{custom_count} custom level(s) found in custom_levels/", True, SUCCESS_COL)
            self.screen.blit(ct, (WIDTH//2-ct.get_width()//2, 595))

        st=fss.render("Sectors: Outer Rim | Crimson Drift | Emerald Expanse | Solar Corridor | Event Horizon",True,(55,45,75))
        self.screen.blit(st,(WIDTH//2-st.get_width()//2,625))
        it=fss.render("Click & drag from probe to aim | F = Gravity overlay | R = Restart | ESC = Menu",True,(45,45,60))
        self.screen.blit(it,(WIDTH//2-it.get_width()//2,648))

    def _draw_game(self, shake_ox=0, shake_oy=0):
        level=self.get_level()
        sox, soy = int(shake_ox), int(shake_oy)

        for obs in level["obstacles"]:
            rx,ry,rw,rh=obs; rect=pygame.Rect(rx+sox,ry+soy,rw,rh)
            pygame.draw.rect(self.screen,OBSTACLE_COL,rect,border_radius=4); pygame.draw.rect(self.screen,OBSTACLE_EDGE,rect,2,border_radius=4)
            pygame.draw.line(self.screen,(90,85,75),(rect.x+2,rect.y+2),(rect.x+rect.w-2,rect.y+2),1)
        for a in level["asteroids"]: a.draw(self.screen)
        for s in level["slingshots"]: s.draw(self.screen)
        for w in level["wells"]: w.draw(self.screen)
        for wh in level["wormholes"]: wh.draw(self.screen)
        for c in level["comets"]: c.draw(self.screen)

        # Gravity field overlay
        if self.show_gravity:
            draw_gravity_field(self.screen, level["wells"], level["slingshots"])

        tx,ty=level["target"]; tp=0.7+0.3*math.sin(self.time*3)
        for i in range(4,0,-1):
            r=TARGET_RADIUS+i*8; gs=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(gs,(50,255,100,int(20*tp)),(r,r),r); self.screen.blit(gs,(int(tx-r)+sox,int(ty-r)+soy))
        pygame.draw.circle(self.screen,TARGET_GLOW,(int(tx)+sox,int(ty)+soy),TARGET_RADIUS,3)
        pygame.draw.circle(self.screen,TARGET_COL,(int(tx)+sox,int(ty)+soy),TARGET_RADIUS-6,2)
        pygame.draw.circle(self.screen,TARGET_COL,(int(tx)+sox,int(ty)+soy),4)
        lx,ly=level["launcher"]; lp=0.8+0.2*math.sin(self.time*4)
        for i in range(3,0,-1):
            r=18+i*6; gs=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(gs,(0,200,255,int(15*lp)),(r,r),r); self.screen.blit(gs,(int(lx-r)+sox,int(ly-r)+soy))
        pygame.draw.circle(self.screen,LAUNCHER_COL,(int(lx)+sox,int(ly)+soy),16); pygame.draw.circle(self.screen,WHITE,(int(lx)+sox,int(ly)+soy),8)
        if self.aiming:
            dx,dy=lx-self.aim_end[0],ly-self.aim_end[1]; power=math.hypot(dx,dy)
            pc=clamp(power,0,MAX_POWER); pr=pc/MAX_POWER
            if power>5:
                nx,ny=vnorm((dx,dy)); ex,ey=lx+nx*80,ly+ny*80
                pygame.draw.line(self.screen,LAUNCHER_COL,(int(lx)+sox,int(ly)+soy),(int(ex)+sox,int(ey)+soy),2)
                px2,py2=-ny,nx
                pygame.draw.polygon(self.screen,LAUNCHER_COL,[(int(ex)+sox,int(ey)+soy),(int(ex-nx*10+px2*4)+sox,int(ey-ny*10+py2*4)+soy),(int(ex-nx*10-px2*4)+sox,int(ey-ny*10-py2*4)+soy)])
                # Trajectory preview
                vx, vy = nx * pc, ny * pc
                pts = predict_trajectory(lx, ly, vx, vy, level["wells"], level["obstacles"],
                    level["asteroids"], level["slingshots"], level["wormholes"])
                for i in range(1, len(pts)):
                    alpha = max(10, int(180 * (1 - i / len(pts))))
                    dim = tuple(max(0, c * alpha // 255) for c in LAUNCHER_COL[:3])
                    if i % 3 == 0:  # Dotted effect
                        pygame.draw.circle(self.screen, dim, (int(pts[i][0])+sox, int(pts[i][1])+soy), 2)
            bx,by,bw2,bh2=20,HEIGHT-50,200,20
            pygame.draw.rect(self.screen,(20,20,35),(bx,by,bw2,bh2),border_radius=5)
            fw=int(bw2*pr)
            if fw>0: pygame.draw.rect(self.screen,lerp_color(POWER_LOW,POWER_HIGH,pr),(bx,by,fw,bh2),border_radius=5)
            pygame.draw.rect(self.screen,(60,60,90),(bx,by,bw2,bh2),2,border_radius=5)
            pt=self.fonts["tiny"].render(f"POWER: {int(pr*100)}%",True,TEXT_COL)
            self.screen.blit(pt,(bx+bw2//2-pt.get_width()//2,by+2))
            pygame.draw.line(self.screen,(0,150,200),(int(lx)+sox,int(ly)+soy),(int(self.aim_end[0]),int(self.aim_end[1])),2)
        if self.probe and self.probe.alive: self.probe.draw(self.screen)
        for p in self.particles: p.draw(self.screen)
        self._draw_hud()
        if self.state=="level_complete": self._draw_level_complete()
        if self.message_alpha>0 and self.state=="playing":
            ms=self.fonts["med"].render(self.message_text,True,self.message_color); ms.set_alpha(int(self.message_alpha))
            self.screen.blit(ms,(WIDTH//2-ms.get_width()//2,HEIGHT-100))

    def _draw_hud(self):
        level=self.get_level(); fs,fss=self.fonts["small"],self.fonts["tiny"]
        si=min(self.current_level//6,4)
        is_endless = self.editor_return_state == "endless"
        panel_h = 140 if is_endless else 120
        panel=pygame.Surface((400,panel_h),pygame.SRCALPHA); panel.fill((8,8,22,190)); self.screen.blit(panel,(10,10))
        is_custom = self.current_level >= len(self.built_in_levels)
        if is_endless:
            prefix = f"ENDLESS (Diff {self.endless_difficulty})"
            sname = f"Streak: {self.endless_streak} | Best: {self.endless_best_streak}"
        elif is_custom:
            prefix = "CUSTOM"
            sname = self.all_levels[self.current_level]["name"]
        else:
            prefix = f"Sector {si+1}"
            sname = SECTORS[si]["name"]
        wn=fss.render(f"{prefix}: {sname}",True,lerp_color(DIM_TEXT,SECTORS[si]["nebula_colors"][0],0.5))
        self.screen.blit(wn,(20,14))
        nt=fs.render(f"Level {self.current_level+1}: {level['name']}",True,WHITE); self.screen.blit(nt,(20,32))
        st=fs.render(f"Shots: {self.shots_taken}",True,TEXT_COL); self.screen.blit(st,(20,62))
        sct=fs.render(f"Score: {self.score}",True,BULLET_COL); self.screen.blit(sct,(20,82))
        # Timer
        mins = int(self.level_timer) // 60
        secs = self.level_timer - mins * 60
        timer_str = f"Time: {mins}:{secs:05.2f}"
        tt2=fss.render(timer_str,True,(180,180,200)); self.screen.blit(tt2,(200,82))
        # Best time
        if self.current_level < 30 and self.current_level in self.best_times:
            bt_val = self.best_times[self.current_level]
            bm = int(bt_val) // 60; bs = bt_val - bm * 60
            bt_str = f"Best: {bm}:{bs:05.2f}"
            bt3=fss.render(bt_str,True,SUCCESS_COL); self.screen.blit(bt3,(200,96))
        if is_endless:
            es=fss.render(f"Endless Score: {self.endless_score}",True,BONUS_COL); self.screen.blit(es,(20,102))
        cc=sum(1 for c in level["comets"] if c.collected); ct=len(level["comets"])
        if ct>0: bt4=fs.render(f"Comets: {cc}/{ct}",True,BONUS_COL); self.screen.blit(bt4,(200,62))
        tt=fs.render(f"\u2605 {self.total_stars}/{len(self.all_levels)*3}",True,STAR_COL); self.screen.blit(tt,(WIDTH-tt.get_width()-20,15))
        bar_w=200; bar_x=WIDTH-bar_w-20; bar_y=55
        pygame.draw.rect(self.screen,(20,20,35),(bar_x,bar_y,bar_w,8),border_radius=4)
        prog=(self.current_level+(1 if self.state=="level_complete" else 0))/len(self.all_levels)
        fw=int(bar_w*prog)
        if fw>0: pygame.draw.rect(self.screen,BH_ACCRETION,(bar_x,bar_y,fw,8),border_radius=4)
        lt=fss.render(f"{self.current_level+1}/{len(self.all_levels)}",True,DIM_TEXT)
        self.screen.blit(lt,(bar_x+bar_w//2-lt.get_width()//2,bar_y+12))
        if self.shots_taken==0 and not self.aiming and (not self.probe or not self.probe.alive):
            for i,line in enumerate(level["desc"].split("\n")):
                dt=fs.render(line,True,DIM_TEXT); self.screen.blit(dt,(WIDTH//2-dt.get_width()//2,HEIGHT-60+i*22))
        grav_hint = " | F: Gravity" if self.show_gravity else ""
        ht=fss.render(f"R: Restart | N: Skip | ESC: Menu{grav_hint}",True,(50,50,65))
        self.screen.blit(ht,(WIDTH//2-ht.get_width()//2,HEIGHT-20))

    def _draw_level_complete(self):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,140)); self.screen.blit(ov,(0,0))
        alpha=min(1.0,self.complete_timer*2); pw,ph=520,340; px,py=WIDTH//2-pw//2,HEIGHT//2-ph//2
        panel=pygame.Surface((pw,ph),pygame.SRCALPHA); panel.fill((10,8,25,int(220*alpha))); self.screen.blit(panel,(px,py))
        pygame.draw.rect(self.screen,BH_ACCRETION,(px,py,pw,ph),2,border_radius=12)
        ct=self.fonts["large"].render("BEACON REACHED!",True,SUCCESS_COL); ct.set_alpha(int(255*alpha))
        self.screen.blit(ct,(WIDTH//2-ct.get_width()//2,py+20))
        stars=self.stars_per_level[self.current_level] if self.current_level<len(self.stars_per_level) else 0
        ss="★ "*stars+"☆ "*(3-stars)
        st=self.fonts["large"].render(ss,True,BULLET_COL); st.set_alpha(int(255*alpha))
        self.screen.blit(st,(WIDTH//2-st.get_width()//2,py+70))
        sm=self.fonts["med"].render(f"Shots: {self.shots_taken}",True,TEXT_COL); sm.set_alpha(int(255*alpha))
        self.screen.blit(sm,(WIDTH//2-sm.get_width()//2,py+120))
        scm=self.fonts["med"].render(f"Score: {self.score}",True,BULLET_COL); scm.set_alpha(int(255*alpha))
        self.screen.blit(scm,(WIDTH//2-scm.get_width()//2,py+150))
        # Show time
        mins = int(self.level_timer) // 60; secs = self.level_timer - mins * 60
        tm=self.fonts["med"].render(f"Time: {mins}:{secs:05.2f}",True,(180,180,200)); tm.set_alpha(int(255*alpha))
        self.screen.blit(tm,(WIDTH//2-tm.get_width()//2,py+180))
        if self.complete_timer>0.5:
            bw2,bh2=180,45
            is_endless = self.editor_return_state == "endless"
            show_next = is_endless or self.current_level < len(self.all_levels)-1
            if show_next:
                self.btn_next=pygame.Rect(WIDTH//2-bw2//2,py+220,bw2,bh2)
                mx,my=pygame.mouse.get_pos(); hov=self.btn_next.collidepoint(mx,my)
                pygame.draw.rect(self.screen,BUTTON_HOVER if hov else BUTTON_COL,self.btn_next,border_radius=10)
                pygame.draw.rect(self.screen,BH_ACCRETION,self.btn_next,2,border_radius=10)
                label = "NEXT LEVEL" if not is_endless else f"NEXT (Diff {self.endless_difficulty})"
                nt=self.fonts["med"].render(label,True,WHITE)
                self.screen.blit(nt,(self.btn_next.centerx-nt.get_width()//2,self.btn_next.centery-nt.get_height()//2))
            else:
                self.btn_next=pygame.Rect(0,0,0,0)
                fi=self.fonts["med"].render("All levels cleared!",True,SUCCESS_COL); fi.set_alpha(int(255*alpha))
                self.screen.blit(fi,(WIDTH//2-fi.get_width()//2,py+230))
            self.btn_menu=pygame.Rect(WIDTH//2-80,py+ph-50,160,35)
            mx,my=pygame.mouse.get_pos(); hov=self.btn_menu.collidepoint(mx,my)
            pygame.draw.rect(self.screen,BUTTON_HOVER if hov else (25,20,40),self.btn_menu,border_radius=8)
            pygame.draw.rect(self.screen,(70,60,100),self.btn_menu,1,border_radius=8)
            mt=self.fonts["small"].render("MENU",True,DIM_TEXT)
            self.screen.blit(mt,(self.btn_menu.centerx-mt.get_width()//2,self.btn_menu.centery-mt.get_height()//2))

    def _draw_game_complete(self):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,160)); self.screen.blit(ov,(0,0))
        title=self.fonts["title"].render("MISSION COMPLETE!",True,SUCCESS_COL)
        self.screen.blit(title,(WIDTH//2-title.get_width()//2,60))
        sub=self.fonts["med"].render(f"All {len(self.all_levels)} levels conquered!",True,TEXT_COL)
        self.screen.blit(sub,(WIDTH//2-sub.get_width()//2,120))
        ts=self.fonts["large"].render(f"Stars: {self.total_stars}/{len(self.all_levels)*3}",True,BONUS_COL)
        self.screen.blit(ts,(WIDTH//2-ts.get_width()//2,170))
        fs=self.fonts["large"].render(f"Score: {self.score}",True,BULLET_COL)
        self.screen.blit(fs,(WIDTH//2-fs.get_width()//2,215))
        self.btn_menu=pygame.Rect(WIDTH//2-100,HEIGHT-80,200,50)
        mx,my=pygame.mouse.get_pos(); hov=self.btn_menu.collidepoint(mx,my)
        pygame.draw.rect(self.screen,BUTTON_HOVER if hov else BUTTON_COL,self.btn_menu,border_radius=12)
        pygame.draw.rect(self.screen,BH_ACCRETION,self.btn_menu,2,border_radius=12)
        mt=self.fonts["med"].render("MAIN MENU",True,WHITE)
        self.screen.blit(mt,(self.btn_menu.centerx-mt.get_width()//2,self.btn_menu.centery-mt.get_height()//2))

    def _draw_load_dialog(self):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,160)); self.screen.blit(ov,(0,0))
        dw,dh=440,320; dx,dy=WIDTH//2-dw//2,HEIGHT//2-dh//2
        pygame.draw.rect(self.screen,ED_PANEL_BG,(dx,dy,dw,dh),border_radius=12)
        pygame.draw.rect(self.screen,BH_ACCRETION,(dx,dy,dw,dh),2,border_radius=12)
        ft=self.fonts["med"]; fs=self.fonts["small"]; fss=self.fonts["tiny"]
        t=ft.render("Load Level",True,WHITE); self.screen.blit(t,(WIDTH//2-t.get_width()//2,dy+10))
        # Close button
        close_rect=pygame.Rect(dx+dw-35,dy+5,30,30)
        pygame.draw.rect(self.screen,(100,40,40),close_rect,border_radius=4)
        ct=fss.render("X",True,WHITE); self.screen.blit(ct,(close_rect.centerx-ct.get_width()//2,close_rect.centery-ct.get_height()//2))
        # File list
        list_rect=pygame.Rect(dx+20,dy+50,dw-40,200)
        pygame.draw.rect(self.screen,(20,20,40),list_rect,border_radius=4)
        if not self.load_dialog_files:
            nt=fs.render("No custom levels found.",True,DIM_TEXT); self.screen.blit(nt,(list_rect.x+10,list_rect.y+10))
            nt2=fss.render(f"Create some in the Editor first!",True,DIM_TEXT); self.screen.blit(nt2,(list_rect.x+10,list_rect.y+35))
            nt3=fss.render(f"Levels folder: custom_levels/",True,DIM_TEXT); self.screen.blit(nt3,(list_rect.x+10,list_rect.y+55))
        else:
            mx,my=pygame.mouse.get_pos()
            visible = self.load_dialog_files[self.load_dialog_scroll:self.load_dialog_scroll+8]
            for i, path in enumerate(visible):
                name = os.path.basename(path)
                iy = list_rect.y + 5 + i * 25
                if iy + 25 > list_rect.y + list_rect.height: break
                item_rect = pygame.Rect(list_rect.x+5, iy, list_rect.width-10, 22)
                hov = item_rect.collidepoint(mx, my)
                pygame.draw.rect(self.screen, ED_TOOL_HOV if hov else (30,28,50), item_rect, border_radius=3)
                lt = fss.render(name, True, WHITE if hov else TEXT_COL)
                self.screen.blit(lt, (item_rect.x + 10, iy + 4))
        # Cancel
        cancel_rect=pygame.Rect(WIDTH//2-60,dy+dh-50,120,35)
        mx,my=pygame.mouse.get_pos(); hov=cancel_rect.collidepoint(mx,my)
        pygame.draw.rect(self.screen,BUTTON_HOVER if hov else BUTTON_COL,cancel_rect,border_radius=8)
        pygame.draw.rect(self.screen,(80,70,110),cancel_rect,1,border_radius=8)
        ct=fs.render("Cancel",True,TEXT_COL); self.screen.blit(ct,(cancel_rect.centerx-ct.get_width()//2,cancel_rect.centery-ct.get_height()//2))

    def run(self):
        running=True
        while running:
            dt=self.clock.tick(FPS)/1000.0; dt=min(dt,0.05)
            running=self.handle_events(); self.update(dt); self.draw()
        pygame.quit(); sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()