"""
TANK DAI CHIEN - ULTIMATE EDITION v3.0
========================================
Features:
- Tutorial / How to Play screen
- Enhanced Shop with upgrade tiers
- Themed maps (Desert, Snow, City, Jungle, Lava)
- Boss battles every 5th level
- Minimap
- Weather effects
- Screen transitions
- Enhanced particles & explosions
- Better HUD with skill indicators
- Achievement popups
- Smooth camera
- Premium visuals
"""
import pygame, sys, math, random, heapq, os
from sprites import SpriteCache, TS
from collections import deque
import collections
import numpy as np

# ═══════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════
COLS, ROWS = 26, 20
SW, SH = COLS * TS, ROWS * TS + 60
FPS = 60
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]

EMPTY = 0; BRICK = 1; STEEL = 2; GRASS = 3; WATER = 4; CRATE = 5; BASE = 6

MAP_THEMES = ["default", "desert", "snow", "city", "jungle", "lava"]

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Allow disabling fullscreen via env var (useful for debugging / windowed play)
START_WINDOWED = os.environ.get("TANK_WINDOWED", "0") == "1"
_screen_flags = (0 if START_WINDOWED else pygame.FULLSCREEN) | pygame.SCALED
screen = pygame.display.set_mode((SW, SH), _screen_flags)
pygame.display.set_caption("TANK DAI CHIEN - ULTIMATE")
clock = pygame.time.Clock()
is_fullscreen = not START_WINDOWED

def toggle_fullscreen():
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    flags = (pygame.FULLSCREEN if is_fullscreen else 0) | pygame.SCALED
    pygame.display.set_mode((SW, SH), flags)

try:
    FONT_BIG = pygame.font.SysFont("consolas", 36, bold=True)
    FONT_MED = pygame.font.SysFont("consolas", 20, bold=True)
    FONT_SM = pygame.font.SysFont("consolas", 14)
    FONT_TITLE = pygame.font.SysFont("consolas", 48, bold=True)
    FONT_HUGE = pygame.font.SysFont("consolas", 60, bold=True)
except Exception:
    FONT_BIG = pygame.font.Font(None, 40)
    FONT_MED = pygame.font.Font(None, 24)
    FONT_SM = pygame.font.Font(None, 16)
    FONT_TITLE = pygame.font.Font(None, 52)
    FONT_HUGE = pygame.font.Font(None, 64)

sprites = SpriteCache()

# ═══════════════════════════════════════
#  KAWAII UI PRIMITIVES
# ═══════════════════════════════════════
KAWAII_PALETTE = {
    "pink":     (255, 170, 210),
    "rose":     (255, 130, 170),
    "mint":     (130, 230, 200),
    "sky":      (140, 200, 255),
    "lavender": (200, 170, 255),
    "peach":    (255, 200, 140),
    "lemon":    (255, 240, 130),
    "cream":    (255, 245, 220),
    "ink":      (60, 50, 90),
    "shadow":   (35, 30, 60),
}

KAWAII_RAINBOW = [(255, 130, 170), (255, 200, 140), (255, 240, 130),
                  (130, 230, 200), (140, 200, 255), (200, 170, 255)]


def draw_kawaii_panel(surf, rect, fill=(60, 50, 95), border=(255, 200, 230),
                      radius=18, shadow_offset=4, glow=True):
    """Rounded gradient panel with soft drop shadow + optional pastel glow.

    Glow is rendered as an outer halo only (a slightly larger rounded rect
    behind the panel) so it never washes out the panel fill itself.
    """
    x, y, w, h = rect
    # Outer glow (drawn first, behind the panel + shadow)
    if glow:
        gpad = 14
        glow_surf = pygame.Surface((w + gpad * 2, h + gpad * 2), pygame.SRCALPHA)
        for i in range(4):
            a = 30 - i * 6
            if a <= 0:
                break
            pygame.draw.rect(glow_surf, (*border[:3], a),
                             (i, i, w + gpad * 2 - i * 2, h + gpad * 2 - i * 2),
                             border_radius=radius + gpad)
        surf.blit(glow_surf, (x - gpad, y - gpad))
    # Drop shadow
    if shadow_offset:
        sh = pygame.Surface((w + shadow_offset * 2, h + shadow_offset * 2), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 130),
                         (shadow_offset, shadow_offset, w, h), border_radius=radius)
        surf.blit(sh, (x - shadow_offset, y - shadow_offset))
    # Panel body (vertical gradient from `fill` to a slightly darker shade)
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        t = i / max(1, h - 1)
        col = (int(fill[0] * (1 - t * 0.35)),
               int(fill[1] * (1 - t * 0.35)),
               int(fill[2] * (1 - t * 0.25)))
        pygame.draw.line(panel, col, (0, i), (w, i))
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
    panel.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(panel, (x, y))
    pygame.draw.rect(surf, border, rect, 2, border_radius=radius)


def draw_kawaii_button(surf, rect, label, font, selected=False,
                       color_idx=0, tick=0, icon_fn=None):
    """Cute rounded button with pastel rainbow palette."""
    base_colors = [
        ((255, 170, 210), (255, 100, 160)),  # pink
        ((255, 220, 140), (255, 170, 60)),   # peach/orange
        ((180, 230, 255), (110, 180, 240)),  # sky
        ((200, 255, 200), (110, 220, 130)),  # mint
        ((220, 200, 255), (170, 130, 240)),  # lavender
    ]
    light, dark = base_colors[color_idx % len(base_colors)]
    x, y, w, h = rect
    pulse = (math.sin(tick * 0.08) + 1) * 0.5 if selected else 0
    # Shadow
    shadow = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 130), (3, 3, w, h), border_radius=h // 2)
    surf.blit(shadow, (x - 3, y - 3))
    # Body gradient
    body = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        t = i / max(1, h - 1)
        col = (int(light[0] * (1 - t * 0.4) + dark[0] * t * 0.4),
               int(light[1] * (1 - t * 0.4) + dark[1] * t * 0.4),
               int(light[2] * (1 - t * 0.4) + dark[2] * t * 0.4))
        pygame.draw.line(body, col, (0, i), (w, i))
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=h // 2)
    body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    # Top gloss highlight
    gloss = pygame.Surface((w, h // 2), pygame.SRCALPHA)
    for i in range(h // 2):
        a = int(160 * (1 - i / max(1, h // 2)))
        pygame.draw.line(gloss, (255, 255, 255, a), (0, i), (w, i))
    g_mask = pygame.Surface((w, h // 2), pygame.SRCALPHA)
    pygame.draw.rect(g_mask, (255, 255, 255, 255), (0, 0, w, h // 2),
                     border_radius=h // 2)
    gloss.blit(g_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    body.blit(gloss, (0, 2))
    surf.blit(body, (x, y))
    # Border
    border_col = (255, 255, 255) if selected else (90, 70, 110)
    pygame.draw.rect(surf, border_col, rect, 3, border_radius=h // 2)
    if selected:
        glow = pygame.Surface((w + 30, h + 30), pygame.SRCALPHA)
        pygame.draw.rect(glow, (255, 240, 200, int(60 + 80 * pulse)),
                         (0, 0, w + 30, h + 30), border_radius=h // 2 + 10)
        surf.blit(glow, (x - 15, y - 15), special_flags=pygame.BLEND_RGBA_ADD)
    # Icon (optional, drawn left)
    label_x = x + w // 2
    if icon_fn:
        icon_size = h - 14
        icon_fn(surf, x + 14, y + (h - icon_size) // 2, icon_size)
        label_x = x + w // 2 + 8
    # Label
    label_shadow = font.render(label, True, (40, 30, 60))
    label_surf = font.render(label, True, (255, 255, 255))
    surf.blit(label_shadow, (label_x - label_surf.get_width() // 2 + 2,
                             y + (h - label_surf.get_height()) // 2 + 2))
    surf.blit(label_surf, (label_x - label_surf.get_width() // 2,
                           y + (h - label_surf.get_height()) // 2))


def draw_rainbow_text(surf, text, pos, font, tick=0, jitter=True):
    """Render text with each character in a different pastel rainbow color
    and a small wave animation."""
    cx = pos[0]
    base_y = pos[1]
    total_w = sum(font.size(c)[0] for c in text)
    cx -= total_w // 2
    for i, ch in enumerate(text):
        col = KAWAII_RAINBOW[(i + tick // 6) % len(KAWAII_RAINBOW)]
        offset_y = int(math.sin(tick * 0.12 + i * 0.6) * 4) if jitter else 0
        # Outline
        outline = font.render(ch, True, (40, 30, 60))
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
            surf.blit(outline, (cx + dx, base_y + offset_y + dy))
        glyph = font.render(ch, True, col)
        surf.blit(glyph, (cx, base_y + offset_y))
        cx += font.size(ch)[0]


def draw_heart_icon(surf, x, y, size, filled=True, outline=(180, 30, 80)):
    """Cute pixel heart at (x, y) with given size."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    fill = (255, 100, 130) if filled else (90, 70, 80)
    # Two circles + triangle
    r = size // 4
    pygame.draw.circle(s, fill, (cx - r, cy - r // 2), r + 1)
    pygame.draw.circle(s, fill, (cx + r, cy - r // 2), r + 1)
    pts = [(cx - 2 * r, cy - r // 4), (cx + 2 * r, cy - r // 4),
           (cx, cy + size // 2 - 1)]
    pygame.draw.polygon(s, fill, pts)
    pygame.draw.circle(s, outline, (cx - r, cy - r // 2), r + 1, 2)
    pygame.draw.circle(s, outline, (cx + r, cy - r // 2), r + 1, 2)
    pygame.draw.lines(s, outline, False,
                      [(cx - 2 * r, cy - r // 4), (cx, cy + size // 2 - 1),
                       (cx + 2 * r, cy - r // 4)], 2)
    # Specular highlight
    pygame.draw.circle(s, (255, 230, 240), (cx - r, cy - r), max(1, r // 3))
    surf.blit(s, (x, y))


def draw_coin_icon(surf, x, y, size):
    """Gold coin with star, rotates slightly with time."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    pygame.draw.circle(s, (255, 200, 60), (cx, cy), size // 2 - 1)
    pygame.draw.circle(s, (200, 130, 30), (cx, cy), size // 2 - 1, 2)
    pygame.draw.circle(s, (255, 240, 160),
                       (cx - size // 6, cy - size // 6), max(1, size // 8))
    star = "*"
    f = pygame.font.SysFont("consolas", max(8, size - 6), bold=True)
    g = f.render(star, True, (180, 100, 30))
    s.blit(g, (cx - g.get_width() // 2, cy - g.get_height() // 2 - 1))
    surf.blit(s, (x, y))


def draw_gem_icon(surf, x, y, size):
    """Cyan diamond / gem icon."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = size // 2
    top = 1
    mid_y = size // 3
    bot = size - 2
    pts = [(cx, top), (size - 2, mid_y), (cx, bot), (1, mid_y)]
    pygame.draw.polygon(s, (140, 220, 255), pts)
    pygame.draw.polygon(s, (60, 140, 200), pts, 2)
    # Inner facets
    pygame.draw.line(s, (220, 245, 255), (cx, top), (cx, bot), 1)
    pygame.draw.line(s, (220, 245, 255), (cx, top), (1, mid_y), 1)
    pygame.draw.polygon(s, (255, 255, 255),
                        [(cx, top + 1), (cx + 3, mid_y - 2), (cx - 1, mid_y - 1)])
    surf.blit(s, (x, y))


def draw_sparkle(surf, x, y, size, color=(255, 255, 200), alpha=255):
    """4-point sparkle / star burst."""
    s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    cx = size
    pygame.draw.line(s, (*color, alpha), (cx, 0), (cx, size * 2 - 1), 2)
    pygame.draw.line(s, (*color, alpha), (0, cx), (size * 2 - 1, cx), 2)
    pygame.draw.line(s, (*color, alpha // 2),
                     (size // 2, size // 2), (size + size // 2, size + size // 2), 1)
    pygame.draw.line(s, (*color, alpha // 2),
                     (size + size // 2, size // 2), (size // 2, size + size // 2), 1)
    pygame.draw.circle(s, (255, 255, 255, alpha), (cx, cx), 2)
    surf.blit(s, (x - cx, y - cx))


def draw_pastel_starfield(surf, tick, density=70):
    """Animated background of soft pastel sparkles + drifting stars."""
    for i in range(density):
        x = (i * 71 + tick * 0.4) % SW
        y = (i * 53 + tick * 0.18) % SH
        col = KAWAII_RAINBOW[i % len(KAWAII_RAINBOW)]
        pulse = abs(math.sin(tick * 0.04 + i * 0.7))
        a = int(60 + pulse * 140)
        sz = 1 + (i % 3)
        ps = pygame.Surface((sz * 2 + 4, sz * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(ps, (*col, a), (sz + 2, sz + 2), sz)
        surf.blit(ps, (int(x), int(y)))
        if i % 9 == 0:
            draw_sparkle(surf, int(x), int(y), 6,
                         color=(255, 255, 220), alpha=int(120 * pulse + 40))


# ═══════════════════════════════════════
#  SOUND FX
# ═══════════════════════════════════════
def gen_sound(freq, dur=0.08, vol=0.3, wave="sine"):
    sr = 44100; n = int(sr * dur); t = np.linspace(0, dur, n, False)
    if wave == "sine": w = np.sin(freq * t * 2 * np.pi)
    elif wave == "noise": w = np.random.uniform(-1, 1, n)
    else: w = np.sign(np.sin(freq * t * 2 * np.pi))
    env = np.ones(n); fl = int(n * 0.1)
    if fl > 0: env[:fl] = np.linspace(0, 1, fl); env[-fl:] = np.linspace(1, 0, fl)
    a = (w * env * vol * 32767).astype(np.int16)
    st = np.empty((n, 2), dtype=np.int16); st[:, 0] = a; st[:, 1] = a
    return pygame.sndarray.make_sound(st)

snd_shoot = gen_sound(600, 0.06, 0.2)
snd_explode = gen_sound(100, 0.3, 0.4, "noise")
snd_pickup = gen_sound(880, 0.1, 0.3)
snd_hit = gen_sound(200, 0.15, 0.3, "noise")
snd_steel = gen_sound(1200, 0.05, 0.15)
snd_combo = gen_sound(900, 0.2, 0.35, "square")
snd_levelup = gen_sound(440, 0.4, 0.3, "sine")
snd_boss_alert = gen_sound(150, 0.5, 0.4, "square")
snd_buy = gen_sound(660, 0.12, 0.25)
snd_deny = gen_sound(200, 0.2, 0.2, "square")

# ═══════════════════════════════════════
#  BACKGROUND MUSIC
# ═══════════════════════════════════════
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

try:
    pygame.mixer.music.load(resource_path("nhacnen.mp3"))
    pygame.mixer.music.set_volume(0.6)
except Exception as e:
    print(f"Music load error: {e}")

# ═══════════════════════════════════════
#  SCREEN TRANSITION
# ═══════════════════════════════════════
class Transition:
    def __init__(self):
        self.active = False
        self.alpha = 0
        self.target_alpha = 0
        self.speed = 8
        self.callback = None
        self.phase = "idle"

    def start(self, callback=None):
        self.active = True
        self.phase = "fade_out"
        self.alpha = 0
        self.target_alpha = 255
        self.callback = callback

    def update(self):
        if not self.active:
            return
        if self.phase == "fade_out":
            self.alpha = min(255, self.alpha + self.speed)
            if self.alpha >= 255:
                if self.callback:
                    self.callback()
                    self.callback = None
                self.phase = "fade_in"
        elif self.phase == "fade_in":
            self.alpha = max(0, self.alpha - self.speed)
            if self.alpha <= 0:
                self.active = False
                self.phase = "idle"

    def draw(self, surf):
        if not self.active or self.alpha <= 0:
            return
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(self.alpha)))
        surf.blit(overlay, (0, 0))

transition = Transition()

# ═══════════════════════════════════════
#  WEATHER SYSTEM
# ═══════════════════════════════════════
class WeatherSystem:
    def __init__(self):
        self.particles = []
        self.weather_type = None
        self.intensity = 50

    def set_weather(self, theme):
        self.particles.clear()
        if theme == "snow":
            self.weather_type = "snow"
            self.intensity = 60
        elif theme == "desert":
            self.weather_type = "sand"
            self.intensity = 30
        elif theme == "jungle":
            self.weather_type = "rain"
            self.intensity = 50
        elif theme == "lava":
            self.weather_type = "ember"
            self.intensity = 25
        else:
            self.weather_type = None

    def update(self):
        if not self.weather_type:
            return

        while len(self.particles) < self.intensity:
            if self.weather_type == "snow":
                self.particles.append({
                    'x': random.randint(0, SW), 'y': random.randint(-20, 0),
                    'vx': random.uniform(-0.5, 0.5), 'vy': random.uniform(0.5, 2),
                    'size': random.randint(2, 4), 'alpha': random.randint(100, 200)
                })
            elif self.weather_type == "rain":
                self.particles.append({
                    'x': random.randint(0, SW), 'y': random.randint(-30, 0),
                    'vx': random.uniform(-1, 0), 'vy': random.uniform(6, 12),
                    'size': random.randint(1, 2), 'alpha': random.randint(80, 150)
                })
            elif self.weather_type == "sand":
                self.particles.append({
                    'x': random.randint(-20, 0), 'y': random.randint(0, SH),
                    'vx': random.uniform(2, 5), 'vy': random.uniform(-0.5, 0.5),
                    'size': random.randint(1, 3), 'alpha': random.randint(60, 120)
                })
            elif self.weather_type == "ember":
                self.particles.append({
                    'x': random.randint(0, SW), 'y': random.randint(SH, SH + 20),
                    'vx': random.uniform(-0.5, 0.5), 'vy': random.uniform(-2, -0.5),
                    'size': random.randint(1, 3), 'alpha': random.randint(100, 200)
                })

        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            if self.weather_type == "snow":
                p['x'] += math.sin(p['y'] * 0.02) * 0.5
            if (p['y'] > SH + 10 or p['y'] < -30 or p['x'] > SW + 10 or p['x'] < -30):
                self.particles.remove(p)

    def draw(self, surf):
        if not self.weather_type:
            return
        for p in self.particles:
            if self.weather_type == "snow":
                c = (230, 235, 255, p['alpha'])
            elif self.weather_type == "rain":
                c = (150, 180, 255, p['alpha'])
            elif self.weather_type == "sand":
                c = (200, 180, 140, p['alpha'])
            elif self.weather_type == "ember":
                c = (255, random.randint(100, 200), 50, p['alpha'])
            else:
                continue
            ps = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            if self.weather_type == "rain":
                pygame.draw.line(ps, c, (p['size'], 0), (0, p['size'] * 2), 1)
            else:
                pygame.draw.circle(ps, c, (p['size'], p['size']), p['size'])
            surf.blit(ps, (int(p['x']), int(p['y'])))

weather = WeatherSystem()

# ═══════════════════════════════════════
#  ACHIEVEMENT SYSTEM
# ═══════════════════════════════════════
class Achievement:
    def __init__(self, name, desc, icon_color):
        self.name = name
        self.desc = desc
        self.icon_color = icon_color
        self.timer = 180
        self.y_offset = -60

achievement_queue = []

def trigger_achievement(name, desc, color=(255, 220, 50)):
    achievement_queue.append(Achievement(name, desc, color))

# ═══════════════════════════════════════
#  PATHFINDER
# ═══════════════════════════════════════
class Pathfinder:
    @staticmethod
    def a_star_path(grid, start, goal, avoid_tanks=None):
        if start == goal: return [start]
        pq = [(0, start)]
        came_from = {start: None}
        cost_so_far = {start: 0}

        while pq:
            _, current = heapq.heappop(pq)
            if current == goal: break
            for dx, dy in DIRS:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < COLS and 0 <= neighbor[1] < ROWS:
                    tile = grid[neighbor[1]][neighbor[0]]
                    if tile in (STEEL, WATER, BASE): continue
                    move_cost = 1
                    if tile in (BRICK, CRATE): move_cost = 8
                    if avoid_tanks and neighbor in avoid_tanks and neighbor != start:
                        move_cost += 5
                    new_cost = cost_so_far[current] + move_cost
                    if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                        cost_so_far[neighbor] = new_cost
                        priority = new_cost + abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                        heapq.heappush(pq, (priority, neighbor))
                        came_from[neighbor] = current

        path = []
        c = goal
        while c is not None and c in came_from:
            path.append(c)
            c = came_from[c]
        path.reverse()
        return path if path and path[0] == start else [start]

    @staticmethod
    def bfs_path(grid, start, goal, avoid_tanks=None):
        if start == goal: return [start]
        queue = collections.deque([start])
        came_from = {start: None}
        blocked = {STEEL, WATER, BASE, BRICK, CRATE}
        while queue:
            current = queue.popleft()
            if current == goal: break
            for dx, dy in DIRS:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < COLS and 0 <= neighbor[1] < ROWS:
                    if neighbor not in came_from:
                        tile = grid[neighbor[1]][neighbor[0]]
                        is_blocked = tile in blocked
                        if avoid_tanks and neighbor in avoid_tanks: is_blocked = True
                        if neighbor == goal: is_blocked = False
                        if not is_blocked:
                            queue.append(neighbor)
                            came_from[neighbor] = current
        path = []
        c = goal
        while c is not None and c in came_from:
            path.append(c)
            c = came_from[c]
        path.reverse()
        return path if path and path[0] == start else [start]

    @staticmethod
    def dfs_path(grid, start, goal, avoid_tanks=None):
        if start == goal: return [start]
        stack = [start]
        came_from = {start: None}
        blocked = {STEEL, WATER, BASE, BRICK, CRATE}
        while stack:
            current = stack.pop()
            if current == goal: break
            for dx, dy in DIRS:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < COLS and 0 <= neighbor[1] < ROWS:
                    if neighbor not in came_from:
                        tile = grid[neighbor[1]][neighbor[0]]
                        is_blocked = tile in blocked
                        if avoid_tanks and neighbor in avoid_tanks: is_blocked = True
                        if neighbor == goal: is_blocked = False
                        if not is_blocked:
                            stack.append(neighbor)
                            came_from[neighbor] = current
        path = []
        c = goal
        while c is not None and c in came_from:
            path.append(c)
            c = came_from[c]
        path.reverse()
        return path if path and path[0] == start else [start]

    @staticmethod
    def can_shoot(grid, sx, sy, tx, ty):
        if sx == tx:
            step = 1 if ty > sy else -1
            for y in range(sy + step, ty, step):
                if grid[y][sx] in (STEEL, WATER, BASE): return False
            return True
        if sy == ty:
            step = 1 if tx > sx else -1
            for x in range(sx + step, tx, step):
                if grid[sy][x] in (STEEL, WATER, BASE): return False
            return True
        return False

    @staticmethod
    def get_next_direction(current_pos, next_pos):
        cx, cy = current_pos
        nx, ny = next_pos
        if nx > cx: return 1
        if nx < cx: return 3
        if ny > cy: return 2
        if ny < cy: return 0
        return -1

    @staticmethod
    def get_safe_directions(grid, x, y):
        gx, gy = int(x // TS), int(y // TS)
        blocked = {STEEL, WATER, BASE}
        safe = []
        for d in range(4):
            dx, dy = DIRS[d]
            nx, ny = gx + dx, gy + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                if grid[ny][nx] not in blocked:
                    safe.append(d)
        return safe

# ═══════════════════════════════════════
#  MAP GENERATOR (THEMED)
# ═══════════════════════════════════════
def generate_map(level=1, cols=26, rows=20):
    global COLS, ROWS
    COLS, ROWS = cols, rows
    grid = [[EMPTY] * cols for _ in range(rows)]

    for x in range(cols):
        grid[0][x] = STEEL
        grid[rows - 1][x] = STEEL
    for y in range(rows):
        grid[y][0] = STEEL
        grid[y][cols - 1] = STEEL

    def is_protected(px, py):
        if py == 1 or py == 2: return True
        if py == rows - 2 or py == rows - 3: return True
        if abs(px - cols // 2) <= 1: return True
        if abs(px - cols // 2) <= 3 and py >= rows - 5: return True
        if py <= 3 and (px <= 3 or px >= cols - 4): return True
        return False

    # Dynamic shapes for higher levels
    if level >= 4:
        shape_type = level % 3
        if shape_type == 1:
            for y in range(1, rows // 2 + 1):
                for x in range(cols // 2 + 1, cols - 1):
                    if not is_protected(x, y): grid[y][x] = STEEL
        elif shape_type == 2:
            sz = min(cols, rows) // 4
            for y in range(1, rows - 1):
                for x in range(1, cols - 1):
                    in_corners = ((x < sz and y < sz) or (x > cols - 1 - sz and y < sz) or
                                  (x < sz and y > rows - 1 - sz) or (x > cols - 1 - sz and y > rows - 1 - sz))
                    if in_corners and not is_protected(x, y):
                        grid[y][x] = STEEL
        else:
            sz = min(cols, rows) // 3
            for y in range(1, rows - 1):
                for x in range(1, cols - 1):
                    if (x + y < sz or (cols - x) + y < sz or x + (rows - y) < sz or (cols - x) + (rows - y) < sz):
                        if not is_protected(x, y): grid[y][x] = STEEL

    # Base
    bx, by = cols // 2, rows - 3
    grid[by][bx] = BASE
    for dx in range(-1, 2):
        for dy in range(-1, 1):
            nx, ny = bx + dx, by + dy
            if 1 <= nx < cols - 1 and 1 <= ny < rows - 1 and grid[ny][nx] == EMPTY:
                grid[ny][nx] = BRICK

    # Random structures
    num_structures = 8 + level * 2
    for _ in range(num_structures):
        sx = random.randint(2, cols - 4)
        sy = random.randint(2, rows - 5)
        stype = random.choice([BRICK, BRICK, BRICK, STEEL, GRASS])
        shape = random.choice(["h", "v", "L", "box", "T", "cross"])
        cells = []
        if shape == "h":
            cells = [(sx + i, sy) for i in range(random.randint(2, 4))]
        elif shape == "v":
            cells = [(sx, sy + i) for i in range(random.randint(2, 4))]
        elif shape == "L":
            cells = [(sx + i, sy) for i in range(3)] + [(sx, sy + i) for i in range(1, 3)]
        elif shape == "box":
            cells = [(sx + i, sy + j) for i in range(2) for j in range(2)]
        elif shape == "T":
            cells = [(sx + i, sy) for i in range(3)] + [(sx + 1, sy + j) for j in range(1, 3)]
        elif shape == "cross":
            cells = [(sx + 1, sy), (sx, sy + 1), (sx + 1, sy + 1), (sx + 2, sy + 1), (sx + 1, sy + 2)]
        for cx, cy in cells:
            if 1 <= cx < cols - 1 and 1 <= cy < rows - 1 and grid[cy][cx] == EMPTY:
                grid[cy][cx] = stype

    # Water
    for _ in range(1 + level // 2):
        wx, wy = random.randint(3, cols - 5), random.randint(3, rows - 6)
        for dx in range(random.randint(1, 3)):
            for dy in range(random.randint(1, 2)):
                if 1 <= wx + dx < cols - 1 and 1 <= wy + dy < rows - 1 and grid[wy + dy][wx + dx] == EMPTY:
                    grid[wy + dy][wx + dx] = WATER

    # Crates
    for _ in range(3 + level // 2):
        cx, cy = random.randint(2, cols - 3), random.randint(2, rows - 4)
        if grid[cy][cx] == EMPTY:
            grid[cy][cx] = CRATE

    return grid, (bx, by)

# ═══════════════════════════════════════
#  BULLET
# ═══════════════════════════════════════
class Bullet:
    def __init__(self, x, y, direction, owner, speed=6, power=1, kind="normal", angle_offset=0):
        self.x, self.y = float(x), float(y)
        self.dir = direction
        self.owner = owner
        self.speed = speed
        self.power = power
        self.kind = kind
        self.alive = True
        self.angle_offset = angle_offset
        self.trail = []

    def update(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)

        dx, dy = DIRS[self.dir]
        if self.angle_offset != 0:
            rad = math.radians(self.angle_offset)
            nx = dx * math.cos(rad) - dy * math.sin(rad)
            ny = dx * math.sin(rad) + dy * math.cos(rad)
            self.x += nx * self.speed
            self.y += ny * self.speed
        else:
            self.x += dx * self.speed
            self.y += dy * self.speed

        if self.x < -100 or self.x >= COLS * TS + 100 or self.y < -100 or self.y >= ROWS * TS + 100:
            self.alive = False

    def get_grid(self):
        return int(self.x // TS), int(self.y // TS)

    def draw(self, surf, offset=(0, 0), scale=1.0):
        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            dtx = int((tx - offset[0]) * scale)
            dty = int((ty - offset[1]) * scale)
            a = int(60 * (i / max(1, len(self.trail))))
            sz = max(1, int(2 * scale * (i / max(1, len(self.trail)))))
            trail_c = (255, 200, 50) if self.owner == "player" else (255, 100, 80)
            ts = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(ts, (*trail_c, a), (sz, sz), sz)
            surf.blit(ts, (dtx - sz, dty - sz))

        draw_x = int((self.x - offset[0]) * scale)
        draw_y = int((self.y - offset[1]) * scale)

        img = sprites.bullet
        if self.owner != "player": img = sprites.bullet_enemy
        if self.kind == "pierce": img = sprites.bullet_pierce
        if self.kind == "bomb": img = sprites.bullet_bomb
        if self.kind == "laser": img = sprites.bullet_laser
        if self.kind == "plasma": img = sprites.bullet_plasma

        if scale != 1.0:
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
        surf.blit(img, (draw_x - img.get_width() // 2, draw_y - img.get_height() // 2))

# ═══════════════════════════════════════
#  CHICKEN & DOG
# ═══════════════════════════════════════
class Chicken:
    def __init__(self, gx, gy):
        self.x = float(gx * TS + TS // 2)
        self.y = float(gy * TS + TS // 2)
        self.dir = random.randint(0, 3)
        self.speed = 0.8
        self.alive = True
        self.frame = 0
        self.move_timer = 0

    def update(self, grid):
        self.frame = (self.frame + 0.1) % 8
        if self.move_timer <= 0:
            self.dir = random.randint(0, 3)
            self.move_timer = random.randint(30, 90)
        dx, dy = DIRS[self.dir]
        nx, ny = self.x + dx * self.speed, self.y + dy * self.speed
        gx, gy = int(nx // TS), int(ny // TS)
        if 0 <= gx < COLS and 0 <= gy < ROWS and grid[gy][gx] == EMPTY:
            self.x, self.y = nx, ny
        else:
            self.move_timer = 0
        self.move_timer -= 1

    def draw(self, surf, tick, offset=(0, 0), scale=1.0):
        draw_x = int((self.x - offset[0]) * scale)
        draw_y = int((self.y - offset[1]) * scale)
        img = sprites.chicken_frames[int(self.frame)]
        if scale != 1.0:
            img = pygame.transform.scale(img, (int(32 * scale), int(32 * scale)))
        surf.blit(img, (draw_x - img.get_width() // 2, draw_y - img.get_height() // 2))

class Dog:
    def __init__(self, gx, gy):
        self.x = float(gx * TS + TS // 2)
        self.y = float(gy * TS + TS // 2)
        self.dir = 2
        self.speed = 2.0
        self.alive = True
        self.frame = 0
        self.bite_cooldown = 0
        self.state = "idle"
        self.dir_key = "down"
        self.move_timer = 0
        self.frozen_timer = 0

    def update(self, grid, player_pos):
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            return
        self.frame = (self.frame + 0.15) % 4
        if self.bite_cooldown > 0: self.bite_cooldown -= 1
        dist = math.hypot(self.x - player_pos[0], self.y - player_pos[1])
        if dist < 250:
            self.state = "chase"
            dx = 1 if player_pos[0] > self.x else -1
            dy = 1 if player_pos[1] > self.y else -1
            if abs(player_pos[0] - self.x) < 5: dx = 0
            if abs(player_pos[1] - self.y) < 5: dy = 0
            if abs(dx) > abs(dy):
                self.dir_key = "right" if dx > 0 else "left"
            else:
                self.dir_key = "down" if dy > 0 else "up"
            nx, ny = self.x + dx * self.speed, self.y + dy * self.speed
            gx, gy = int(nx // TS), int(ny // TS)
            if 0 <= gx < COLS and 0 <= gy < ROWS and grid[gy][gx] not in (STEEL, WATER):
                self.x, self.y = nx, ny
        else:
            self.state = "idle"
            if self.move_timer <= 0:
                self.dir = random.randint(0, 3)
                self.move_timer = random.randint(60, 150)
                self.dir_key = ["up", "right", "down", "left"][self.dir]
            dx, dy = DIRS[self.dir]
            nx, ny = self.x + dx * 0.5, self.y + dy * 0.5
            gx, gy = int(nx // TS), int(ny // TS)
            if 0 <= gx < COLS and 0 <= gy < ROWS and grid[gy][gx] == EMPTY:
                self.x, self.y = nx, ny
            else:
                self.move_timer = 0
            self.move_timer -= 1

    def draw(self, surf, tick, offset=(0, 0), scale=1.0):
        draw_x = int((self.x - offset[0]) * scale)
        draw_y = int((self.y - offset[1]) * scale)
        img = sprites.dog_frames.get(self.dir_key, sprites.dog_frames["down"])[int(self.frame)]
        if scale != 1.0:
            img = pygame.transform.scale(img, (int(36 * scale), int(36 * scale)))
        surf.blit(img, (draw_x - img.get_width() // 2, draw_y - img.get_height() // 2))

# ═══════════════════════════════════════
#  EXPLOSION
# ═══════════════════════════════════════
class Explosion:
    def __init__(self, x, y, big=False):
        self.x, self.y = x, y
        self.frame = 0
        self.speed = 0.3 if big else 0.5
        self.big = big
        self.done = False

    def update(self):
        self.frame += self.speed
        if self.frame >= len(sprites.explosion):
            self.done = True

    def draw(self, surf, offset=(0, 0), scale=1.0):
        if self.done: return
        img = sprites.explosion[int(self.frame)]
        base_scale = 1.8 if self.big else 1.0
        final_scale = base_scale * scale
        w, h = int(96 * final_scale), int(96 * final_scale)
        img = pygame.transform.scale(img, (w, h))
        draw_x = int((self.x - offset[0]) * scale)
        draw_y = int((self.y - offset[1]) * scale)
        surf.blit(img, (draw_x - w // 2, draw_y - h // 2))

# ═══════════════════════════════════════
#  ITEM DROP
# ═══════════════════════════════════════
class Item:
    def __init__(self, gx, gy, kind):
        self.gx, self.gy = gx, gy
        self.kind = kind
        self.timer = 600
        self.alive = True

    def update(self):
        self.timer -= 1
        if self.timer <= 0: self.alive = False

    def draw(self, surf, tick, offset=(0, 0), scale=1.0):
        if not self.alive: return
        bob = int(math.sin(tick * 0.1) * 3)
        draw_x = int((self.gx * TS + TS // 2 - offset[0]) * scale)
        draw_y = int((self.gy * TS + TS // 2 + bob - offset[1]) * scale)

        pulse = abs(math.sin(tick * 0.08))
        r = int((16 + pulse * 4) * scale)
        a = int(30 + pulse * 30)
        colors = {"health": (255, 80, 80), "shield": (80, 140, 255), "speed": (80, 255, 130),
                  "star": (255, 215, 0), "money": (255, 220, 50), "life": (255, 50, 150),
                  "rapid": (255, 150, 40), "multi": (220, 200, 40), "pierce": (80, 200, 255),
                  "bomb": (150, 150, 150), "laser": (0, 255, 180), "plasma": (200, 50, 255),
                  "freeze": (120, 220, 255), "max_power": (255, 200, 60), "grenade": (90, 200, 90)}
        c = colors.get(self.kind, (255, 255, 100))

        gs = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*c, a), (r * 2, r * 2), r * 2)
        surf.blit(gs, (draw_x - r * 2, draw_y - r * 2))

        if self.kind in sprites.items:
            img = sprites.items[self.kind]
        else:
            img = sprites.items.get("health", sprites.items[list(sprites.items.keys())[0]])
        if scale != 1.0:
            img = pygame.transform.scale(img, (int(30 * scale), int(30 * scale)))
        surf.blit(img, (draw_x - img.get_width() // 2, draw_y - img.get_height() // 2))

# ═══════════════════════════════════════
#  TANK
# ═══════════════════════════════════════
class Tank:
    def __init__(self, gx, gy, tank_type="player"):
        self.x = float(gx * TS + TS // 2)
        self.y = float(gy * TS + TS // 2)
        self.dir = 0
        self.speed = 1.8
        self.sprint_multiplier = 1.0
        self.energy = 100
        self.max_energy = 100
        self.hp = 3
        self.max_hp = 3
        self.alive = True
        self.tank_type = tank_type
        self.shoot_cd = 0
        self.shoot_delay = 20
        self.bullet_speed = 6
        self.bullet_power = 1
        self.shield = 0
        self.spawn_timer = 60
        self.flash = 0
        self.skill = None
        self.skill_timer = 0
        self.skill_ammo = 0
        self.muzzle_frame = -1
        self.frozen_timer = 0
        self.tier = 0  # player upgrade tier (0..4)
        self.name = ""  # optional name tag (player only)

    def get_grid(self):
        return int(self.x // TS), int(self.y // TS)

    def get_center(self):
        return self.x, self.y

    def can_move_to(self, nx, ny, grid, other_tanks=None):
        half = TS // 2 - 3
        corners = [(nx - half, ny - half), (nx + half, ny - half),
                   (nx - half, ny + half), (nx + half, ny + half)]
        for cx, cy in corners:
            gx, gy = int(cx // TS), int(cy // TS)
            if gx < 0 or gy < 0 or gx >= COLS or gy >= ROWS:
                return False
            if grid[gy][gx] in (BRICK, STEEL, WATER, CRATE, BASE):
                return False
        if other_tanks:
            for other in other_tanks:
                if other is self or not other.alive: continue
                ox, oy = other.get_center()
                new_dist = math.hypot(nx - ox, ny - oy)
                if new_dist < TS - 4:
                    old_dist = math.hypot(self.x - ox, self.y - oy)
                    if new_dist < old_dist:
                        return False
        return True

    def move(self, dx, dy, grid, other_tanks=None):
        if dx == 0 and dy == 0: return False
        if abs(dx) > abs(dy):
            self.dir = 1 if dx > 0 else 3
        else:
            self.dir = 0 if dy < 0 else 2

        nx, ny = self.x + dx, self.y + dy
        spd = math.hypot(dx, dy)
        alignment_strength = 0.3

        if abs(dx) <= abs(dy) * 0.5:
            target_x = int(self.x // TS) * TS + TS / 2.0
            nx += (target_x - self.x) * alignment_strength
        elif abs(dy) <= abs(dx) * 0.5:
            target_y = int(self.y // TS) * TS + TS / 2.0
            ny += (target_y - self.y) * alignment_strength

        if self.can_move_to(nx, ny, grid, other_tanks):
            self.x, self.y = nx, ny
            return True
        else:
            full_dx = math.copysign(spd, dx) if dx != 0 else 0
            full_dy = math.copysign(spd, dy) if dy != 0 else 0

            can_x = dx != 0 and self.can_move_to(self.x + full_dx, self.y, grid, other_tanks)
            can_y = dy != 0 and self.can_move_to(self.x, self.y + full_dy, grid, other_tanks)

            if can_x and not can_y:
                self.x += full_dx
                self.dir = 1 if dx > 0 else 3
                return True
            elif can_y and not can_x:
                self.y += full_dy
                self.dir = 0 if dy < 0 else 2
                return True
            elif can_x and can_y:
                if abs(dx) > abs(dy):
                    self.x += full_dx; self.dir = 1 if dx > 0 else 3
                else:
                    self.y += full_dy; self.dir = 0 if dy < 0 else 2
                return True

            if self.can_move_to(nx, self.y, grid, other_tanks) and nx != self.x:
                self.x = nx; return True
            if self.can_move_to(self.x, ny, grid, other_tanks) and ny != self.y:
                self.y = ny; return True
        return False

    def shoot(self):
        if self.shoot_cd > 0 or not self.alive: return []
        if self.skill == "rapid" and self.skill_ammo > 0:
            self.shoot_cd = 5
            self.skill_ammo -= 1
            if self.skill_ammo <= 0: self.skill = None
        else:
            self.shoot_cd = self.shoot_delay

        dx, dy = DIRS[self.dir]
        bx = self.x + dx * (TS // 2 + 2)
        by = self.y + dy * (TS // 2 + 2)
        snd_shoot.play()
        self.muzzle_frame = 0

        if self.skill == "ammo" and self.skill_timer > 0:
            bullets = [
                Bullet(bx, by, self.dir, self.tank_type, self.bullet_speed, self.bullet_power),
                Bullet(bx, by, self.dir, self.tank_type, self.bullet_speed, self.bullet_power, angle_offset=-25),
                Bullet(bx, by, self.dir, self.tank_type, self.bullet_speed, self.bullet_power, angle_offset=25),
            ]
            return bullets

        bullet_kind = "normal"
        if self.skill in ("pierce", "bomb", "laser", "plasma"):
            bullet_kind = self.skill
        return [Bullet(bx, by, self.dir, self.tank_type, self.bullet_speed, self.bullet_power, kind=bullet_kind)]

    def hit(self, power=1):
        if self.shield > 0:
            self.shield -= 1
            snd_steel.play()
            return False
        self.hp -= power
        self.flash = 10
        if self.hp <= 0:
            self.alive = False
            return True
        snd_hit.play()
        return False

    def update(self):
        if self.shoot_cd > 0: self.shoot_cd -= 1
        if self.spawn_timer > 0: self.spawn_timer -= 1
        if self.flash > 0: self.flash -= 1
        if self.skill_timer > 0:
            self.skill_timer -= 1
            if self.skill_timer == 0: self.skill = None
        if self.muzzle_frame >= 0: self.muzzle_frame += 0.5
        if self.muzzle_frame >= len(sprites.muzzle_flash): self.muzzle_frame = -1

    def draw(self, surf, tick, offset=(0, 0), scale=1.0):
        if not self.alive: return
        draw_x = int((self.x - offset[0]) * scale)
        draw_y = int((self.y - offset[1]) * scale)
        s_ts = int(TS * scale)

        if self.spawn_timer > 0:
            fi = int((60 - self.spawn_timer) / 60 * len(sprites.spawn_effect))
            fi = max(0, min(len(sprites.spawn_effect) - 1, fi))
            img = sprites.spawn_effect[fi]
            if scale != 1.0: img = pygame.transform.scale(img, (s_ts + 8, s_ts + 8))
            surf.blit(img, (draw_x - s_ts // 2 - 4, draw_y - s_ts // 2 - 4))
            if tick % 4 < 2: return

        # Player aura
        if self.tank_type == "player":
            pulse = abs(math.sin(tick * 0.1))
            r = int((s_ts // 2 + 4 + pulse * 4))
            a = int(40 + pulse * 40)
            gs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            if self.sprint_multiplier > 1.0:
                aura_c = (255, 200, 50, a)
            elif self.shield > 0:
                aura_c = (80, 150, 255, a + 20)
            else:
                aura_c = (100, 255, 150, a)
            pygame.draw.circle(gs, aura_c, (r, r), r)
            surf.blit(gs, (draw_x - r, draw_y - r))

        # Shield visual
        if self.shield > 0:
            shield_pulse = abs(math.sin(tick * 0.15))
            sr = int(s_ts // 2 + 6 + shield_pulse * 2)
            ss = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(ss, (80, 150, 255, int(60 + shield_pulse * 40)), (sr, sr), sr, 2)
            surf.blit(ss, (draw_x - sr, draw_y - sr))

        tank_key = self.tank_type
        if tank_key == "player":
            tier = max(0, min(len(sprites.player_tiers) - 1, getattr(self, "tier", 0)))
            img = sprites.player_tiers[tier][self.dir]
        else:
            if tank_key not in sprites.tanks:
                tank_key = "enemy_a"
            img = sprites.tanks[tank_key][self.dir]
        if scale != 1.0: img = pygame.transform.scale(img, (s_ts, s_ts))

        if self.flash > 0 and tick % 3 < 1:
            white_img = img.copy()
            white_img.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(white_img, (draw_x - s_ts // 2, draw_y - s_ts // 2))
        else:
            surf.blit(img, (draw_x - s_ts // 2, draw_y - s_ts // 2))

        # Frozen overlay
        if getattr(self, "frozen_timer", 0) > 0:
            ice_alpha = int(120 + 60 * abs(math.sin(tick * 0.2)))
            ice = pygame.Surface((s_ts, s_ts), pygame.SRCALPHA)
            ice.fill((140, 220, 255, ice_alpha // 2))
            surf.blit(ice, (draw_x - s_ts // 2, draw_y - s_ts // 2), special_flags=pygame.BLEND_RGBA_ADD)
            # Ice crystals around tank
            cr = s_ts // 2 + 2
            cs = pygame.Surface((cr * 2, cr * 2), pygame.SRCALPHA)
            for ang in range(0, 360, 60):
                rad = math.radians(ang + tick * 1.5)
                xx = cr + math.cos(rad) * cr
                yy = cr + math.sin(rad) * cr
                pygame.draw.circle(cs, (200, 240, 255, 220), (int(xx), int(yy)), 2)
            surf.blit(cs, (draw_x - cr, draw_y - cr))

        # Muzzle flash
        if self.muzzle_frame >= 0 and self.muzzle_frame < len(sprites.muzzle_flash):
            mf_img = sprites.muzzle_flash[int(self.muzzle_frame)]
            mdx, mdy = DIRS[self.dir]
            mx = draw_x + mdx * (s_ts // 2 + 4)
            my = draw_y + mdy * (s_ts // 2 + 4)
            if scale != 1.0:
                mf_img = pygame.transform.scale(mf_img, (int(24 * scale), int(24 * scale)))
            surf.blit(mf_img, (mx - mf_img.get_width() // 2, my - mf_img.get_height() // 2))

        # HP bar
        if self.tank_type == "player" or self.flash > 0:
            bw = int(28 * scale)
            bx_bar = draw_x - bw // 2
            by_bar = draw_y - s_ts // 2 - int(8 * scale)
            pygame.draw.rect(surf, (20, 20, 20), (bx_bar - 1, by_bar - 1, bw + 2, 6), border_radius=2)
            hw = int(bw * self.hp / self.max_hp)
            c = (80, 220, 80) if self.hp > 1 else (220, 60, 60)
            pygame.draw.rect(surf, c, (bx_bar, by_bar, hw, 4), border_radius=2)

            if self.tank_type == "player":
                ey = by_bar + 6
                pygame.draw.rect(surf, (20, 20, 20), (bx_bar - 1, ey, bw + 2, 4), border_radius=1)
                ew = int(bw * self.energy / self.max_energy)
                pygame.draw.rect(surf, (50, 200, 255), (bx_bar, ey + 1, ew, 2), border_radius=1)

        # Floating name tag above player tank
        if self.tank_type == "player" and self.name:
            label = FONT_SM.render(self.name, True, (255, 255, 255))
            tag_w = label.get_width() + 14
            tag_h = label.get_height() + 4
            tag_x = draw_x - tag_w // 2
            tag_y = draw_y - s_ts // 2 - int(20 * scale) - tag_h
            tag = pygame.Surface((tag_w, tag_h), pygame.SRCALPHA)
            pygame.draw.rect(tag, (40, 30, 70, 220), (0, 0, tag_w, tag_h),
                             border_radius=tag_h // 2)
            pygame.draw.rect(tag, (255, 200, 230, 255), (0, 0, tag_w, tag_h),
                             2, border_radius=tag_h // 2)
            surf.blit(tag, (tag_x, tag_y))
            surf.blit(label, (tag_x + 7, tag_y + 2))

# ═══════════════════════════════════════
#  ENEMY AI
# ═══════════════════════════════════════
class EnemyTank(Tank):
    def __init__(self, gx, gy, tank_type="enemy_a", difficulty=1.0):
        super().__init__(gx, gy, tank_type)
        self.difficulty = difficulty
        self.path = []
        self.path_update_timer = 0
        self.stuck_counter = 0
        self.last_pos = (self.x, self.y)

        if tank_type == "enemy_b":
            self.speed = 2.2 * difficulty
            self.hp = 2; self.max_hp = 2
            self.shoot_delay = max(5, int(25 / difficulty))
        elif tank_type == "elite":
            self.speed = 1.6 * difficulty
            self.hp = 5; self.max_hp = 5
            self.shoot_delay = max(5, int(15 / difficulty))
            self.bullet_power = 2
        elif tank_type == "boss":
            self.speed = 1.2 * difficulty
            self.hp = 15; self.max_hp = 15
            self.shoot_delay = max(3, int(10 / difficulty))
            self.bullet_power = 3
        else:
            base_speed = 1.2 if difficulty <= 0.7 else 1.5
            self.speed = base_speed * difficulty
            self.hp = 2; self.max_hp = 2
            self.shoot_delay = max(8, int(35 / difficulty))

    def get_tank_positions(self, all_tanks):
        positions = set()
        for t in all_tanks:
            if t != self and t.alive:
                positions.add(t.get_grid())
        return positions

    def update_ai(self, grid, player, all_tanks):
        if not self.alive or self.spawn_timer > 0: return None
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            return None
        my_pos = self.get_grid()
        player_pos = player.get_grid()
        base_pos = (COLS // 2, ROWS - 3)

        dist_to_p = abs(my_pos[0] - player_pos[0]) + abs(my_pos[1] - player_pos[1])
        target_pos = player_pos
        if dist_to_p > 15:
            target_pos = base_pos if random.random() < 0.2 else None
        else:
            if self.tank_type == "enemy_b" and random.random() < 0.3:
                target_pos = base_pos
            elif self.tank_type in ("elite", "boss"):
                dist_to_b = abs(my_pos[0] - base_pos[0]) + abs(my_pos[1] - base_pos[1])
                target_pos = player_pos if dist_to_p < dist_to_b else base_pos

        # Shoot when has line of sight
        if Pathfinder.can_shoot(grid, my_pos[0], my_pos[1], player_pos[0], player_pos[1]):
            if my_pos[0] == player_pos[0]:
                self.dir = 0 if player_pos[1] < my_pos[1] else 2
            else:
                self.dir = 1 if player_pos[0] > my_pos[0] else 3
            shoot_chance = 0.08 * (1.0 + self.difficulty)
            if self.tank_type == "boss": shoot_chance *= 2
            if random.random() < shoot_chance:
                self.muzzle_frame = 0
                return self.shoot()

        # Pathfinding
        self.path_update_timer += 1
        should_repath = self.path_update_timer >= 40 or not self.path or self.stuck_counter >= 10
        if not should_repath and self.path:
            last_goal = self.path[-1]
            if target_pos is not None:
                if abs(last_goal[0] - target_pos[0]) + abs(last_goal[1] - target_pos[1]) > 2:
                    should_repath = True

        if should_repath:
            self.path_update_timer = 0
            other_positions = self.get_tank_positions(all_tanks)
            if target_pos is None:
                cx, cy = my_pos
                rx = max(1, min(COLS - 2, cx + random.randint(-4, 4)))
                ry = max(1, min(ROWS - 2, cy + random.randint(-4, 4)))
                target_pos = (rx, ry) if grid[ry][rx] == EMPTY else my_pos
            self.path = Pathfinder.a_star_path(grid, my_pos, target_pos, other_positions)
            self.stuck_counter = 0

        if len(self.path) > 1:
            next_pos = self.path[1]
            tile_next = grid[next_pos[1]][next_pos[0]]
            if tile_next in (BRICK, CRATE):
                self.dir = Pathfinder.get_next_direction(my_pos, next_pos)
                if random.random() < 0.15:
                    return self.shoot()
            else:
                next_dir = Pathfinder.get_next_direction(my_pos, next_pos)
                if next_dir != -1:
                    ddx, ddy = DIRS[next_dir]
                    moved = self.move(ddx * self.speed, ddy * self.speed, grid, all_tanks)
                    if not moved or (abs(self.x - self.last_pos[0]) < 1 and abs(self.y - self.last_pos[1]) < 1):
                        self.stuck_counter += 1
                    else:
                        self.stuck_counter = 0
                    if moved and self.get_grid() == next_pos:
                        self.path.pop(0)
                    self.last_pos = (self.x, self.y)
        else:
            safe_dirs = Pathfinder.get_safe_directions(grid, self.x, self.y)
            if safe_dirs:
                if self.dir not in safe_dirs:
                    self.dir = random.choice(safe_dirs)
                ddx, ddy = DIRS[self.dir]
                self.move(ddx * self.speed, ddy * self.speed, grid, all_tanks)
        return None

# ═══════════════════════════════════════
#  PARTICLES
# ═══════════════════════════════════════
particles = []

class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'life', 'max_life', 'size']
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        a = random.uniform(0, 6.28)
        v = random.uniform(1, 5)
        self.vx, self.vy = math.cos(a) * v, math.sin(a) * v
        self.color = color
        self.life = random.randint(15, 40)
        self.max_life = self.life
        self.size = random.randint(2, 5)

def spawn_particles(x, y, color, n=10):
    for _ in range(n):
        particles.append(Particle(x, y, color))

def update_draw_particles(surf, offset=(0, 0), scale=1.0):
    for p in particles[:]:
        p.x += p.vx; p.y += p.vy
        p.vx *= 0.94; p.vy *= 0.94
        p.vy += 0.05
        p.life -= 1
        if p.life <= 0:
            particles.remove(p)
            continue
        draw_x = int((p.x - offset[0]) * scale)
        draw_y = int((p.y - offset[1]) * scale)
        a = p.life / p.max_life
        sz = max(1, int(p.size * a * scale))
        if sz > 1:
            gs = pygame.Surface((sz * 4, sz * 4), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*p.color, int(50 * a)), (sz * 2, sz * 2), sz * 2)
            surf.blit(gs, (draw_x - sz * 2, draw_y - sz * 2))
        pygame.draw.circle(surf, p.color, (draw_x, draw_y), sz)

# ═══════════════════════════════════════
#  FLOATING TEXT
# ═══════════════════════════════════════
floating_texts = []

class FloatingText:
    def __init__(self, x, y, text, color=(255, 220, 80), center_bounce=False, huge=False):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.center_bounce = center_bounce
        self.huge = huge
        self.life = 80 if (center_bounce or huge) else 50
        self.max_life = self.life

    def update(self):
        if not self.center_bounce:
            self.y -= 0.8
        self.life -= 1

    def draw(self, surf, offset=(0, 0), scale=1.0):
        a = self.life / self.max_life
        font = FONT_BIG if (self.center_bounce or self.huge) else FONT_SM
        t = font.render(self.text, True, self.color)

        if self.center_bounce or self.huge:
            progress = 1.0 - a
            if progress < 0.2: s = 0.5 + (progress / 0.2) * 1.5
            else: s = 1.5 - ((progress - 0.2) / 0.8) * 0.5
            if self.huge: s *= 1.2
            nw, nh = int(t.get_width() * s), int(t.get_height() * s)
            if nw > 0 and nh > 0:
                t = pygame.transform.scale(t, (nw, nh))
            if self.center_bounce:
                draw_x, draw_y = SW // 2, SH // 3
            else:
                draw_x = int((self.x - offset[0]) * scale)
                draw_y = int((self.y - offset[1]) * scale)
        else:
            if scale != 1.0:
                nw, nh = int(t.get_width() * scale), int(t.get_height() * scale)
                if nw > 0 and nh > 0:
                    t = pygame.transform.scale(t, (nw, nh))
            draw_x = int((self.x - offset[0]) * scale)
            draw_y = int((self.y - offset[1]) * scale)

        ts = pygame.Surface(t.get_size(), pygame.SRCALPHA)
        ts.blit(t, (0, 0))
        ts.set_alpha(int(255 * a))
        surf.blit(ts, (draw_x - t.get_width() // 2, draw_y - t.get_height() // 2))

# ═══════════════════════════════════════
#  GAME CLASS
# ═══════════════════════════════════════
class Game:
    def __init__(self):
        self.state = "title"
        try: pygame.mixer.music.play(-1)
        except Exception: pass
        self.level = 1
        self.score = 0
        self.lives = 3
        self.money = 0
        self.grid = None
        self.base_pos = None
        self.player = None
        self.enemies = []
        self.chickens = []
        self.dogs = []
        self.bullets = []
        self.explosions = []
        self.items = []
        self.enemies_to_spawn = 0
        self.spawn_timer = 0
        self.spawn_points = []
        self.tick = 0
        self.kills = 0
        self.total_enemies = 0
        self.water_frame = 0
        self.shake_amount = 0
        self.shake_x = 0
        self.shake_y = 0
        self.combo = 0
        self.combo_timer = 0
        self.auto_mode = False
        self.auto_path = []
        self.auto_path_update = 0
        self.max_alive = 1
        self.mission_text = ""
        self.mission_timer = 0
        self.won_level = False
        self.bought_skills = {}
        self.auto_algos = ["A*", "BFS", "DFS"]
        self.auto_algo_idx = 0
        self.auto_algo = "A*"
        self.map_theme = "default"
        self.backpack = []
        self.total_kills = 0
        self.total_money_earned = 0
        self.player_tier = 0  # persisted across levels
        self.gems = 10
        self.player_name = os.environ.get("TANK_PLAYER_NAME", "Thuanvuse")

        # Kawaii title menu
        self.menu_buttons = ["BATTLE", "GARAGE", "UPGRADE", "ACHIEVEMENTS"]
        self.menu_sel = 0

        # Garage / skin selection
        self.skin_idx = 0
        self.skin_names = [f"Tier {i + 1}" for i in range(5)]
        self.unlocked_skins = {0}

        # Achievements (id -> (label, unlocked))
        self.achievement_defs = [
            ("FIRST_BLOOD", "Diet ke dich dau tien"),
            ("LEVEL_5", "Hoan thanh level 5"),
            ("LEVEL_10", "Hoan thanh level 10"),
            ("BOSS_SLAYER", "Ha guc 1 Boss"),
            ("RICH", "Tich luy 5000 GP"),
            ("MAX_TIER", "Dat Tank tier 4 (MAX)"),
            ("FROZEN_HUNTER", "Dung FREEZE 3 lan"),
            ("GRENADIER", "Dung GRENADE 5 lan"),
        ]
        self.achievements_unlocked = set()
        self.freeze_uses = 0
        self.grenade_uses = 0

        # Pause
        self.pause_items = ["TIEP TUC", "CHOI LAI", "VAO SHOP", "CACH CHOI", "VE SANH", "THOAT GAME"]
        self.pause_sel = 0

        # Shop
        self.shop_page = 0
        self.shop_sel = 0

        # Camera
        self.cam_x = 0
        self.cam_y = 0
        self.cam_zoom = 1.0
        self.target_zoom = 1.0

        # Tutorial page
        self.tutorial_page = 0

        # Title animation
        self.title_tanks = []
        for i in range(6):
            self.title_tanks.append({
                'x': random.randint(0, SW),
                'y': random.randint(50, SH - 100),
                'dir': random.randint(0, 3),
                'type': random.choice(["player", "enemy_a", "enemy_b", "elite"]),
                'speed': random.uniform(0.3, 1.0),
            })

        # Stats
        self.stats = {
            "max_combo": 0,
            "total_kills": 0,
            "bosses_killed": 0,
            "levels_completed": 0,
            "money_spent": 0,
        }

    def get_theme_for_level(self, level):
        themes = ["default", "desert", "jungle", "snow", "city", "lava"]
        return themes[(level - 1) % len(themes)]

    def start_level(self, level):
        self.level = level
        new_cols, new_rows = 26, 20

        global COLS, ROWS
        COLS, ROWS = new_cols, new_rows

        self.grid, self.base_pos = generate_map(level, new_cols, new_rows)

        # Theme
        self.map_theme = self.get_theme_for_level(level)
        sprites.set_floor_theme(self.map_theme)
        weather.set_weather(self.map_theme)

        self.target_zoom = 1.0
        self.cam_zoom = 1.0

        # Player
        self.player = Tank(new_cols // 2 - 2, new_rows - 2, "player")
        self.player.tier = self.player_tier
        self.player.name = self.player_name

        if self.auto_mode:
            self.player.speed = 3.5
            self.player.shoot_delay = 5
            self.player.max_hp = 10
            self.player.hp = 10
            self.player.shield = 5
        else:
            self.player.hp = 3 + min(level // 3, 3)
            self.player.max_hp = self.player.hp

        # Apply bought skills
        if getattr(self, 'bought_skills', None):
            for skill, val in self.bought_skills.items():
                if hasattr(self.player, skill):
                    setattr(self.player, skill, val)
            self.bought_skills = {}

        self.enemies = []
        self.chickens = []
        self.dogs = []
        self.bullets = []
        self.explosions = []
        self.items = []
        particles.clear()
        floating_texts.clear()

        num_chickens = 0
        num_dogs = 0
        is_boss_level = (level % 5 == 0)

        if level == 1:
            self.total_enemies = 3
            self.max_alive = 1
            self.mission_text = "NHIEM VU: TIEU DIET 3 XE TANG DICH"
            self.mission_timer = 240
        elif level == 2:
            self.total_enemies = 4
            self.max_alive = 2
            num_chickens = 5
            self.mission_text = "NHIEM VU: GIET GA LAY TIEN DE MUA DO"
            self.mission_timer = 240
        elif level == 3:
            self.total_enemies = 8
            self.max_alive = 4
            num_chickens = 4
            num_dogs = 2
            self.mission_text = "CANH BAO: CO CHO DIEN XUAT HIEN!"
            self.mission_timer = 240
        elif is_boss_level:
            self.total_enemies = 3 + level
            self.max_alive = min(5 + level // 2, 12)
            num_chickens = 3
            num_dogs = 2
            self.mission_text = f"BOSS FIGHT! MAN {level} - BOSS XUAT HIEN!"
            self.mission_timer = 300
            snd_boss_alert.play()
        else:
            self.total_enemies = 3 + level
            self.max_alive = min(3 + level, 10)
            num_chickens = 3 + level
            num_dogs = 1 + level // 3
            self.mission_text = f"NHIEM VU: TIEU DIET {self.total_enemies} KE DICH"
            self.mission_timer = 180

        self.enemies_to_spawn = self.total_enemies
        self.kills = 0
        self.spawn_timer = 0
        self.spawn_points = [(2, 1), (new_cols // 2, 1), (new_cols - 3, 1)]
        self.combo = 0
        self.combo_timer = 0

        # Spawn NPCs
        for _ in range(num_chickens):
            rx, ry = random.randint(5, new_cols - 5), random.randint(5, new_rows - 5)
            if self.grid[ry][rx] == EMPTY: self.chickens.append(Chicken(rx, ry))
        for _ in range(num_dogs):
            rx, ry = random.randint(5, new_cols - 5), random.randint(5, new_rows - 5)
            if self.grid[ry][rx] == EMPTY: self.dogs.append(Dog(rx, ry))

        if getattr(self, 'bought_nuke', False):
            self.items.append(Item(new_cols // 2 - 2, new_rows - 3, "star"))
            self.bought_nuke = False

        self.state = "playing"

        for _ in range(min(3, self.enemies_to_spawn)):
            self.spawn_enemy()

    def spawn_enemy(self):
        if self.enemies_to_spawn <= 0: return
        available_spawns = []
        for sp in self.spawn_points:
            occupied = any(e.alive and e.get_grid() == sp for e in self.enemies)
            if not occupied: available_spawns.append(sp)
        if not available_spawns: return

        sp = random.choice(available_spawns)
        is_boss_level = (self.level % 5 == 0)

        types = ["enemy_a"] * 5 + ["enemy_b"] * 3
        if self.level >= 3:
            types += ["elite"] * (self.level - 1)
        if is_boss_level and self.enemies_to_spawn == 1:
            etype = "boss"
        else:
            etype = random.choice(types)

        difficulty = min(0.4 + self.level * 0.1, 2.5)
        enemy = EnemyTank(sp[0], sp[1], etype, difficulty)
        self.enemies.append(enemy)
        self.enemies_to_spawn -= 1
        spawn_particles(sp[0] * TS + TS // 2, sp[1] * TS + TS // 2, (255, 255, 200), 12)

    def register_kill(self, x, y, base_score):
        self.score += base_score
        self.combo += 1
        self.combo_timer = 180
        self.total_kills += 1
        self.stats["total_kills"] += 1
        if self.combo > self.stats["max_combo"]:
            self.stats["max_combo"] = self.combo

        pygame.time.delay(30)
        self.shake_amount = min(self.shake_amount + 5, 25)

        if self.combo == 2:
            floating_texts.append(FloatingText(x, y - 20, "DOUBLE KILL!", (255, 100, 255)))
            self.money += 20
        elif self.combo == 3:
            floating_texts.append(FloatingText(x, y - 20, "TRIPLE KILL!!", (255, 50, 50)))
            self.money += 50
            snd_combo.play()
        elif self.combo == 4:
            floating_texts.append(FloatingText(x, y - 20, "RAMPAGE!!!", (255, 0, 0)))
            self.money += 100
            snd_combo.play()
        elif self.combo >= 5:
            floating_texts.append(FloatingText(x, y - 20, "GODLIKE!!!!!", (255, 0, 255), huge=True))
            self.money += 200
            snd_combo.play()
            trigger_achievement("GODLIKE!", "5+ combo trong 1 chuoi!", (255, 0, 255))

        if random.random() < 0.2 + (self.combo * 0.05):
            self.items.append(Item(int(x // TS), int(y // TS), "money"))

    # ═══════════════════════════════════
    # AUTO MODE
    # ═══════════════════════════════════
    def auto_play(self):
        if not self.player.alive or self.player.spawn_timer > 0: return
        my_pos = self.player.get_grid()
        alive_enemies = [e for e in self.enemies if e.alive and e.spawn_timer <= 0]

        # Dodge system
        dodge_dir = -1
        danger_bullets = [b for b in self.bullets if b.owner != "player" and b.alive
                         and math.hypot(b.x - self.player.x, b.y - self.player.y) < TS * 3.5]

        if danger_bullets:
            safe = Pathfinder.get_safe_directions(self.grid, self.player.x, self.player.y)
            if safe:
                best_d = -1; max_safety = -1
                for d in safe:
                    ddx, ddy = DIRS[d]
                    nx = self.player.x + ddx * self.player.speed
                    ny = self.player.y + ddy * self.player.speed
                    current_safety = min((math.hypot(nx - b.x, ny - b.y) for b in danger_bullets), default=1000)
                    if current_safety > max_safety:
                        max_safety = current_safety; best_d = d
                if max_safety < TS * 1.5:
                    dodge_dir = best_d

        # Shoot visible enemies
        visible_enemies = []
        for enemy in alive_enemies:
            epos = enemy.get_grid()
            if Pathfinder.can_shoot(self.grid, my_pos[0], my_pos[1], epos[0], epos[1]):
                dist = abs(my_pos[0] - epos[0]) + abs(my_pos[1] - epos[1])
                visible_enemies.append((dist, enemy))

        if visible_enemies:
            visible_enemies.sort(key=lambda x: x[0])
            target = visible_enemies[0][1]
            epos = target.get_grid()
            if my_pos[0] == epos[0]:
                self.player.dir = 0 if epos[1] < my_pos[1] else 2
            else:
                self.player.dir = 1 if epos[0] > my_pos[0] else 3
            bullets = self.player.shoot()
            if bullets: self.bullets.extend(bullets)

        # Movement
        if dodge_dir != -1:
            ddx, ddy = DIRS[dodge_dir]
            self.player.move(ddx * self.player.speed, ddy * self.player.speed, self.grid, self.enemies)
        else:
            item_target = None
            for it in self.items:
                if it.alive and abs(my_pos[0] - it.gx) + abs(my_pos[1] - it.gy) < 5:
                    item_target = it; break

            nav_goal = None
            if item_target:
                nav_goal = (item_target.gx, item_target.gy)
            elif alive_enemies:
                nearest = min(alive_enemies, key=lambda e: abs(my_pos[0] - e.get_grid()[0]) + abs(my_pos[1] - e.get_grid()[1]))
                nav_goal = nearest.get_grid()

            if nav_goal:
                self.auto_path_update += 1
                if self.auto_path_update >= 20 or not self.auto_path or self.auto_path[-1] != nav_goal:
                    self.auto_path_update = 0
                    if self.auto_algo == "A*":
                        self.auto_path = Pathfinder.a_star_path(self.grid, my_pos, nav_goal)
                    elif self.auto_algo == "BFS":
                        self.auto_path = Pathfinder.bfs_path(self.grid, my_pos, nav_goal)
                    else:
                        self.auto_path = Pathfinder.dfs_path(self.grid, my_pos, nav_goal)

                if len(self.auto_path) > 1:
                    next_node = self.auto_path[1]
                    tile_type = self.grid[next_node[1]][next_node[0]]
                    if tile_type in (BRICK, CRATE):
                        self.player.dir = Pathfinder.get_next_direction(my_pos, next_node)
                        bullets = self.player.shoot()
                        if bullets: self.bullets.extend(bullets)
                    else:
                        ndir = Pathfinder.get_next_direction(my_pos, next_node)
                        if ndir != -1:
                            ddx, ddy = DIRS[ndir]
                            moved = self.player.move(ddx * self.player.speed, ddy * self.player.speed, self.grid, self.enemies)
                            if moved and self.player.get_grid() == next_node:
                                self.auto_path.pop(0)
                else:
                    self.auto_path = []

    def _activate_menu_selection(self):
        choice = self.menu_buttons[self.menu_sel]
        if choice == "BATTLE":
            def start():
                self.score = 0; self.lives = 3; self.money = 0
                self.total_kills = 0; self.total_money_earned = 0
                self.player_tier = self.skin_idx  # start at chosen skin tier
                self.start_level(1)
                self.state = "level_start"
                pygame.mixer.music.stop()
            transition.start(start)
        elif choice == "GARAGE":
            self.state = "garage"
        elif choice == "UPGRADE":
            self.state = "shop"
        elif choice == "ACHIEVEMENTS":
            self.state = "achievements"

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            # Global hotkeys (work in any state)
            if ev.key == pygame.K_F11:
                toggle_fullscreen()
                return
            if self.state == "title":
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.menu_sel = (self.menu_sel + 1) % len(self.menu_buttons)
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    self.menu_sel = (self.menu_sel - 1) % len(self.menu_buttons)
                elif ev.key == pygame.K_RETURN:
                    self._activate_menu_selection()
                elif ev.key == pygame.K_h:
                    self.state = "tutorial"
                    self.tutorial_page = 0
            elif self.state == "garage":
                if ev.key in (pygame.K_LEFT, pygame.K_a):
                    self.skin_idx = (self.skin_idx - 1) % len(self.skin_names)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    self.skin_idx = (self.skin_idx + 1) % len(self.skin_names)
                elif ev.key == pygame.K_RETURN:
                    if self.skin_idx not in self.unlocked_skins:
                        cost = (self.skin_idx + 1) * 200
                        if self.gems >= cost:
                            self.gems -= cost
                            self.unlocked_skins.add(self.skin_idx)
                elif ev.key == pygame.K_ESCAPE:
                    self.state = "title"
            elif self.state == "achievements":
                if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.state = "title"
            elif self.state == "tutorial":
                if ev.key == pygame.K_ESCAPE or ev.key == pygame.K_RETURN:
                    self.state = "title"
                elif ev.key == pygame.K_RIGHT:
                    self.tutorial_page = min(3, self.tutorial_page + 1)
                elif ev.key == pygame.K_LEFT:
                    self.tutorial_page = max(0, self.tutorial_page - 1)
            elif self.state == "level_start":
                if ev.key == pygame.K_SPACE:
                    self.state = "playing"
            elif self.state == "playing":
                if ev.key == pygame.K_f:
                    self.auto_mode = not self.auto_mode
                    self.auto_path = []
                    if self.auto_mode:
                        self.player.speed = 3.5
                        self.player.shoot_delay = 5
                        self.player.max_hp = 10
                        self.player.hp = 10
                        self.player.shield = 5
                        msg = "AUTO BUFF: ON"
                    else:
                        self.player.speed = 1.8
                        self.player.shoot_delay = 20
                        normal_max = 3 + min(self.level // 3, 3)
                        self.player.max_hp = normal_max
                        self.player.hp = min(self.player.hp, normal_max)
                        msg = "AUTO BUFF: OFF"
                    c = (80, 255, 130) if self.auto_mode else (255, 100, 80)
                    floating_texts.append(FloatingText(self.player.x, self.player.y - 40, msg, c))

                if ev.key == pygame.K_g:
                    self.auto_algo_idx = (self.auto_algo_idx + 1) % len(self.auto_algos)
                    self.auto_algo = self.auto_algos[self.auto_algo_idx]
                    self.auto_path = []
                    floating_texts.append(FloatingText(self.player.x, self.player.y - 80, f"ALGO: {self.auto_algo}", (255, 255, 0), huge=True))

                if ev.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    idx = ev.key - pygame.K_1
                    if idx < len(self.backpack):
                        item_kind = self.backpack.pop(idx)
                        self.apply_item_ultra(item_kind)
                        snd_pickup.play()

                if ev.key == pygame.K_ESCAPE:
                    self.state = "pause"
                    self.pause_sel = 0

            elif self.state == "pause":
                if ev.key == pygame.K_ESCAPE:
                    self.state = "playing"
                elif ev.key == pygame.K_UP:
                    self.pause_sel = (self.pause_sel - 1) % len(self.pause_items)
                elif ev.key == pygame.K_DOWN:
                    self.pause_sel = (self.pause_sel + 1) % len(self.pause_items)
                elif ev.key == pygame.K_RETURN:
                    sel = self.pause_items[self.pause_sel]
                    if sel == "TIEP TUC": self.state = "playing"
                    elif sel == "CHOI LAI":
                        self.start_level(self.level)
                        pygame.mixer.music.stop()
                    elif sel == "VAO SHOP":
                        self.state = "shop"
                        try: pygame.mixer.music.play(-1)
                        except Exception: pass
                    elif sel == "CACH CHOI":
                        self.state = "tutorial"
                        self.tutorial_page = 0
                    elif sel == "VE SANH":
                        self.state = "title"
                        try: pygame.mixer.music.play(-1)
                        except Exception: pass
                    elif sel == "THOAT GAME":
                        pygame.quit(); sys.exit()

            elif self.state in ("gameover", "level_clear"):
                if ev.key == pygame.K_RETURN:
                    def go_shop():
                        self.state = "shop"
                        try: pygame.mixer.music.play(-1)
                        except Exception: pass
                    transition.start(go_shop)

            elif self.state == "shop":
                self.handle_shop_events(ev)

    def update(self):
        self.tick += 1
        transition.update()
        weather.update()

        # Achievement animation
        for ach in achievement_queue[:]:
            ach.timer -= 1
            ach.y_offset = min(10, ach.y_offset + 4)
            if ach.timer <= 0:
                achievement_queue.remove(ach)

        if self.tick % 10 == 0:
            self.water_frame = (self.water_frame + 1) % len(sprites.water_frames)

        # Title tank animation
        if self.state == "title":
            for t in self.title_tanks:
                ddx, ddy = DIRS[t['dir']]
                t['x'] += ddx * t['speed']
                t['y'] += ddy * t['speed']
                if t['x'] < -40 or t['x'] > SW + 40 or t['y'] < -40 or t['y'] > SH + 40:
                    t['dir'] = random.randint(0, 3)
                    if t['dir'] == 0: t['y'] = SH + 30
                    elif t['dir'] == 1: t['x'] = -30
                    elif t['dir'] == 2: t['y'] = -30
                    elif t['dir'] == 3: t['x'] = SW + 30

        if self.state != "playing": return

        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0: self.combo = 0
        if self.mission_timer > 0: self.mission_timer -= 1

        # Camera
        self.cam_zoom += (self.target_zoom - self.cam_zoom) * 0.05
        target_cam_x = self.player.x - (SW / self.cam_zoom) / 2
        target_cam_y = self.player.y - (ROWS * TS / self.cam_zoom) / 2
        self.cam_x += (target_cam_x - self.cam_x) * 0.1
        self.cam_y += (target_cam_y - self.cam_y) * 0.1
        map_w, map_h = COLS * TS, ROWS * TS
        view_w = SW / self.cam_zoom
        view_h = (ROWS * TS) / self.cam_zoom
        self.cam_x = max(0, min(self.cam_x, map_w - view_w))
        self.cam_y = max(0, min(self.cam_y, map_h - view_h))

        # Player input
        keys = pygame.key.get_pressed()
        self.player.update()

        if self.player.alive and self.player.spawn_timer <= 0:
            if self.auto_mode:
                self.auto_play()
            else:
                mdx, mdy = 0, 0
                if keys[pygame.K_UP] or keys[pygame.K_w]: mdy -= 1
                if keys[pygame.K_DOWN] or keys[pygame.K_s]: mdy += 1
                if keys[pygame.K_LEFT] or keys[pygame.K_a]: mdx -= 1
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]: mdx += 1

                is_moving = mdx != 0 or mdy != 0
                if is_moving and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.player.energy > 0:
                    self.player.sprint_multiplier = 1.8
                    self.player.energy = max(0, self.player.energy - 0.5)
                else:
                    self.player.sprint_multiplier = 1.0
                    if self.player.energy < self.player.max_energy:
                        self.player.energy = min(self.player.max_energy, self.player.energy + 0.15)

                if is_moving:
                    mag = math.hypot(mdx, mdy)
                    spd = self.player.speed * self.player.sprint_multiplier
                    self.player.move(mdx / mag * spd, mdy / mag * spd, self.grid, self.enemies)

                if keys[pygame.K_SPACE]:
                    new_bullets = self.player.shoot()
                    if new_bullets: self.bullets.extend(new_bullets)

        # Enemy AI
        for enemy in self.enemies:
            enemy.update()
            new_bullets = enemy.update_ai(self.grid, self.player, self.enemies + [self.player])
            if new_bullets:
                if isinstance(new_bullets, list): self.bullets.extend(new_bullets)
                else: self.bullets.append(new_bullets)

        # Soft separation
        all_tanks = [self.player] + [e for e in self.enemies if e.alive]
        for i in range(len(all_tanks)):
            for j in range(i + 1, len(all_tanks)):
                t1, t2 = all_tanks[i], all_tanks[j]
                if t1.alive and t2.alive:
                    ddx = t1.x - t2.x; ddy = t1.y - t2.y
                    dist = math.hypot(ddx, ddy)
                    if 0 < dist < TS - 5:
                        push_force = (TS - 5 - dist) * 0.05
                        px, py = ddx / dist * push_force, ddy / dist * push_force
                        if t1.can_move_to(t1.x + px, t1.y + py, self.grid):
                            t1.x += px; t1.y += py
                        if t2.can_move_to(t2.x - px, t2.y - py, self.grid):
                            t2.x -= px; t2.y -= py

        # NPC updates
        for c in self.chickens: c.update(self.grid)
        for d in self.dogs:
            d.update(self.grid, (self.player.x, self.player.y))
            if d.alive and self.player.alive and d.bite_cooldown <= 0:
                if math.hypot(d.x - self.player.x, d.y - self.player.y) < 25:
                    killed = self.player.hit(1)
                    d.alive = False
                    spawn_particles(d.x, d.y, (150, 100, 50), 10)
                    self.shake_amount = 10
                    floating_texts.append(FloatingText(self.player.x, self.player.y, "CHO CAN!", (255, 50, 50)))
                    if killed:
                        self.explosions.append(Explosion(self.player.x, self.player.y, big=True))
                        snd_explode.play()
                        self.shake_amount = 15
                        self.lives -= 1
                        if self.lives <= 0:
                            self.state = "gameover"; self.won_level = False
                        else:
                            self._respawn_player()

        # Spawn timer
        self.spawn_timer += 1
        alive_count = sum(1 for e in self.enemies if e.alive and e.spawn_timer <= 0)
        if self.spawn_timer >= 70 and alive_count < self.max_alive and self.enemies_to_spawn > 0:
            self.spawn_enemy(); self.spawn_timer = 0

        # Bullets
        for bullet in self.bullets[:]:
            bullet.update()
            if not bullet.alive:
                self.bullets.remove(bullet); continue

            gx, gy = bullet.get_grid()
            if 0 <= gx < COLS and 0 <= gy < ROWS:
                tile = self.grid[gy][gx]
                if tile in (BRICK, STEEL, BASE, CRATE):
                    if tile in (BRICK, CRATE):
                        self.grid[gy][gx] = EMPTY
                        spawn_particles(gx * TS + TS // 2, gy * TS + TS // 2, (150, 100, 50), 8)
                        if tile == CRATE or random.random() < 0.1:
                            item_kinds = ["health", "shield", "speed", "star", "rapid", "multi",
                                          "pierce", "bomb", "freeze", "grenade", "max_power"]
                            self.items.append(Item(gx, gy, random.choice(item_kinds)))
                    if bullet.kind != "pierce":
                        bullet.alive = False
                        self.explosions.append(Explosion(int(bullet.x), int(bullet.y)))
                        if tile == STEEL: snd_steel.play()
                        if tile == BASE:
                            self.explosions.append(Explosion(gx * TS + TS // 2, gy * TS + TS // 2, big=True))
                            self.state = "gameover"; self.won_level = False
                        continue

            # Hit player
            if bullet.owner != "player" and self.player.alive:
                if abs(bullet.x - self.player.x) < 15 and abs(bullet.y - self.player.y) < 15:
                    killed = self.player.hit(bullet.power)
                    bullet.alive = False
                    self.explosions.append(Explosion(int(bullet.x), int(bullet.y)))
                    if killed:
                        self.explosions.append(Explosion(self.player.x, self.player.y, big=True))
                        snd_explode.play(); self.shake_amount = 12
                        self.lives -= 1
                        if self.lives <= 0:
                            self.state = "gameover"; self.won_level = False
                        else:
                            self._respawn_player()
                    continue

            if bullet.owner == "player":
                for c in self.chickens:
                    if c.alive and abs(bullet.x - c.x) < 15 and abs(bullet.y - c.y) < 15:
                        c.alive = False; bullet.alive = False
                        self.explosions.append(Explosion(c.x, c.y))
                        val = random.choice([50, 100, 200])
                        self.register_kill(c.x, c.y, val)
                        spawn_particles(c.x, c.y, (255, 255, 100), 12)
                        floating_texts.append(FloatingText(c.x, c.y, f"+{val}$", (255, 215, 0)))

                for d in self.dogs:
                    if d.alive and abs(bullet.x - d.x) < 18 and abs(bullet.y - d.y) < 18:
                        d.alive = False; bullet.alive = False
                        self.register_kill(d.x, d.y, 150)
                        self.explosions.append(Explosion(d.x, d.y))
                        spawn_particles(d.x, d.y, (150, 100, 50), 15)
                        floating_texts.append(FloatingText(d.x, d.y, "DOG KILLED!", (255, 150, 50)))

                for enemy in self.enemies:
                    if enemy.alive and abs(bullet.x - enemy.x) < 12 and abs(bullet.y - enemy.y) < 12:
                        killed = enemy.hit(bullet.power)
                        bullet.alive = False if bullet.kind != "pierce" else True
                        if killed:
                            self.kills += 1
                            base_score = 100
                            if enemy.tank_type == "elite": base_score = 300
                            elif enemy.tank_type == "boss":
                                base_score = 1000
                                self.stats["bosses_killed"] += 1
                                trigger_achievement("BOSS SLAYER!", f"Ha guc Boss man {self.level}!", (255, 100, 50))
                            self.register_kill(enemy.x, enemy.y, base_score)
                            self.explosions.append(Explosion(enemy.x, enemy.y, big=True))
                            spawn_particles(enemy.x, enemy.y, (255, 150, 50), 15)

        self.enemies = [e for e in self.enemies if e.alive or e.spawn_timer > 0]
        self.chickens = [c for c in self.chickens if c.alive]
        self.dogs = [d for d in self.dogs if d.alive]

        for exp in self.explosions[:]:
            exp.update()
            if exp.done: self.explosions.remove(exp)

        # Item pickup
        for item in self.items[:]:
            item.update()
            if not item.alive: self.items.remove(item); continue
            ix, iy = item.gx * TS + TS // 2, item.gy * TS + TS // 2
            if abs(self.player.x - ix) < 20 and abs(self.player.y - iy) < 20:
                snd_pickup.play()
                if item.kind == "money":
                    gain = random.randint(50, 150)
                    self.money += gain; self.total_money_earned += gain
                    floating_texts.append(FloatingText(self.player.x, self.player.y, f"+{gain}$", (255, 215, 0)))
                else:
                    self.apply_item_ultra(item.kind)
                self.items.remove(item)

        # Level clear
        if self.kills >= self.total_enemies and self.enemies_to_spawn <= 0:
            self.state = "level_clear"; self.won_level = True
            self.stats["levels_completed"] += 1
            snd_levelup.play()

        # Random items
        if self.tick % 480 == 0:
            for _ in range(10):
                rx, ry = random.randint(1, COLS - 2), random.randint(1, ROWS - 2)
                if self.grid[ry][rx] == EMPTY:
                    kind = random.choice(["health", "shield", "speed", "star", "life",
                                          "rapid", "multi", "pierce", "bomb",
                                          "freeze", "grenade", "max_power"])
                    self.items.append(Item(rx, ry, kind)); break

    def _respawn_player(self):
        ox, oy = self.player.x, self.player.y
        rx, ry = COLS // 2 - 2, ROWS - 2
        for _ in range(20):
            tx, ty = random.randint(1, COLS - 2), random.randint(1, ROWS - 2)
            if self.grid[ty][tx] == EMPTY: rx, ry = tx, ty; break
        self.player = Tank(rx, ry, "player")
        spawn_particles(ox, oy, (255, 50, 50), 20)
        floating_texts.append(FloatingText(ox, oy, "RESPAWNED!", (255, 255, 255)))

    def apply_item_ultra(self, kind):
        if kind == "health":
            self.player.hp = min(self.player.max_hp, self.player.hp + 1)
            floating_texts.append(FloatingText(self.player.x, self.player.y, "+1 HP", (80, 255, 80)))
        elif kind == "life":
            self.lives += 1
            floating_texts.append(FloatingText(self.player.x, self.player.y, "1UP! EXTRA LIFE", (255, 50, 150)))
        elif kind == "shield":
            self.player.shield += 3
            floating_texts.append(FloatingText(self.player.x, self.player.y, "SHIELD UP!", (80, 150, 255)))
        elif kind == "speed":
            self.player.energy = self.player.max_energy
            floating_texts.append(FloatingText(self.player.x, self.player.y, "ENERGY REFILL", (80, 255, 130)))
        elif kind == "rapid":
            self.player.skill = "rapid"; self.player.skill_ammo = 40
            floating_texts.append(FloatingText(self.player.x, self.player.y, "RAPID FIRE!", (255, 100, 50)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "multi":
            self.player.skill = "ammo"; self.player.skill_timer = 600
            floating_texts.append(FloatingText(self.player.x, self.player.y, "MULTI-SHOT!", (255, 200, 50)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "pierce":
            self.player.skill = "pierce"; self.player.skill_timer = 600
            floating_texts.append(FloatingText(self.player.x, self.player.y, "PIERCE BULLETS", (80, 200, 255)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "bomb":
            self.player.skill = "bomb"; self.player.skill_timer = 600
            floating_texts.append(FloatingText(self.player.x, self.player.y, "BOMB BULLETS", (255, 100, 50)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "laser":
            self.player.skill = "laser"; self.player.skill_timer = 600
            floating_texts.append(FloatingText(self.player.x, self.player.y, "LASER BEAM!", (0, 255, 180)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "plasma":
            self.player.skill = "plasma"; self.player.skill_timer = 600
            floating_texts.append(FloatingText(self.player.x, self.player.y, "PLASMA SHOTS!", (200, 50, 255)))
            self.player.tier = min(4, self.player.tier + 1)
        elif kind == "star":
            floating_texts.append(FloatingText(self.player.x, self.player.y, "BOMBA!!!", (255, 50, 50), huge=True))
            for e in self.enemies:
                if e.alive and e.spawn_timer <= 0:
                    killed = e.hit(10)
                    if killed:
                        self.kills += 1
                        self.register_kill(e.x, e.y, 100)
                        self.explosions.append(Explosion(e.x, e.y, big=True))
            self.shake_amount = 25
        elif kind == "freeze":
            # Freeze every alive enemy for ~5s (300 ticks at 60 FPS)
            self.freeze_uses += 1
            for e in self.enemies:
                if e.alive and e.spawn_timer <= 0:
                    e.frozen_timer = 300
            for d in self.dogs:
                if d.alive:
                    d.frozen_timer = 300
            floating_texts.append(FloatingText(self.player.x, self.player.y, "FREEZE!", (120, 220, 255), huge=True))
            self.shake_amount = 6
        elif kind == "max_power":
            # Instantly upgrade tank to max tier
            self.player.tier = 4
            self.player.max_hp = max(self.player.max_hp, 8)
            self.player.hp = self.player.max_hp
            self.player.shield += 3
            self.player.bullet_power = 3
            self.player.shoot_delay = 8
            self.player.skill = "pierce"
            self.player.skill_timer = 900
            floating_texts.append(FloatingText(self.player.x, self.player.y, "MAX POWER!", (255, 200, 60), huge=True))
            self.shake_amount = 10
        elif kind == "grenade":
            # AOE explosion centered on player; damages enemies within radius
            self.grenade_uses += 1
            radius = TS * 4
            for e in self.enemies:
                if e.alive and e.spawn_timer <= 0:
                    if math.hypot(e.x - self.player.x, e.y - self.player.y) <= radius:
                        killed = e.hit(4)
                        if killed:
                            self.kills += 1
                            self.register_kill(e.x, e.y, 100)
                            self.explosions.append(Explosion(e.x, e.y, big=True))
            for d in self.dogs:
                if d.alive and math.hypot(d.x - self.player.x, d.y - self.player.y) <= radius:
                    d.alive = False
                    self.register_kill(d.x, d.y, 150)
                    self.explosions.append(Explosion(d.x, d.y))
            for c in self.chickens:
                if c.alive and math.hypot(c.x - self.player.x, c.y - self.player.y) <= radius:
                    c.alive = False
                    self.register_kill(c.x, c.y, 50)
            # Burst of explosions for visual feedback
            for _ in range(6):
                ang = random.uniform(0, math.tau)
                rr = random.uniform(0, radius)
                ex = self.player.x + math.cos(ang) * rr
                ey = self.player.y + math.sin(ang) * rr
                self.explosions.append(Explosion(int(ex), int(ey), big=True))
            spawn_particles(self.player.x, self.player.y, (255, 180, 60), 30)
            floating_texts.append(FloatingText(self.player.x, self.player.y, "GRENADE!", (90, 220, 90), huge=True))
            self.shake_amount = 18
            snd_explode.play()

        # Persist tier across levels
        self.player_tier = self.player.tier
        self._check_achievements()

    # ═══════════════════════════════════
    # SHOP
    # ═══════════════════════════════════
    def draw_shop(self):
        s = self._surf
        # Gradient background
        for y in range(SH):
            t = y / SH
            c = (int(10 + 20 * t), int(15 + 25 * t), int(30 + 40 * t))
            pygame.draw.line(s, c, (0, y), (SW, y))

        # Header
        header_h = 80
        header_s = pygame.Surface((SW, header_h), pygame.SRCALPHA)
        pygame.draw.rect(header_s, (20, 30, 60, 220), (0, 0, SW, header_h))
        s.blit(header_s, (0, 0))

        title = FONT_TITLE.render("CUA HANG XE TANG", True, (255, 220, 50))
        shadow = FONT_TITLE.render("CUA HANG XE TANG", True, (100, 80, 0))
        s.blit(shadow, (SW // 2 - title.get_width() // 2 + 2, 12))
        s.blit(title, (SW // 2 - title.get_width() // 2, 10))

        # Decorative line
        pygame.draw.line(s, (255, 220, 50), (40, header_h - 5), (SW - 40, header_h - 5), 2)

        # Balance
        money_text = FONT_MED.render(f"TAI KHOAN: ${self.money}", True, (100, 255, 120))
        s.blit(money_text, (SW // 2 - money_text.get_width() // 2, header_h + 5))

        # Backpack status
        bp_text = FONT_SM.render(f"BALO: {len(self.backpack)}/3", True, (180, 180, 200))
        s.blit(bp_text, (SW - 100, header_h + 8))

        items = [
            ("1", "DAN DA HUONG", "Ban ra 3 tia cuc manh", 500, "multi"),
            ("2", "BAN SIEU TOC", "Dan toc do cao lien tuc", 800, "rapid"),
            ("3", "DAN XUYEN THAU", "Ban xuyen tuong & ke dich", 600, "pierce"),
            ("4", "GIAP THEP", "Tang 3 diem giap bao ve", 300, "shield"),
            ("5", "SUA CHUA XE", "Hoi day mau ngay lap tuc", 200, "health"),
            ("6", "THEM MANG", "Tang 1 mang du phong", 1000, "life"),
            ("7", "BOM NUKE", "Huy diet toan bo ke thu", 1000, "star"),
            ("8", "NANG LUONG", "Hoi day nang luong nitro", 150, "speed"),
            ("9", "TIA LASER", "Ban tia laser sieu manh", 900, "laser"),
            ("0", "DAN PLASMA", "Dan plasma huy diet", 750, "plasma"),
        ]

        start_y = header_h + 30
        for i, (key, name, desc, price, kind) in enumerate(items):
            col = i % 2
            row = i // 2
            bx = 30 + col * (SW // 2 - 10)
            by = start_y + row * 78
            w = SW // 2 - 50

            # Card background
            affordable = self.money >= price
            card_color = (40, 55, 85) if affordable else (30, 30, 40)
            border_color = (80, 130, 200) if affordable else (50, 50, 60)

            pygame.draw.rect(s, card_color, (bx, by, w, 68), border_radius=10)
            pygame.draw.rect(s, border_color, (bx, by, w, 68), 2, border_radius=10)

            # Gloss
            gloss = pygame.Surface((w - 4, 20), pygame.SRCALPHA)
            pygame.draw.rect(gloss, (255, 255, 255, 15), (0, 0, w - 4, 20), border_radius=8)
            s.blit(gloss, (bx + 2, by + 2))

            # Key
            key_c = (255, 215, 0) if affordable else (80, 80, 80)
            key_bg = pygame.Surface((28, 28), pygame.SRCALPHA)
            pygame.draw.rect(key_bg, (*key_c[:3], 40), (0, 0, 28, 28), border_radius=6)
            pygame.draw.rect(key_bg, key_c, (0, 0, 28, 28), 2, border_radius=6)
            s.blit(key_bg, (bx + 8, by + 8))
            kl = FONT_MED.render(key, True, key_c)
            s.blit(kl, (bx + 22 - kl.get_width() // 2, by + 12))

            # Icon
            if kind in sprites.items:
                s.blit(sprites.items[kind], (bx + 10, by + 38))

            # Name & Desc
            name_c = (255, 255, 255) if affordable else (120, 120, 120)
            name_t = FONT_MED.render(name, True, name_c)
            s.blit(name_t, (bx + 45, by + 10))
            desc_t = FONT_SM.render(desc, True, (150, 155, 170))
            s.blit(desc_t, (bx + 45, by + 32))

            # Price
            p_c = (80, 255, 120) if affordable else (255, 80, 80)
            p_t = FONT_MED.render(f"${price}", True, p_c)
            s.blit(p_t, (bx + 45, by + 48))

        # Continue
        pulse = abs(math.sin(self.tick * 0.08))
        msg = "[ ENTER ] MAN TIEP THEO" if self.won_level else "[ ENTER ] CHOI LAI"
        c_val = int(180 + pulse * 75)
        instr = FONT_MED.render(msg, True, (c_val, 255, c_val))
        s.blit(instr, (SW // 2 - instr.get_width() // 2, SH - 45))

    def handle_shop_events(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RETURN:
                def start_next():
                    target_lvl = self.level + 1 if self.won_level else self.level
                    self.start_level(target_lvl)
                    self.state = "level_start"
                    pygame.mixer.music.stop()
                transition.start(start_next)

            prices = {"1": 500, "2": 800, "3": 600, "4": 300, "5": 200,
                      "6": 1000, "7": 1000, "8": 150, "9": 900, "0": 750}
            kinds = {"1": "multi", "2": "rapid", "3": "pierce", "4": "shield", "5": "health",
                     "6": "life", "7": "star", "8": "speed", "9": "laser", "0": "plasma"}
            key_name = pygame.key.name(ev.key)
            if key_name in prices:
                cost = prices[key_name]
                if self.money >= cost:
                    if len(self.backpack) < 3:
                        self.money -= cost
                        self.stats["money_spent"] += cost
                        snd_buy.play()
                        self.backpack.append(kinds[key_name])
                        floating_texts.append(FloatingText(SW // 2, SH // 2, f"DA THEM {kinds[key_name].upper()}!", (100, 255, 100), center_bounce=True))
                    else:
                        snd_deny.play()
                        floating_texts.append(FloatingText(SW // 2, SH // 2, "BALO DAY!", (255, 80, 80), center_bounce=True))
                else:
                    snd_deny.play()
                    floating_texts.append(FloatingText(SW // 2, SH // 2, "KHONG DU TIEN!", (255, 80, 80), center_bounce=True))

    # ═══════════════════════════════════
    # DRAW
    # ═══════════════════════════════════
    def draw(self):
        if self.shake_amount > 0:
            self.shake_x = random.randint(-int(self.shake_amount), int(self.shake_amount))
            self.shake_y = random.randint(-int(self.shake_amount), int(self.shake_amount))
            self.shake_amount *= 0.85
            if self.shake_amount < 0.5:
                self.shake_amount = 0; self.shake_x = 0; self.shake_y = 0

        game_surf = pygame.Surface((SW, SH))
        game_surf.fill((10, 10, 15))
        self._surf = game_surf

        if self.state == "title": self.draw_title()
        elif self.state == "tutorial": self.draw_tutorial()
        elif self.state == "garage": self.draw_garage()
        elif self.state == "achievements": self.draw_achievements()
        elif self.state == "level_start": self.draw_level_start()
        elif self.state == "playing": self.draw_game()
        elif self.state == "shop": self.draw_shop()
        elif self.state == "gameover": self.draw_gameover()
        elif self.state == "level_clear": self.draw_level_clear()
        elif self.state == "pause": self.draw_pause()

        screen.fill((0, 0, 0))
        screen.blit(game_surf, (self.shake_x, self.shake_y))

        # Mission text overlay
        if self.state == "playing" and self.mission_timer > 0 and self.mission_text:
            if self.tick % 30 < 20:
                txt = FONT_MED.render(self.mission_text, True, (255, 230, 50))
                shadow = FONT_MED.render(self.mission_text, True, (50, 0, 0))
                screen.blit(shadow, (SW // 2 - txt.get_width() // 2 + 2, SH // 4 + 2))
                screen.blit(txt, (SW // 2 - txt.get_width() // 2, SH // 4))

        # Achievement popup
        for ach in achievement_queue:
            ach_y = int(ach.y_offset)
            a = min(255, ach.timer * 3)
            ach_s = pygame.Surface((300, 50), pygame.SRCALPHA)
            pygame.draw.rect(ach_s, (*ach.icon_color[:3], min(200, a)), (0, 0, 300, 50), border_radius=10)
            pygame.draw.rect(ach_s, (255, 255, 255, min(150, a)), (0, 0, 300, 50), 2, border_radius=10)
            nt = FONT_MED.render(ach.name, True, (255, 255, 255))
            dt = FONT_SM.render(ach.desc, True, (220, 220, 220))
            ach_s.blit(nt, (10, 5))
            ach_s.blit(dt, (10, 28))
            ach_s.set_alpha(a)
            screen.blit(ach_s, (SW // 2 - 150, ach_y))

        # Transition
        transition.draw(screen)

        # Floating texts (for shop/menus)
        if self.state in ("shop",):
            for ft in floating_texts[:]:
                ft.update()
                ft.draw(screen)
                if ft.life <= 0: floating_texts.remove(ft)

        pygame.display.flip()

    def draw_game(self):
        s = self._surf
        cam_off = (self.cam_x, self.cam_y)
        zoom = self.cam_zoom
        s_ts = int(TS * zoom)

        start_gx = max(0, int(self.cam_x // TS))
        end_gx = min(COLS, int((self.cam_x + SW / zoom) // TS) + 1)
        start_gy = max(0, int(self.cam_y // TS))
        end_gy = min(ROWS, int((self.cam_y + (ROWS * TS) / zoom) // TS) + 1)

        # Map tiles
        for y in range(start_gy, end_gy):
            for x in range(start_gx, end_gx):
                tile = self.grid[y][x]
                dx = int((x * TS - self.cam_x) * zoom)
                dy = int((y * TS - self.cam_y) * zoom)
                floor_img = sprites.floor
                if zoom != 1.0: floor_img = pygame.transform.scale(floor_img, (s_ts + 1, s_ts + 1))
                s.blit(floor_img, (dx, dy))
                if tile != EMPTY and tile != GRASS:
                    img = None
                    if tile == BRICK: img = sprites.brick
                    elif tile == STEEL: img = sprites.steel
                    elif tile == WATER: img = sprites.water_frames[self.water_frame]
                    elif tile == CRATE: img = sprites.crate
                    elif tile == BASE: img = sprites.base
                    if img:
                        if zoom != 1.0: img = pygame.transform.scale(img, (s_ts + 1, s_ts + 1))
                        s.blit(img, (dx, dy))

        # Entities
        for enemy in self.enemies: enemy.draw(s, self.tick, cam_off, zoom)
        for chick in self.chickens: chick.draw(s, self.tick, cam_off, zoom)
        for dog in self.dogs: dog.draw(s, self.tick, cam_off, zoom)
        for item in self.items: item.draw(s, self.tick, cam_off, zoom)
        if self.player: self.player.draw(s, self.tick, cam_off, zoom)

        # Backpack UI
        self.draw_backpack_ui(s)

        # Grass overlay
        for y in range(start_gy, end_gy):
            for x in range(start_gx, end_gx):
                if self.grid[y][x] == GRASS:
                    dx = int((x * TS - self.cam_x) * zoom)
                    dy = int((y * TS - self.cam_y) * zoom)
                    img = sprites.grass
                    if zoom != 1.0: img = pygame.transform.scale(img, (s_ts, s_ts))
                    s.blit(img, (dx, dy))

        # Effects
        for bullet in self.bullets: bullet.draw(s, cam_off, zoom)
        for exp in self.explosions: exp.draw(s, cam_off, zoom)
        update_draw_particles(s, cam_off, zoom)

        for ft in floating_texts[:]:
            ft.update()
            ft.draw(s, cam_off, zoom)
            if ft.life <= 0: floating_texts.remove(ft)

        # Weather
        weather.draw(s)

        # MINIMAP
        self.draw_minimap(s)

        # HUD
        self.draw_hud(s)

        # Auto path
        if self.auto_mode and self.auto_path:
            pts = [(px * TS + TS // 2, py * TS + TS // 2) for px, py in self.auto_path]
            if len(pts) > 1:
                pygame.draw.lines(s, (255, 100, 100, 150), False, pts, 2)

    def draw_minimap(self, surf):
        mm_scale = 3
        mm_w = COLS * mm_scale
        mm_h = ROWS * mm_scale
        mm_x = SW - mm_w - 8
        mm_y = 8

        mm = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        mm.fill((0, 0, 0, 150))

        for y in range(ROWS):
            for x in range(COLS):
                tile = self.grid[y][x]
                if tile == STEEL:
                    pygame.draw.rect(mm, (140, 145, 160), (x * mm_scale, y * mm_scale, mm_scale, mm_scale))
                elif tile == BRICK:
                    pygame.draw.rect(mm, (160, 80, 50), (x * mm_scale, y * mm_scale, mm_scale, mm_scale))
                elif tile == WATER:
                    pygame.draw.rect(mm, (40, 80, 180), (x * mm_scale, y * mm_scale, mm_scale, mm_scale))
                elif tile == BASE:
                    pygame.draw.rect(mm, (255, 220, 50), (x * mm_scale, y * mm_scale, mm_scale, mm_scale))
                elif tile == CRATE:
                    pygame.draw.rect(mm, (150, 110, 60), (x * mm_scale, y * mm_scale, mm_scale, mm_scale))

        # Player on minimap
        if self.player and self.player.alive:
            pgx, pgy = self.player.get_grid()
            pygame.draw.rect(mm, (80, 255, 120), (pgx * mm_scale - 1, pgy * mm_scale - 1, mm_scale + 2, mm_scale + 2))

        # Enemies
        for e in self.enemies:
            if e.alive:
                egx, egy = e.get_grid()
                ec = (255, 80, 80) if e.tank_type != "boss" else (255, 0, 255)
                pygame.draw.rect(mm, ec, (egx * mm_scale, egy * mm_scale, mm_scale, mm_scale))

        # Border
        pygame.draw.rect(mm, (80, 120, 180), (0, 0, mm_w, mm_h), 1)

        surf.blit(mm, (mm_x, mm_y))

    def draw_hud(self, surf):
        hud_h = 60
        hud_y = SH - hud_h

        # Kawaii HUD background — pastel gradient bar with rounded top
        hud_bg = pygame.Surface((SW, hud_h), pygame.SRCALPHA)
        for i in range(hud_h):
            t = i / hud_h
            r = int(45 + 25 * t)
            g = int(30 + 20 * t)
            b = int(75 + 30 * t)
            pygame.draw.line(hud_bg, (r, g, b, 235), (0, i), (SW, i))
        surf.blit(hud_bg, (0, hud_y))
        # Rainbow ribbon along the top edge
        for x in range(SW):
            seg = (x // 80) % len(KAWAII_RAINBOW)
            col = KAWAII_RAINBOW[seg]
            for dy in range(2):
                surf.set_at((x, hud_y + dy), col)

        # ── LIVES with heart icons ──
        lives_lbl = FONT_SM.render("LIVES", True, (255, 220, 240))
        surf.blit(lives_lbl, (12, hud_y + 6))
        for i in range(max(0, self.lives)):
            draw_heart_icon(surf, 12 + i * 26, hud_y + 24, 22, filled=True)

        # ── SCORE ── (under lives)
        score_t = FONT_MED.render(f"{self.score:,}", True, (255, 240, 180))
        surf.blit(score_t, (140, hud_y + 28))
        sc_lbl = FONT_SM.render("SCORE", True, (200, 200, 240))
        surf.blit(sc_lbl, (140, hud_y + 12))

        # Level badge
        badge_x = SW // 2 - 50
        theme_colors = {
            "default": (50, 100, 150), "desert": (180, 140, 60), "snow": (100, 150, 200),
            "city": (80, 80, 100), "jungle": (40, 120, 60), "lava": (150, 50, 30)
        }
        bc = theme_colors.get(self.map_theme, (50, 100, 150))
        pygame.draw.rect(surf, bc, (badge_x, hud_y + 6, 100, 22), border_radius=11)
        pygame.draw.rect(surf, (200, 220, 255), (badge_x, hud_y + 6, 100, 22), 1, border_radius=11)
        lvl_t = FONT_SM.render(f"LEVEL {self.level} - {self.map_theme.upper()}", True, (255, 255, 255))
        surf.blit(lvl_t, (badge_x + 50 - lvl_t.get_width() // 2, hud_y + 10))

        # Enemies left
        left = max(0, self.total_enemies - self.kills)
        e_t = FONT_SM.render(f"ENEMIES: {left}", True, (255, 100, 100))
        surf.blit(e_t, (SW - 150, hud_y + 8))
        for i in range(min(left, 8)):
            mini = pygame.transform.scale(sprites.tanks["enemy_a"][2], (12, 12))
            surf.blit(mini, (SW - 150 + i * 14, hud_y + 28))

        # Auto mode
        if self.auto_mode:
            pulse = abs(math.sin(self.tick * 0.2))
            c = (int(50 + 200 * pulse), 255, int(100 + 150 * pulse))
            surf.blit(FONT_SM.render(f"AUTO: {self.auto_algo}", True, c), (badge_x + 110, hud_y + 10))
            surf.blit(FONT_SM.render("[F]OFF [G]ALGO", True, (120, 140, 120)), (badge_x + 110, hud_y + 26))
        else:
            surf.blit(FONT_SM.render("[F]AUTO", True, (80, 100, 80)), (badge_x + 110, hud_y + 15))

        # Skill indicator
        if self.player and self.player.skill:
            skill_colors = {"rapid": (255, 150, 40), "ammo": (255, 200, 50), "pierce": (80, 200, 255),
                           "bomb": (255, 100, 50), "laser": (0, 255, 180), "plasma": (200, 50, 255)}
            sc = skill_colors.get(self.player.skill, (200, 200, 200))
            skill_name = self.player.skill.upper()
            if self.player.skill == "ammo": skill_name = "MULTI"
            st = FONT_SM.render(f"SKILL: {skill_name}", True, sc)
            surf.blit(st, (badge_x - 100, hud_y + 35))
            if self.player.skill_timer > 0:
                bar_w = 60
                bar_fill = int(bar_w * self.player.skill_timer / 600)
                pygame.draw.rect(surf, (40, 40, 40), (badge_x - 100, hud_y + 50, bar_w, 4))
                pygame.draw.rect(surf, sc, (badge_x - 100, hud_y + 50, bar_fill, 4))

        # Combo
        if self.combo > 1:
            pulse = abs(math.sin(self.tick * 0.3))
            c = (255, int(150 + pulse * 100), 50)
            combo_t = FONT_MED.render(f"x{self.combo} COMBO", True, c)
            surf.blit(combo_t, (badge_x - 90, hud_y + 8))
            cw = 60
            cx = badge_x - 90
            cy = hud_y + 28
            pygame.draw.rect(surf, (40, 40, 40), (cx, cy, cw, 4), border_radius=2)
            fw = int((self.combo_timer / 180) * cw)
            pygame.draw.rect(surf, (255, 100, 50), (cx, cy, fw, 4), border_radius=2)

    def draw_level_start(self):
        self.draw_game()
        s = pygame.Surface((SW, SH), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))

        # Theme name
        theme_names = {"default": "CHIEN TRUONG", "desert": "SA MAC", "snow": "BANG GIA",
                      "city": "THANH PHO", "jungle": "RUNG RAM", "lava": "NUI LUA"}
        theme_name = theme_names.get(self.map_theme, "CHIEN TRUONG")

        # Level number
        lvl_t = FONT_HUGE.render(f"MAN {self.level}", True, (255, 220, 50))
        shadow = FONT_HUGE.render(f"MAN {self.level}", True, (100, 80, 0))
        s.blit(shadow, (SW // 2 - lvl_t.get_width() // 2 + 3, SH // 2 - 100 + 3))
        s.blit(lvl_t, (SW // 2 - lvl_t.get_width() // 2, SH // 2 - 100))

        # Theme
        theme_t = FONT_MED.render(f"DIA HINH: {theme_name}", True, (180, 200, 255))
        s.blit(theme_t, (SW // 2 - theme_t.get_width() // 2, SH // 2 - 40))

        # Mission
        if self.mission_text:
            bg_rect = pygame.Rect(20, SH // 2, SW - 40, 45)
            pygame.draw.rect(s, (150, 30, 30, 200), bg_rect, border_radius=8)
            txt = FONT_MED.render(self.mission_text, True, (255, 255, 150))
            s.blit(txt, (SW // 2 - txt.get_width() // 2, SH // 2 + 10))

        # Boss warning
        if self.level % 5 == 0:
            pulse = abs(math.sin(self.tick * 0.15))
            warn_c = (255, int(50 + 200 * pulse), int(50 * pulse))
            warn_t = FONT_BIG.render("!! BOSS XUAT HIEN !!", True, warn_c)
            s.blit(warn_t, (SW // 2 - warn_t.get_width() // 2, SH // 2 + 55))

        pulse = abs(math.sin(self.tick * 0.1))
        instr = FONT_MED.render("NHAN [ SPACE ] DE BAT DAU", True, (int(150 + pulse * 105), int(180 + pulse * 75), 255))
        s.blit(instr, (SW // 2 - instr.get_width() // 2, SH // 2 + 100))

        self._surf.blit(s, (0, 0))

    def draw_title(self):
        s = self._surf
        # Pastel night-sky gradient background
        for y in range(SH):
            t = y / SH
            r = int(28 + 30 * t + 10 * math.sin(self.tick * 0.01 + t * 3))
            g = int(20 + 25 * t)
            b = int(60 + 45 * t)
            pygame.draw.line(s, (min(255, r), min(255, g), min(255, b)),
                             (0, y), (SW, y))

        # Sparkly starfield
        draw_pastel_starfield(s, self.tick, density=80)

        # Subtle background tanks (kawaii style — small + transparent)
        for tank in self.title_tanks:
            tk = tank['type']
            d = tank['dir']
            if tk in sprites.tanks:
                img = sprites.tanks[tk][d]
                img = pygame.transform.scale(img, (36, 36))
                alpha_s = pygame.Surface((36, 36), pygame.SRCALPHA)
                alpha_s.blit(img, (0, 0))
                alpha_s.set_alpha(35)
                s.blit(alpha_s, (int(tank['x']) - 18, int(tank['y']) - 18))

        # Currency panel (top-right) — drawn first so title centers cleanly
        self._draw_currency_panel(s, SW - 270, 12)
        # Player profile panel (top-left)
        self._draw_profile_panel(s, 12, 12)

        # Title with kawaii rainbow gradient (below the side panels)
        draw_rainbow_text(s, "KAWAII TANK KINGDOM", (SW // 2, 100),
                          FONT_TITLE, tick=self.tick)
        sub = FONT_SM.render(":  TANK DAI CHIEN  :", True, (255, 220, 240))
        s.blit(sub, (SW // 2 - sub.get_width() // 2, 158))

        # 5-tank preview row
        tank_types = ["player", "enemy_a", "enemy_b", "elite", "boss"]
        labels = ["NEKO", "DICH", "FAST", "ELITE", "BOSS"]
        preview_y = 188
        for i, (tk, label) in enumerate(zip(tank_types, labels)):
            bx = SW // 2 - 235 + i * 95
            by = preview_y
            draw_kawaii_panel(s, (bx, by, 80, 90), fill=(70, 50, 100),
                              border=KAWAII_RAINBOW[i % len(KAWAII_RAINBOW)],
                              radius=14, shadow_offset=3, glow=False)
            d = (self.tick // 30 + i) % 4
            if tk == "player":
                tier = min(len(sprites.player_tiers) - 1, self.skin_idx)
                tank_img = sprites.player_tiers[tier][d]
            elif tk in sprites.tanks:
                tank_img = sprites.tanks[tk][d]
            else:
                tank_img = None
            if tank_img is not None:
                big = pygame.transform.scale(tank_img, (52, 52))
                s.blit(big, (bx + 14, by + 8))
            lbl = FONT_SM.render(label, True, (255, 240, 200))
            s.blit(lbl, (bx + 40 - lbl.get_width() // 2, by + 65))

        # Big menu buttons
        btn_w, btn_h = 260, 52
        gap = 14
        total_h = len(self.menu_buttons) * (btn_h + gap) - gap
        start_y = SH - total_h - 60
        icons = [
            lambda surf, x, y, sz: surf.blit(
                pygame.transform.scale(sprites.player_tiers[
                    min(len(sprites.player_tiers) - 1, self.skin_idx)][1],
                    (sz, sz)), (x, y)),
            lambda surf, x, y, sz: surf.blit(
                pygame.transform.scale(sprites.tanks["player"][2], (sz, sz)),
                (x, y)),
            draw_coin_icon,
            lambda surf, x, y, sz: draw_heart_icon(surf, x, y, sz, filled=True),
        ]
        for i, label in enumerate(self.menu_buttons):
            bx = SW // 2 - btn_w // 2
            by = start_y + i * (btn_h + gap)
            draw_kawaii_button(s, (bx, by, btn_w, btn_h), label, FONT_MED,
                               selected=(i == self.menu_sel), color_idx=i,
                               tick=self.tick, icon_fn=icons[i])

        # Help footer
        hint = "  ↑/↓  chon  •  ENTER  vao  •  H  huong dan  •  F11  toggle fullscreen"
        ht = FONT_SM.render(hint, True, (255, 220, 240))
        s.blit(ht, (SW // 2 - ht.get_width() // 2, SH - 28))

    def _draw_currency_panel(self, surf, x, y):
        """Top-right currency display: gold + gems."""
        w, h = 250, 70
        draw_kawaii_panel(surf, (x, y, w, h), fill=(50, 35, 80),
                          border=(255, 200, 230), radius=14,
                          shadow_offset=3, glow=False)
        # Gold row
        draw_coin_icon(surf, x + 12, y + 8, 22)
        gt = FONT_MED.render(f"{self.money:,}", True, (255, 240, 180))
        surf.blit(gt, (x + 42, y + 9))
        plus_g = FONT_SM.render("+", True, (255, 255, 200))
        pygame.draw.circle(surf, (90, 200, 110), (x + w - 22, y + 19), 11)
        surf.blit(plus_g, (x + w - 25, y + 12))
        # Gem row
        draw_gem_icon(surf, x + 12, y + 38, 22)
        gemt = FONT_MED.render(f"{self.gems:,}", True, (200, 240, 255))
        surf.blit(gemt, (x + 42, y + 39))
        pygame.draw.circle(surf, (90, 200, 110), (x + w - 22, y + 49), 11)
        surf.blit(plus_g, (x + w - 25, y + 42))

    def draw_garage(self):
        s = self._surf
        for y in range(SH):
            t = y / SH
            pygame.draw.line(s, (int(35 + 20 * t), int(25 + 15 * t),
                                 int(70 + 40 * t)), (0, y), (SW, y))
        draw_pastel_starfield(s, self.tick, density=60)
        # Title
        draw_rainbow_text(s, "GARAGE", (SW // 2, 30), FONT_TITLE, tick=self.tick)
        sub = FONT_SM.render("Chon mau tank cua ban", True, (255, 220, 240))
        s.blit(sub, (SW // 2 - sub.get_width() // 2, 90))

        # Currency panel
        self._draw_currency_panel(s, SW - 270, 12)

        # Big tank preview at center
        center_x, center_y = SW // 2, 290
        panel_w, panel_h = 360, 280
        draw_kawaii_panel(s, (center_x - panel_w // 2, center_y - panel_h // 2,
                              panel_w, panel_h),
                          fill=(60, 45, 95),
                          border=KAWAII_RAINBOW[self.skin_idx % 6],
                          radius=18, shadow_offset=4, glow=True)
        tier = min(len(sprites.player_tiers) - 1, self.skin_idx)
        d = (self.tick // 30) % 4
        big = pygame.transform.scale(sprites.player_tiers[tier][d], (180, 180))
        s.blit(big, (center_x - 90, center_y - 110))
        # Stats per tier
        stats_list = [
            ("HP", 4 + self.skin_idx),
            ("FIRE RATE", 5 + self.skin_idx),
            ("BULLET PWR", 1 + self.skin_idx // 2),
            ("ARMOR", self.skin_idx),
        ]
        for i, (lbl, val) in enumerate(stats_list):
            yy = center_y + 60 + i * 18
            lt = FONT_SM.render(lbl, True, (200, 220, 255))
            s.blit(lt, (center_x - 130, yy))
            for j in range(5):
                col = (255, 220, 80) if j < val else (90, 60, 100)
                pygame.draw.rect(s, col,
                                 (center_x + 10 + j * 20, yy + 2, 16, 10),
                                 border_radius=3)

        # Skin name + status
        name = self.skin_names[self.skin_idx]
        nt = FONT_BIG.render(name, True, (255, 240, 200))
        s.blit(nt, (center_x - nt.get_width() // 2, center_y + 130))
        if self.skin_idx in self.unlocked_skins:
            stat = FONT_MED.render("UNLOCKED", True, (130, 240, 160))
            s.blit(stat, (center_x - stat.get_width() // 2, center_y + 165))
        else:
            cost = (self.skin_idx + 1) * 200
            stat = FONT_MED.render(f"COST: {cost} GEMS", True, (200, 220, 255))
            s.blit(stat, (center_x - stat.get_width() // 2, center_y + 165))

        # Left/right arrows
        for dx, key, sym in [(-1, "<", "<"), (+1, ">", ">")]:
            ax = center_x + dx * (panel_w // 2 + 50)
            ay = center_y - 20
            pulse = abs(math.sin(self.tick * 0.1 + dx))
            r = int(30 + pulse * 6)
            pygame.draw.circle(s, (80, 60, 120), (ax, ay), r)
            pygame.draw.circle(s, (255, 200, 230), (ax, ay), r, 3)
            ar = FONT_BIG.render(sym, True, (255, 255, 255))
            s.blit(ar, (ax - ar.get_width() // 2, ay - ar.get_height() // 2))

        # Bottom hint bar
        hint = "←/→ doi tank   ENTER mua bang gem   ESC quay lai"
        ht = FONT_SM.render(hint, True, (255, 230, 240))
        s.blit(ht, (SW // 2 - ht.get_width() // 2, SH - 28))

    def draw_achievements(self):
        s = self._surf
        for y in range(SH):
            t = y / SH
            pygame.draw.line(s, (int(40 + 20 * t), int(30 + 15 * t),
                                 int(70 + 35 * t)), (0, y), (SW, y))
        draw_pastel_starfield(s, self.tick, density=50)

        draw_rainbow_text(s, "ACHIEVEMENTS", (SW // 2, 30), FONT_TITLE,
                          tick=self.tick)
        unlocked_count = len(self.achievements_unlocked)
        total = len(self.achievement_defs)
        sub = FONT_MED.render(f"{unlocked_count}/{total} dat duoc",
                              True, (255, 240, 200))
        s.blit(sub, (SW // 2 - sub.get_width() // 2, 95))

        # Grid of achievement cards
        cols = 2
        card_w, card_h = 360, 70
        gap_x, gap_y = 30, 16
        total_w = cols * card_w + (cols - 1) * gap_x
        start_x = SW // 2 - total_w // 2
        start_y = 140
        for i, (key, label) in enumerate(self.achievement_defs):
            row = i // cols
            col = i % cols
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)
            unlocked = key in self.achievements_unlocked
            border = (255, 220, 100) if unlocked else (110, 90, 130)
            fill = (75, 55, 110) if unlocked else (45, 35, 70)
            draw_kawaii_panel(s, (x, y, card_w, card_h), fill=fill,
                              border=border, radius=14, shadow_offset=3,
                              glow=unlocked)
            # Trophy / lock icon
            ic_x, ic_y = x + 18, y + card_h // 2
            if unlocked:
                # Star/trophy
                pygame.draw.circle(s, (255, 220, 80), (ic_x + 14, ic_y), 18)
                pygame.draw.circle(s, (200, 130, 30), (ic_x + 14, ic_y), 18, 3)
                star = FONT_MED.render("*", True, (255, 100, 30))
                s.blit(star, (ic_x + 14 - star.get_width() // 2,
                              ic_y - star.get_height() // 2))
            else:
                pygame.draw.rect(s, (90, 80, 110),
                                 (ic_x, ic_y - 12, 28, 24), border_radius=4)
                pygame.draw.rect(s, (200, 200, 220),
                                 (ic_x + 4, ic_y - 18, 20, 16), 2,
                                 border_radius=8)
            # Text
            nt = FONT_MED.render(key.replace("_", " ").title(), True,
                                 (255, 240, 220) if unlocked else (170, 160, 190))
            s.blit(nt, (x + 60, y + 14))
            dt = FONT_SM.render(label, True,
                                (220, 220, 250) if unlocked else (140, 130, 160))
            s.blit(dt, (x + 60, y + 40))

        # Hint
        hint = "ENTER hoac ESC quay lai"
        ht = FONT_SM.render(hint, True, (255, 230, 240))
        s.blit(ht, (SW // 2 - ht.get_width() // 2, SH - 28))

    def _check_achievements(self):
        u = self.achievements_unlocked
        if self.total_kills >= 1: u.add("FIRST_BLOOD")
        if self.level >= 5 and self.stats.get("levels_completed", 0) >= 5:
            u.add("LEVEL_5")
        if self.level >= 10 and self.stats.get("levels_completed", 0) >= 10:
            u.add("LEVEL_10")
        if self.stats.get("bosses_killed", 0) >= 1: u.add("BOSS_SLAYER")
        if self.total_money_earned >= 5000: u.add("RICH")
        if self.player_tier >= 4: u.add("MAX_TIER")
        if self.freeze_uses >= 3: u.add("FROZEN_HUNTER")
        if self.grenade_uses >= 5: u.add("GRENADIER")

    def _draw_profile_panel(self, surf, x, y):
        """Player profile (top-left): tank avatar + name."""
        w, h = 230, 70
        draw_kawaii_panel(surf, (x, y, w, h), fill=(50, 35, 80),
                          border=(180, 220, 255), radius=14,
                          shadow_offset=3, glow=False)
        # Avatar
        tier = min(len(sprites.player_tiers) - 1, self.skin_idx)
        avatar = pygame.transform.scale(sprites.player_tiers[tier][0], (50, 50))
        surf.blit(avatar, (x + 8, y + 10))
        # Name
        nm = FONT_MED.render("PLAYER", True, (255, 240, 220))
        surf.blit(nm, (x + 70, y + 8))
        nick = FONT_SM.render(self.player_name, True, (180, 220, 255))
        surf.blit(nick, (x + 70, y + 35))

    def draw_tutorial(self):
        s = self._surf
        for y in range(SH):
            t = y / SH
            pygame.draw.line(s, (int(10 + 15 * t), int(12 + 18 * t), int(25 + 35 * t)), (0, y), (SW, y))

        # Header
        title = FONT_TITLE.render("HUONG DAN CHOI", True, (255, 220, 50))
        s.blit(title, (SW // 2 - title.get_width() // 2, 15))
        pygame.draw.line(s, (255, 220, 50), (50, 65), (SW - 50, 65), 2)

        pages = [
            {
                "title": "DIEU KHIEN CO BAN",
                "items": [
                    ("W A S D / Phim Mui Ten", "Di chuyen xe tang 4 huong"),
                    ("SPACE", "Ban dan - giu de ban lien tuc"),
                    ("SHIFT + Di chuyen", "Chay nhanh (ton nang luong)"),
                    ("ESC", "Tam dung / Menu"),
                    ("Phim 1, 2, 3", "Su dung vat pham trong balo"),
                ]
            },
            {
                "title": "CHE DO TU DONG (AUTO)",
                "items": [
                    ("Phim F", "Bat/Tat che do tu dong (co buff)"),
                    ("Phim G", "Doi thuat toan: A*, BFS, DFS"),
                    ("A* (Mac dinh)", "Tim duong ngan nhat, co pha tuong"),
                    ("BFS", "Tim duong rong, chi di duong trong"),
                    ("DFS", "Tim duong sau, ngau nhien hon"),
                ]
            },
            {
                "title": "VAT PHAM & CUA HANG",
                "items": [
                    ("Mau (Health)", "Hoi 1 diem mau"),
                    ("Giap (Shield)", "Chan 3 phat dan"),
                    ("Nang luong", "Hoi day thanh chay nhanh"),
                    ("Nuke (Star)", "Tieu diet toan bo ke dich"),
                    ("Balo chua toi da 3 vat pham", "Mua trong shop, dung bang phim 1-3"),
                ]
            },
            {
                "title": "MAP & BOSS",
                "items": [
                    ("6 dia hinh", "Chien truong, Sa mac, Bang gia, Thanh pho, Rung, Nui lua"),
                    ("Moi 5 man", "Boss xuat hien - rat manh!"),
                    ("Ga", "Ban de lay tien"),
                    ("Cho", "Duoi can nguoi choi - nguy hiem!"),
                    ("Can cu", "Bao ve can cu o phia duoi ban do"),
                ]
            }
        ]

        page = pages[self.tutorial_page]

        # Page title
        pt = FONT_BIG.render(page["title"], True, (100, 220, 255))
        s.blit(pt, (SW // 2 - pt.get_width() // 2, 85))

        # Items
        for i, (key, desc) in enumerate(page["items"]):
            y_pos = 140 + i * 70

            # Key box
            key_bg = pygame.Surface((SW - 80, 55), pygame.SRCALPHA)
            pygame.draw.rect(key_bg, (30, 40, 60, 200), (0, 0, SW - 80, 55), border_radius=8)
            pygame.draw.rect(key_bg, (60, 90, 140), (0, 0, SW - 80, 55), 1, border_radius=8)
            s.blit(key_bg, (40, y_pos))

            # Key label
            key_t = FONT_MED.render(key, True, (255, 220, 80))
            s.blit(key_t, (60, y_pos + 8))

            # Description
            desc_t = FONT_SM.render(desc, True, (180, 185, 200))
            s.blit(desc_t, (60, y_pos + 32))

        # Page indicator
        page_t = FONT_SM.render(f"Trang {self.tutorial_page + 1}/{len(pages)}", True, (150, 150, 170))
        s.blit(page_t, (SW // 2 - page_t.get_width() // 2, SH - 70))

        # Navigation
        nav_t = FONT_SM.render("[ <- ] Truoc    [ -> ] Tiep    [ ESC/ENTER ] Quay lai", True, (120, 140, 180))
        s.blit(nav_t, (SW // 2 - nav_t.get_width() // 2, SH - 40))

        # Page dots
        for i in range(len(pages)):
            cx = SW // 2 - (len(pages) * 12) // 2 + i * 12 + 6
            c = (255, 220, 50) if i == self.tutorial_page else (60, 70, 90)
            pygame.draw.circle(s, c, (cx, SH - 85), 4)

    def draw_gameover(self):
        self.draw_game()
        s = self._surf
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        s.blit(overlay, (0, 0))

        # Vignette effect
        for i in range(3):
            vig = pygame.Surface((SW, SH), pygame.SRCALPHA)
            pygame.draw.rect(vig, (80, 0, 0, 20 - i * 5), (i * 10, i * 10, SW - i * 20, SH - i * 20), i * 5 + 5)
            s.blit(vig, (0, 0))

        text = FONT_HUGE.render("GAME OVER", True, (255, 50, 50))
        shadow = FONT_HUGE.render("GAME OVER", True, (80, 0, 0))
        s.blit(shadow, (SW // 2 - text.get_width() // 2 + 3, SH // 2 - 78))
        s.blit(text, (SW // 2 - text.get_width() // 2, SH // 2 - 80))

        score_t = FONT_MED.render(f"DIEM SO: {self.score}", True, (255, 215, 80))
        s.blit(score_t, (SW // 2 - score_t.get_width() // 2, SH // 2 - 10))

        stats_lines = [
            f"Xe tang tieu diet: {self.total_kills}",
            f"Man dat duoc: {self.level}",
            f"Combo cao nhat: {self.stats['max_combo']}",
        ]
        for i, line in enumerate(stats_lines):
            lt = FONT_SM.render(line, True, (180, 185, 200))
            s.blit(lt, (SW // 2 - lt.get_width() // 2, SH // 2 + 20 + i * 22))

        pulse = abs(math.sin(self.tick * 0.05))
        restart_t = FONT_MED.render("[ ENTER ] DE TIEP TUC", True, (int(180 + 75 * pulse), int(180 + 75 * pulse), 255))
        s.blit(restart_t, (SW // 2 - restart_t.get_width() // 2, SH // 2 + 100))

    def draw_level_clear(self):
        s = self._surf
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        s.blit(overlay, (0, 0))

        # Victory sparkles
        for i in range(30):
            x = (i * 47 + self.tick * 2) % SW
            y = (i * 31 + self.tick) % SH
            a = int(abs(math.sin(self.tick * 0.1 + i)) * 220)
            c = [(255, 255, 100), (100, 255, 200), (255, 150, 255), (100, 200, 255)][i % 4]
            ps = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*c, max(0, a)), (4, 4), 3)
            s.blit(ps, (int(x), int(y)))

        text = FONT_TITLE.render(f"MAN {self.level} HOAN THANH!", True, (80, 255, 130))
        shadow = FONT_TITLE.render(f"MAN {self.level} HOAN THANH!", True, (0, 60, 20))
        s.blit(shadow, (SW // 2 - text.get_width() // 2 + 2, SH // 2 - 78))
        s.blit(text, (SW // 2 - text.get_width() // 2, SH // 2 - 80))

        score_t = FONT_MED.render(f"DIEM: {self.score}", True, (255, 215, 80))
        s.blit(score_t, (SW // 2 - score_t.get_width() // 2, SH // 2 - 20))

        kills_t = FONT_SM.render(f"TIEU DIET: {self.kills} / {self.total_enemies}", True, (200, 220, 200))
        s.blit(kills_t, (SW // 2 - kills_t.get_width() // 2, SH // 2 + 10))

        money_t = FONT_SM.render(f"TIEN: ${self.money}", True, (100, 255, 120))
        s.blit(money_t, (SW // 2 - money_t.get_width() // 2, SH // 2 + 35))

        # Next level preview
        next_theme = self.get_theme_for_level(self.level + 1)
        theme_names = {"default": "CHIEN TRUONG", "desert": "SA MAC", "snow": "BANG GIA",
                      "city": "THANH PHO", "jungle": "RUNG RAM", "lava": "NUI LUA"}
        next_t = FONT_SM.render(f"Man tiep theo: {theme_names.get(next_theme, '???')}", True, (160, 180, 220))
        s.blit(next_t, (SW // 2 - next_t.get_width() // 2, SH // 2 + 60))

        pulse = abs(math.sin(self.tick * 0.06))
        next_btn = FONT_MED.render("[ ENTER ] TIEP TUC", True, (int(180 + 75 * pulse), 255, int(180 + 75 * pulse)))
        s.blit(next_btn, (SW // 2 - next_btn.get_width() // 2, SH // 2 + 95))

    def draw_pause(self):
        self.draw_game()
        s = self._surf
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        s.blit(overlay, (0, 0))

        title = FONT_TITLE.render("TAM DUNG", True, (255, 255, 255))
        s.blit(title, (SW // 2 - title.get_width() // 2, SH // 4 - 20))

        for i, item in enumerate(self.pause_items):
            is_sel = i == self.pause_sel
            if is_sel:
                pulse = abs(math.sin(self.tick * 0.15))
                color = (min(255, int(255 + 50 * pulse)), min(255, int(220 + 35 * pulse)), 50)
                # Selection background
                txt_temp = FONT_MED.render(item, True, color)
                rect = txt_temp.get_rect(center=(SW // 2, SH // 2 - 60 + i * 45))
                sel_bg = pygame.Surface((rect.width + 40, rect.height + 14), pygame.SRCALPHA)
                pygame.draw.rect(sel_bg, (50, 60, 100, 180), (0, 0, rect.width + 40, rect.height + 14), border_radius=8)
                pygame.draw.rect(sel_bg, (100, 150, 255), (0, 0, rect.width + 40, rect.height + 14), 2, border_radius=8)
                s.blit(sel_bg, (rect.x - 20, rect.y - 7))
            else:
                color = (130, 130, 140)

            txt = FONT_MED.render(item, True, color)
            rect = txt.get_rect(center=(SW // 2, SH // 2 - 60 + i * 45))
            s.blit(txt, rect)

        instr = FONT_SM.render("[ MUI TEN ] CHON  -  [ ENTER ] DONG Y", True, (100, 110, 130))
        s.blit(instr, (SW // 2 - instr.get_width() // 2, SH - 80))

    def draw_backpack_ui(self, surf):
        slot_size = 44
        margin = 8
        bx = SW - (slot_size + margin) * 3 - 90
        by = 10

        # Backpack label
        bp_t = FONT_SM.render("BALO", True, (120, 130, 160))
        surf.blit(bp_t, (bx, by - 2))

        for i in range(3):
            sx = bx + i * (slot_size + margin)
            sy = by + 14

            # Slot bg
            slot_bg = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
            pygame.draw.rect(slot_bg, (25, 28, 40, 200), (0, 0, slot_size, slot_size), border_radius=8)
            has_item = i < len(self.backpack)
            border_c = (100, 150, 220) if has_item else (50, 55, 70)
            pygame.draw.rect(slot_bg, border_c, (0, 0, slot_size, slot_size), 2, border_radius=8)
            surf.blit(slot_bg, (sx, sy))

            # Slot number
            num_t = FONT_SM.render(str(i + 1), True, (100, 110, 130))
            surf.blit(num_t, (sx + 4, sy + 2))

            if has_item:
                kind = self.backpack[i]
                if kind in sprites.items:
                    img = pygame.transform.scale(sprites.items[kind], (30, 30))
                    surf.blit(img, (sx + 7, sy + 8))
                # Highlight
                hl = pygame.Surface((slot_size - 4, 12), pygame.SRCALPHA)
                pygame.draw.ellipse(hl, (255, 255, 255, 25), (0, 0, slot_size - 4, 12))
                surf.blit(hl, (sx + 2, sy + 2))

# ═══════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════
def main():
    game = Game()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            game.handle_event(ev)
        game.update()
        game.draw()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
