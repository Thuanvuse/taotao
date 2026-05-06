"""
HYPER PREMIUM Sprite Engine v5.0
Tank Dai Chien - ULTIMATE EDITION
Maximum visual quality - detailed 3D shading, rich textures, dramatic effects
"""
import pygame, math, random
from enum import Enum

TS = 32

# ═══════════════════════════════════════════════
#  MATERIAL & COLOR SYSTEM
# ═══════════════════════════════════════════════
class Material(Enum):
    MATTE = 0; METALLIC = 1; RUSTY = 2; CAMO = 3; CHROME = 4; NEON = 5

bullet_colors = {
    "normal": (255, 225, 80), "enemy": (255, 110, 85),
    "pierce": (80, 200, 255), "bomb": (255, 100, 50),
    "laser": (0, 255, 180), "plasma": (200, 50, 255),
}

def _clamp(v): return max(0, min(255, int(v)))
def _lighter(c, amt=40): return tuple(_clamp(x + amt) for x in c)
def _darker(c, amt=40): return tuple(_clamp(x - amt) for x in c)
def _mix(c1, c2, t=0.5): return tuple(_clamp(c1[i]*(1-t)+c2[i]*t) for i in range(min(len(c1),len(c2))))

TANK_COLORS = {
    "player": {
        "body": (50, 185, 75), "body2": (40, 155, 60), "body_hi": (130, 245, 155),
        "turret": (55, 200, 85), "turret_hi": (150, 255, 180),
        "barrel": (65, 190, 95), "barrel_hi": (170, 255, 200),
        "track": (28, 65, 32), "track_hi": (50, 100, 55), "rivet": (75, 130, 80),
        "accent": (255, 230, 60), "glow": (100, 255, 130, 60),
        "material": Material.METALLIC, "eye": (20, 20, 25), "star": (255, 255, 180),
    },
    "enemy_a": {
        "body": (210, 55, 50), "body2": (170, 35, 35), "body_hi": (255, 140, 130),
        "turret": (195, 50, 45), "turret_hi": (255, 155, 140),
        "barrel": (230, 85, 75), "barrel_hi": (255, 170, 155),
        "track": (90, 28, 28), "track_hi": (130, 45, 45), "rivet": (160, 65, 65),
        "accent": (255, 200, 60), "glow": (255, 80, 60, 50),
        "material": Material.RUSTY, "eye": (25, 15, 15), "star": (255, 200, 180),
    },
    "enemy_b": {
        "body": (55, 85, 210), "body2": (35, 55, 170), "body_hi": (130, 160, 255),
        "turret": (50, 75, 195), "turret_hi": (140, 165, 255),
        "barrel": (75, 105, 230), "barrel_hi": (155, 180, 255),
        "track": (22, 35, 95), "track_hi": (40, 60, 130), "rivet": (60, 80, 160),
        "accent": (100, 200, 255), "glow": (60, 120, 255, 50),
        "material": Material.METALLIC, "eye": (15, 15, 25), "star": (180, 210, 255),
    },
    "elite": {
        "body": (45, 45, 52), "body2": (28, 28, 35), "body_hi": (95, 95, 110),
        "turret": (38, 38, 48), "turret_hi": (85, 85, 105),
        "barrel": (65, 65, 78), "barrel_hi": (110, 110, 130),
        "track": (18, 18, 22), "track_hi": (35, 35, 45), "rivet": (55, 55, 65),
        "accent": (255, 120, 30), "glow": (255, 100, 30, 60),
        "material": Material.CHROME, "eye": (255, 40, 10), "star": (255, 180, 80),
    },
    "boss": {
        "body": (90, 20, 110), "body2": (60, 10, 75), "body_hi": (160, 70, 200),
        "turret": (80, 18, 100), "turret_hi": (150, 65, 190),
        "barrel": (130, 45, 170), "barrel_hi": (200, 110, 240),
        "track": (45, 12, 58), "track_hi": (65, 22, 85), "rivet": (95, 45, 115),
        "accent": (255, 50, 220), "glow": (255, 0, 200, 80),
        "material": Material.NEON, "eye": (255, 0, 100), "star": (255, 160, 255),
    },
}

# ═══════════════════════════════════════════════
#  ADVANCED DRAWING HELPERS
# ═══════════════════════════════════════════════

def draw_beveled_rect(surf, color, rect, depth=3, radius=0):
    x, y, w, h = rect
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    hi = _lighter(color, 55)
    sh = _darker(color, 55)
    for i in range(depth):
        f = 1.0 - i / max(1, depth)
        hc = _mix(color, hi, f * 0.7)
        sc = _mix(color, sh, f * 0.7)
        pygame.draw.line(surf, hc, (x+i, y+i), (x+w-i-1, y+i))
        pygame.draw.line(surf, hc, (x+i, y+i+1), (x+i, y+h-i-1))
        pygame.draw.line(surf, sc, (x+w-i-1, y+i+1), (x+w-i-1, y+h-i-1))
        pygame.draw.line(surf, sc, (x+i+1, y+h-i-1), (x+w-i-1, y+h-i-1))

def draw_gloss(surf, rect, intensity=100):
    x, y, w, h = rect
    g = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h // 2):
        a = int(intensity * (1 - i / (h / 2)) * 0.6)
        pygame.draw.line(g, (255, 255, 255, max(0, min(255, a))), (0, i), (w, i))
    surf.blit(g, (x, y))

def draw_noise(surf, rect, color, var=18, density=0.35):
    x, y, w, h = rect
    for _ in range(int(w * h * density)):
        px = x + random.randint(0, w - 1)
        py = y + random.randint(0, h - 1)
        off = random.randint(-var, var)
        nc = tuple(_clamp(c + off) for c in color)
        if 0 <= px < surf.get_width() and 0 <= py < surf.get_height():
            surf.set_at((px, py), nc)

def draw_radial_glow(surf, center, color, radius, alpha=80):
    g = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        a = int(alpha * (r / radius) ** 0.5 * (1 - r / radius))
        c = (*color[:3], max(0, min(255, a)))
        pygame.draw.circle(g, c, (radius, radius), r)
    surf.blit(g, (center[0] - radius, center[1] - radius))

def draw_metallic_sheen(surf, rect, angle=30):
    x, y, w, h = rect
    g = pygame.Surface((w, h), pygame.SRCALPHA)
    rad = math.radians(angle)
    for i in range(w):
        for j in range(h):
            d = abs(math.cos(rad) * i + math.sin(rad) * j)
            v = math.sin(d * 0.3) * 0.5 + 0.5
            a = int(v * 40)
            g.set_at((i, j), (255, 255, 255, max(0, min(255, a))))
    surf.blit(g, (x, y))

# ═══════════════════════════════════════════════
#  MAP TILES - HYPER DETAILED
# ═══════════════════════════════════════════════

def make_brick_tile_ultra():
    s = pygame.Surface((TS, TS))
    mortar = (85, 50, 30)
    s.fill(mortar)
    for row in range(4):
        y = row * 8
        offset = 8 if row % 2 else 0
        for col in range(-1, 3):
            bx = col * 16 + offset
            if bx >= TS: bx -= TS
            r = random.randint(0, 30)
            brick_c = (155 + r, 75 + r//2, 42 + r//3)
            bw = min(15, TS - max(0, bx))
            if bx < 0: bw = 15 + bx; bx = 0
            if bw <= 0: continue
            draw_beveled_rect(s, brick_c, (bx + 1, y + 1, bw - 1, 6), 2)
            # Weathering cracks
            if random.random() < 0.3:
                cx = bx + random.randint(2, max(3, bw - 2))
                cy = y + random.randint(2, 5)
                pygame.draw.line(s, _darker(brick_c, 30), (cx, cy), (cx + random.randint(-2, 2), cy + random.randint(1, 3)))
            # Subtle texture
            for _ in range(3):
                px = bx + random.randint(1, max(2, bw-1))
                py = y + random.randint(1, 5)
                if 0 <= px < TS and 0 <= py < TS:
                    s.set_at((px, py), _mix(brick_c, mortar, 0.3))
    # Overall weathering
    draw_noise(s, (0, 0, TS, TS), (160, 80, 48), 12, 0.08)
    return s

def make_steel_tile_ultra():
    s = pygame.Surface((TS, TS))
    base = (150, 155, 172)
    s.fill(base)
    # Main plate
    draw_beveled_rect(s, (168, 173, 195), (2, 2, TS-4, TS-4), 4, 1)
    # Brushed metal lines
    for i in range(3, TS-3, 2):
        intensity = 0.15 + 0.1 * math.sin(i * 0.4)
        lc = _mix(base, (220, 225, 240), intensity)
        pygame.draw.line(s, lc, (3, i), (TS-4, i))
    # Corner bolts with 3D effect
    for dx, dy in [(7, 7), (TS-8, 7), (7, TS-8), (TS-8, TS-8)]:
        pygame.draw.circle(s, (105, 110, 122), (dx, dy), 4)
        pygame.draw.circle(s, (130, 135, 150), (dx, dy), 3)
        pygame.draw.circle(s, (175, 180, 195), (dx-1, dy-1), 2)
        pygame.draw.circle(s, (85, 90, 100), (dx, dy), 4, 1)
        # Slot in bolt
        pygame.draw.line(s, (80, 85, 95), (dx-2, dy), (dx+2, dy), 1)
    # Center cross mark
    c = TS // 2
    pygame.draw.line(s, (125, 130, 148), (c-5, c), (c+5, c), 2)
    pygame.draw.line(s, (125, 130, 148), (c, c-5), (c, c+5), 2)
    # Gloss overlay
    draw_gloss(s, (3, 3, TS-6, TS//2-2), 55)
    # Subtle reflections
    for _ in range(3):
        rx = random.randint(4, TS-5)
        ry = random.randint(4, TS-5)
        pygame.draw.circle(s, (190, 195, 210), (rx, ry), 1)
    return s

def make_grass_tile_ultra():
    s = pygame.Surface((TS, TS), pygame.SRCALPHA)
    # Dense grass blades with variety
    for _ in range(55):
        gx = random.randint(0, TS-1)
        gy = random.randint(2, TS-1)
        h = random.randint(4, 14)
        sway = random.randint(-3, 3)
        shade = random.random()
        if shade < 0.3:
            gc = (random.randint(25, 50), random.randint(160, 220), random.randint(25, 55))
        elif shade < 0.7:
            gc = (random.randint(40, 70), random.randint(130, 180), random.randint(35, 65))
        else:
            gc = (random.randint(60, 90), random.randint(180, 230), random.randint(40, 70))
        w = random.choice([1, 1, 1, 2])
        # Draw blade with curve
        mid_sway = sway // 2
        pts = [(gx, gy), (gx + mid_sway, gy - h//2), (gx + sway, gy - h)]
        if len(pts) >= 2:
            pygame.draw.lines(s, gc, False, pts, w)
    # Wildflowers
    for _ in range(random.randint(2, 6)):
        fx = random.randint(4, TS-5)
        fy = random.randint(4, TS-6)
        fc = random.choice([(255, 255, 100), (255, 180, 200), (200, 160, 255), (255, 200, 120)])
        pygame.draw.circle(s, fc, (fx, fy), random.choice([1, 2]))
        if random.random() < 0.5:
            pygame.draw.circle(s, _lighter(fc, 60), (fx, fy-1), 1)
    # Ground debris
    for _ in range(4):
        dx = random.randint(1, TS-2)
        dy = random.randint(TS//2, TS-2)
        pygame.draw.circle(s, (80, 60, 40, 60), (dx, dy), 1)
    return s

def make_crate_tile_ultra():
    s = pygame.Surface((TS, TS))
    wood_base = (165, 120, 70)
    s.fill((90, 65, 38))
    # Main wood panel
    draw_beveled_rect(s, wood_base, (2, 2, TS-4, TS-4), 3, 2)
    # Wood grain
    for y in range(3, TS-3):
        grain = int(math.sin(y * 0.5 + random.random()) * 8)
        gc = _mix(wood_base, _darker(wood_base, 15), abs(grain) / 8)
        pygame.draw.line(s, gc, (3, y), (TS-4, y))
    # Cross braces
    pygame.draw.line(s, (100, 72, 42), (3, 3), (TS-4, TS-4), 2)
    pygame.draw.line(s, (100, 72, 42), (TS-4, 3), (3, TS-4), 2)
    pygame.draw.line(s, _lighter((100, 72, 42), 20), (4, 3), (TS-3, TS-4), 1)
    # Border frame
    pygame.draw.rect(s, (95, 68, 40), (2, 2, TS-4, TS-4), 2)
    # Center nail/circle
    pygame.draw.circle(s, (110, 78, 45), (TS//2, TS//2), 4)
    pygame.draw.circle(s, (85, 60, 35), (TS//2, TS//2), 4, 1)
    pygame.draw.circle(s, (140, 105, 65), (TS//2-1, TS//2-1), 1)
    # Wood texture noise
    draw_noise(s, (3, 3, TS-6, TS-6), wood_base, 12, 0.1)
    return s

def make_water_tile_ultra(frame=0):
    s = pygame.Surface((TS, TS))
    t = frame * 0.3
    # Deep water base gradient
    for y in range(TS):
        depth = y / TS
        r = int(25 + 15 * depth)
        g = int(60 + 30 * depth + 8 * math.sin(t + y * 0.2))
        b = int(155 + 30 * math.sin(t * 0.7 + y * 0.15) + 20 * depth)
        pygame.draw.line(s, (_clamp(r), _clamp(g), _clamp(b)), (0, y), (TS, y))
    # Wave highlights
    for wave in range(5):
        wy = int((wave * 7 + frame * 1.5) % TS)
        wx_off = int(math.sin(t + wave) * 4)
        for x in range(0, TS, 2):
            wx = (x + wx_off) % TS
            wave_a = int(50 + 30 * math.sin(x * 0.3 + t))
            if 0 <= wy < TS:
                s.set_at((wx, wy), _mix(s.get_at((wx, wy))[:3], (120, 180, 255), wave_a / 255))
    # Foam/sparkle highlights
    for _ in range(4):
        sx = int((random.randint(2, TS-3) + math.sin(t * 0.5) * 3) % TS)
        sy = random.randint(2, TS-3)
        bright = int(80 + 40 * math.sin(t + sx + sy))
        pygame.draw.circle(s, (_clamp(bright + 100), _clamp(bright + 140), 255, 90), (sx, sy), random.choice([1, 2]))
    # Caustic light patterns
    for _ in range(3):
        cx = int((random.randint(0, TS) + math.sin(t * 0.3) * 5) % TS)
        cy = int((random.randint(0, TS) + math.cos(t * 0.4) * 3) % TS)
        pygame.draw.ellipse(s, (100, 170, 255, 25), (cx-3, cy-1, 6, 3))
    return s

def make_floor_tile_ultra(theme="default"):
    s = pygame.Surface((TS, TS))
    if theme == "desert":
        # Sandy ground with dunes and pebbles
        base = (190, 170, 130)
        s.fill(base)
        # Sand texture waves
        for y in range(TS):
            wave = int(5 * math.sin(y * 0.3))
            for x in range(TS):
                v = math.sin((x + wave) * 0.2) * 8
                c = (_clamp(base[0] + v), _clamp(base[1] + v - 2), _clamp(base[2] + v - 5))
                s.set_at((x, y), c)
        # Pebbles
        for _ in range(5):
            px, py = random.randint(2, TS-3), random.randint(2, TS-3)
            pc = (random.randint(160, 185), random.randint(145, 165), random.randint(105, 125))
            pygame.draw.circle(s, pc, (px, py), random.choice([1, 2]))
            pygame.draw.circle(s, _lighter(pc, 20), (px, py-1), 1)
        draw_noise(s, (0, 0, TS, TS), base, 8, 0.15)
    elif theme == "snow":
        # Snowy ground with sparkle and tracks
        base = (225, 230, 240)
        s.fill(base)
        for y in range(TS):
            for x in range(TS):
                v = random.randint(-5, 5)
                s.set_at((x, y), (_clamp(base[0]+v), _clamp(base[1]+v), _clamp(base[2]+v+2)))
        # Snow drifts
        for _ in range(3):
            dx, dy = random.randint(0, TS), random.randint(0, TS)
            r = random.randint(4, 8)
            pygame.draw.circle(s, (235, 240, 248), (dx, dy), r)
        # Ice sparkles
        for _ in range(4):
            sx, sy = random.randint(0, TS-1), random.randint(0, TS-1)
            s.set_at((sx, sy), (245, 250, 255))
    elif theme == "city":
        # Concrete/asphalt with lane markings
        base = (62, 64, 72)
        s.fill(base)
        # Concrete tile pattern
        for y in range(0, TS, 16):
            for x in range(0, TS, 16):
                tile_c = (_clamp(base[0] + random.randint(-3, 3)),
                         _clamp(base[1] + random.randint(-3, 3)),
                         _clamp(base[2] + random.randint(-3, 3)))
                pygame.draw.rect(s, tile_c, (x+1, y+1, 14, 14))
                # Subtle border
                pygame.draw.rect(s, _lighter(base, 8), (x, y, 16, 16), 1)
        # Cracks
        if random.random() < 0.4:
            cx = random.randint(4, TS-5)
            cy = random.randint(4, TS-5)
            for _ in range(random.randint(2, 5)):
                nx = cx + random.randint(-3, 3)
                ny = cy + random.randint(-3, 3)
                pygame.draw.line(s, _darker(base, 15), (cx, cy), (nx, ny))
                cx, cy = nx, ny
        draw_noise(s, (0, 0, TS, TS), base, 5, 0.1)
    elif theme == "jungle":
        # Dense jungle floor with roots and leaves
        base = (32, 52, 28)
        s.fill(base)
        # Leaf litter layers
        for _ in range(15):
            lx, ly = random.randint(0, TS-1), random.randint(0, TS-1)
            lc = random.choice([
                (40, 65, 30), (28, 48, 22), (50, 70, 35), (35, 55, 25)
            ])
            lr = random.randint(2, 5)
            pygame.draw.ellipse(s, lc, (lx-lr, ly-lr//2, lr*2, lr))
        # Small roots
        for _ in range(3):
            rx = random.randint(0, TS)
            ry = random.randint(0, TS)
            pygame.draw.line(s, (55, 40, 25), (rx, ry), (rx + random.randint(-8, 8), ry + random.randint(-4, 4)), 1)
        # Mushrooms
        if random.random() < 0.3:
            mx, my = random.randint(4, TS-5), random.randint(4, TS-5)
            pygame.draw.rect(s, (140, 120, 80), (mx, my, 2, 4))
            pygame.draw.circle(s, (180, 50, 50), (mx+1, my), 3)
        draw_noise(s, (0, 0, TS, TS), base, 10, 0.15)
    elif theme == "lava":
        # Dark volcanic rock with glowing cracks
        base = (38, 16, 12)
        s.fill(base)
        # Rocky texture
        for y in range(TS):
            for x in range(TS):
                v = random.randint(-6, 6)
                s.set_at((x, y), (_clamp(base[0]+v+2), _clamp(base[1]+v), _clamp(base[2]+v)))
        # Lava cracks (glowing)
        if random.random() < 0.5:
            cx, cy = random.randint(4, TS-5), random.randint(4, TS-5)
            for _ in range(random.randint(3, 6)):
                nx = cx + random.randint(-4, 4)
                ny = cy + random.randint(-4, 4)
                # Glow around crack
                pygame.draw.line(s, (120, 40, 10), (cx, cy), (nx, ny), 3)
                pygame.draw.line(s, (200, 80, 20), (cx, cy), (nx, ny), 2)
                pygame.draw.line(s, (255, 160, 40), (cx, cy), (nx, ny), 1)
                cx, cy = nx, ny
        # Ember spots
        for _ in range(2):
            ex, ey = random.randint(2, TS-3), random.randint(2, TS-3)
            pygame.draw.circle(s, (100, 30, 10), (ex, ey), 2)
            pygame.draw.circle(s, (180, 60, 15), (ex, ey), 1)
    else:
        # Default: dark concrete with subtle grid
        base = (30, 32, 42)
        s.fill(base)
        for y in range(0, TS, 8):
            for x in range(0, TS, 8):
                v = random.randint(-3, 3)
                tile_c = (_clamp(base[0]+v), _clamp(base[1]+v), _clamp(base[2]+v+1))
                pygame.draw.rect(s, tile_c, (x, y, 7, 7))
        # Grid lines
        for i in range(0, TS+1, 8):
            pygame.draw.line(s, _lighter(base, 6), (i, 0), (i, TS))
            pygame.draw.line(s, _lighter(base, 6), (0, i), (TS, i))
        draw_noise(s, (0, 0, TS, TS), base, 4, 0.06)
    return s

def make_base_tile_ultra():
    s = pygame.Surface((TS, TS), pygame.SRCALPHA)
    cx, cy = TS//2, TS//2
    # Outer ring with gradient
    for r in range(TS//2, TS//2-4, -1):
        t = (TS//2 - r) / 4
        c = _mix((200, 160, 40), (255, 220, 80), t)
        pygame.draw.circle(s, c, (cx, cy), r)
    # Inner plate
    pygame.draw.circle(s, (180, 140, 35), (cx, cy), TS//2-4)
    pygame.draw.circle(s, (210, 170, 50), (cx, cy), TS//2-6)
    # Star emblem
    pts = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = 9 if i % 2 == 0 else 4
        pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    pygame.draw.polygon(s, (255, 240, 140), pts)
    pygame.draw.polygon(s, (255, 255, 200), pts, 1)
    # Gloss
    draw_gloss(s, (4, 4, TS-8, TS//2-4), 70)
    # Border
    pygame.draw.circle(s, (140, 100, 25), (cx, cy), TS//2-1, 2)
    return s

# ═══════════════════════════════════════════════
#  TANK SPRITES - MAXIMUM DETAIL
# ═══════════════════════════════════════════════

def _draw_tank_body(s, c, is_boss=False):
    """Draw tank body facing UP on a TS x TS surface."""
    # === TRACKS ===
    for tx in [1, 24]:
        tw, th = 7, 24
        ty = 4
        # Track base
        draw_beveled_rect(s, c["track"], (tx, ty, tw, th), 2, 2)
        # Tread pattern
        for i in range(ty + 2, ty + th - 1, 3):
            pygame.draw.line(s, c["track_hi"], (tx+1, i), (tx+tw-2, i))
            pygame.draw.line(s, _darker(c["track"], 20), (tx+1, i+1), (tx+tw-2, i+1))
        # Rivets on tracks
        for i in range(ty + 2, ty + th - 1, 5):
            pygame.draw.circle(s, c["rivet"], (tx + tw//2, i), 1)
        # Track wheels (visible)
        for wy in [ty+3, ty+th//2, ty+th-4]:
            pygame.draw.circle(s, _lighter(c["track"], 15), (tx+tw//2, wy), 2)
            pygame.draw.circle(s, c["track"], (tx+tw//2, wy), 2, 1)

    # === BODY ===
    bx, by, bw, bh = 5, 5, 22, 22
    # Shadow under body
    pygame.draw.rect(s, _darker(c["body"], 60), (bx+1, by+1, bw, bh), border_radius=3)
    # Main body
    draw_beveled_rect(s, c["body"], (bx, by, bw, bh), 3, 3)

    # Armor panel lines
    panel_c = _darker(c["body"], 25)
    pygame.draw.line(s, panel_c, (bx+3, by+3), (bx+3, by+bh-3))
    pygame.draw.line(s, panel_c, (bx+bw-4, by+3), (bx+bw-4, by+bh-3))
    pygame.draw.line(s, panel_c, (bx+3, by+bh//2), (bx+bw-4, by+bh//2))

    # Armor rivets
    for rx, ry in [(bx+4, by+4), (bx+bw-5, by+4), (bx+4, by+bh-5), (bx+bw-5, by+bh-5)]:
        pygame.draw.circle(s, c["rivet"], (rx, ry), 1)

    # Material effect
    mat = c["material"]
    if mat == Material.METALLIC:
        draw_gloss(s, (bx, by, bw, bh//2), 65)
    elif mat == Material.CHROME:
        draw_gloss(s, (bx, by, bw, bh//2), 100)
        # Chrome reflection lines
        for i in range(bx+2, bx+bw-2, 4):
            a = int(30 * abs(math.sin(i * 0.5)))
            pygame.draw.line(s, (*_lighter(c["body"], 40)[:3],), (i, by+2), (i+2, by+bh-3))
    elif mat == Material.RUSTY:
        draw_noise(s, (bx+1, by+1, bw-2, bh-2), c["body"], 22, 0.25)
        # Rust spots
        for _ in range(3):
            rx = bx + random.randint(3, bw-4)
            ry = by + random.randint(3, bh-4)
            pygame.draw.circle(s, _mix(c["body"], (120, 60, 30), 0.5), (rx, ry), random.randint(1, 2))
    elif mat == Material.NEON:
        # Neon glow edge
        glow_c = c["glow"]
        g = pygame.Surface((bw+4, bh+4), pygame.SRCALPHA)
        pygame.draw.rect(g, glow_c, (0, 0, bw+4, bh+4), border_radius=5)
        s.blit(g, (bx-2, by-2))
        # Redraw body on top
        draw_beveled_rect(s, c["body"], (bx, by, bw, bh), 3, 3)
        # Neon lines
        pygame.draw.rect(s, (*c["accent"][:3],), (bx+1, by+1, bw-2, bh-2), 1, border_radius=3)

    # Accent stripe
    stripe_c = c["accent"]
    pygame.draw.line(s, stripe_c, (bx+5, by+5), (bx+bw-6, by+5), 2)

    # Star/emblem
    star_c = c["star"]
    ecx, ecy = TS//2, TS//2 + 2
    pygame.draw.circle(s, _darker(stripe_c, 30), (ecx, ecy), 3)
    pygame.draw.circle(s, stripe_c, (ecx, ecy), 2)

def _draw_tank_turret(s, c):
    """Draw turret centered on TS//2."""
    cx, cy = TS//2, TS//2 + 1
    # Turret shadow
    pygame.draw.circle(s, _darker(c["turret"], 40), (cx+1, cy+1), 9)
    # Main turret
    pygame.draw.circle(s, c["turret"], (cx, cy), 9)
    pygame.draw.circle(s, c["turret_hi"], (cx, cy), 7)
    pygame.draw.circle(s, c["turret"], (cx, cy), 7, 1)
    # Hatch detail
    pygame.draw.circle(s, _darker(c["turret"], 15), (cx, cy), 4)
    pygame.draw.circle(s, c["turret_hi"], (cx, cy), 3)
    pygame.draw.circle(s, c["turret"], (cx, cy), 3, 1)
    # Specular highlight
    pygame.draw.circle(s, _lighter(c["turret_hi"], 40), (cx-2, cy-2), 2)
    pygame.draw.circle(s, (255, 255, 255, 180), (cx-3, cy-3), 1)

def _draw_tank_barrel(c):
    """Draw barrel pointing UP."""
    bw, bh = 6, 16
    barrel = pygame.Surface((bw, bh), pygame.SRCALPHA)
    # Main barrel shaft
    draw_beveled_rect(barrel, c["barrel"], (0, 2, bw, bh-2), 1, 1)
    # Barrel highlight stripe
    pygame.draw.line(barrel, c["barrel_hi"], (1, 3), (1, bh-2))
    pygame.draw.line(barrel, _darker(c["barrel"], 20), (bw-2, 3), (bw-2, bh-2))
    # Muzzle brake (tip)
    draw_beveled_rect(barrel, _lighter(c["barrel"], 15), (0, 0, bw, 4), 1, 1)
    pygame.draw.rect(barrel, _darker(c["barrel"], 10), (1, 1, bw-2, 1))
    # Ring near tip
    pygame.draw.line(barrel, _darker(c["barrel"], 30), (0, 4), (bw, 4))
    pygame.draw.line(barrel, c["barrel_hi"], (0, 5), (bw, 5))
    # Base ring where it meets turret
    pygame.draw.line(barrel, _darker(c["barrel"], 20), (0, bh-2), (bw, bh-2))
    return barrel

def make_tank_surface_ultra(tank_key, direction):
    c = TANK_COLORS[tank_key]
    base = pygame.Surface((TS, TS), pygame.SRCALPHA)

    # Draw body facing up
    _draw_tank_body(base, c, tank_key == "boss")
    # Draw turret
    _draw_tank_turret(base, c)
    # Draw barrel
    barrel = _draw_tank_barrel(c)

    # Compose with direction
    final = pygame.Surface((TS, TS), pygame.SRCALPHA)
    if direction == 0:  # UP
        final.blit(base, (0, 0))
        final.blit(barrel, (TS//2 - 3, -2))
    elif direction == 1:  # RIGHT
        rs = pygame.transform.rotate(base, -90)
        rb = pygame.transform.rotate(barrel, -90)
        final.blit(rs, (0, 0))
        final.blit(rb, (TS - 14, TS//2 - 3))
    elif direction == 2:  # DOWN
        rs = pygame.transform.rotate(base, 180)
        rb = pygame.transform.rotate(barrel, 180)
        final.blit(rs, (0, 0))
        final.blit(rb, (TS//2 - 3, TS - 14))
    elif direction == 3:  # LEFT
        rs = pygame.transform.rotate(base, 90)
        rb = pygame.transform.rotate(barrel, 90)
        final.blit(rs, (0, 0))
        final.blit(rb, (-2, TS//2 - 3))

    return final

# ═══════════════════════════════════════════════
#  BULLETS - BEAUTIFUL
# ═══════════════════════════════════════════════

def make_bullet(color=(255, 225, 80)):
    s = pygame.Surface((14, 14), pygame.SRCALPHA)
    # Outer glow
    pygame.draw.circle(s, (*color[:3], 35), (7, 7), 6)
    pygame.draw.circle(s, (*color[:3], 70), (7, 7), 5)
    # Core
    pygame.draw.circle(s, (*color[:3], 200), (7, 7), 3)
    # Hot center
    pygame.draw.circle(s, (255, 255, 240, 240), (6, 6), 2)
    pygame.draw.circle(s, (255, 255, 255), (5, 5), 1)
    return s

def make_bullet_advanced(kind="pierce"):
    s = pygame.Surface((18, 18), pygame.SRCALPHA)
    cx, cy = 9, 9
    if kind == "pierce":
        # Blue energy bolt
        pygame.draw.ellipse(s, (60, 160, 255, 40), (1, 3, 16, 12))
        pygame.draw.ellipse(s, (80, 200, 255, 120), (3, 5, 12, 8))
        pygame.draw.ellipse(s, (160, 230, 255, 220), (5, 6, 8, 6))
        pygame.draw.ellipse(s, (220, 245, 255), (6, 7, 6, 4))
        # Energy sparks
        for a in range(0, 360, 60):
            rad = math.radians(a)
            px = cx + math.cos(rad) * 7
            py = cy + math.sin(rad) * 5
            pygame.draw.circle(s, (100, 200, 255, 80), (int(px), int(py)), 1)
    elif kind == "bomb":
        # Bomb with fuse
        pygame.draw.circle(s, (55, 55, 58), (cx, cy), 7)
        pygame.draw.circle(s, (75, 75, 80), (cx, cy), 6)
        pygame.draw.circle(s, (90, 90, 95), (cx-1, cy-1), 4)
        # Highlight
        pygame.draw.circle(s, (120, 120, 130), (cx-2, cy-2), 2)
        # Fuse
        pygame.draw.line(s, (160, 140, 100), (cx+3, cy-5), (cx+5, cy-7), 2)
        # Fuse spark
        pygame.draw.circle(s, (255, 200, 50), (cx+5, cy-7), 2)
        pygame.draw.circle(s, (255, 255, 200), (cx+5, cy-7), 1)
        # Shell outline
        pygame.draw.circle(s, (40, 40, 42), (cx, cy), 7, 1)
    elif kind == "laser":
        # Green laser beam
        pygame.draw.rect(s, (0, 200, 140, 30), (1, 6, 16, 6))
        pygame.draw.rect(s, (0, 255, 180, 100), (3, 7, 12, 4))
        pygame.draw.rect(s, (100, 255, 220, 200), (4, 8, 10, 2))
        pygame.draw.rect(s, (200, 255, 240), (5, 8, 8, 1))
        # Tip glow
        pygame.draw.circle(s, (0, 255, 180, 60), (15, 9), 4)
    elif kind == "plasma":
        # Purple plasma orb
        pygame.draw.circle(s, (180, 40, 255, 30), (cx, cy), 8)
        pygame.draw.circle(s, (200, 60, 255, 80), (cx, cy), 6)
        pygame.draw.circle(s, (220, 100, 255, 160), (cx, cy), 4)
        pygame.draw.circle(s, (240, 180, 255), (cx, cy), 2)
        # Energy ring
        pygame.draw.circle(s, (200, 80, 255, 60), (cx, cy), 7, 1)
        # Electric arcs
        for a in range(0, 360, 90):
            rad = math.radians(a)
            px = cx + math.cos(rad) * 6
            py = cy + math.sin(rad) * 6
            pygame.draw.line(s, (220, 150, 255, 100), (cx, cy), (int(px), int(py)))
    return s

# ═══════════════════════════════════════════════
#  EXPLOSIONS - CINEMATIC QUALITY
# ═══════════════════════════════════════════════

def make_explosion_ultra(num_frames=24):
    frames = []
    for i in range(num_frames):
        s = pygame.Surface((96, 96), pygame.SRCALPHA)
        t = i / num_frames
        cx, cy = 48, 48

        # Shockwave ring (early)
        if t < 0.4:
            sw_r = int(10 + 45 * (t / 0.4))
            sw_a = int(100 * (1 - t / 0.4))
            pygame.draw.circle(s, (255, 255, 200, max(0, sw_a)), (cx, cy), sw_r, max(1, int(3 * (1 - t/0.4))))

        # Outer fire
        r_out = int(8 + 42 * t)
        a_out = int(220 * (1 - t) ** 1.2)
        for lr in range(r_out, max(0, r_out - 6), -2):
            lt = (r_out - lr) / 6
            fc = (255, _clamp(220 - 280*t + lt*60), _clamp(80 - 100*t + lt*40), _clamp(a_out * (1-lt*0.3)))
            pygame.draw.circle(s, fc, (cx, cy), lr)

        # Middle orange glow
        r_mid = int(6 + 32 * t)
        a_mid = int(255 * max(0, 1 - t * 1.4))
        pygame.draw.circle(s, (255, _clamp(200-200*t), _clamp(60-60*t), _clamp(a_mid)), (cx, cy), r_mid)

        # Hot white core
        if t < 0.45:
            r_core = int(5 + 18 * t)
            a_core = int(255 * (1 - t * 2.2))
            pygame.draw.circle(s, (255, 255, _clamp(220-200*t), _clamp(a_core)), (cx, cy), r_core)
            # Ultra bright center
            if t < 0.2:
                pygame.draw.circle(s, (255, 255, 255, _clamp(int(255*(1-t*5)))), (cx, cy), int(r_core * 0.5))

        # Flying debris/sparks
        if t < 0.8:
            num_sparks = 8
            for j in range(num_sparks):
                angle = math.radians(j * (360/num_sparks) + i * 20 + j * 7)
                dist = 8 + 40 * t + random.randint(-3, 3)
                sx = cx + math.cos(angle) * dist
                sy = cy + math.sin(angle) * dist
                spark_a = int(220 * (1 - t / 0.8))
                spark_r = max(1, int(3.5 * (1 - t)))
                sc = (255, _clamp(200 - 150*t), _clamp(50 - 50*t), _clamp(spark_a))
                pygame.draw.circle(s, sc, (int(sx), int(sy)), spark_r)
                # Spark trail
                if t < 0.5:
                    tx = cx + math.cos(angle) * (dist - 5)
                    ty = cy + math.sin(angle) * (dist - 5)
                    pygame.draw.line(s, (255, 180, 50, _clamp(int(spark_a*0.5))),
                                   (int(tx), int(ty)), (int(sx), int(sy)), 1)

        # Smoke
        if t > 0.25:
            smoke_t = (t - 0.25) / 0.75
            for ring in range(2):
                r_smoke = int(18 + 28 * smoke_t + ring * 5)
                a_smoke = int(70 * (1 - smoke_t) * (1 - ring * 0.3))
                gray = 80 + ring * 30
                pygame.draw.circle(s, (gray, gray, gray, _clamp(a_smoke)), (cx, cy), r_smoke,
                                 max(1, int(5 * (1 - smoke_t))))

        frames.append(s)
    return frames

def make_muzzle_flash_ultra():
    frames = []
    for i in range(8):
        s = pygame.Surface((28, 28), pygame.SRCALPHA)
        t = i / 8
        r = int(5 + 9 * (1 - t))
        a = int(255 * (1 - t))
        # Outer glow
        pygame.draw.circle(s, (255, 200, 80, _clamp(int(a*0.3))), (14, 14), r + 3)
        # Main flash
        pygame.draw.circle(s, (255, 240, 180, _clamp(a)), (14, 14), r)
        # Hot center
        if t < 0.4:
            ca = int(255 * (1 - t * 2.5))
            pygame.draw.circle(s, (255, 255, 255, _clamp(ca)), (14, 14), max(1, r // 2))
        frames.append(s)
    return frames

def make_spawn_effect_ultra():
    frames = []
    for i in range(16):
        s = pygame.Surface((TS + 10, TS + 10), pygame.SRCALPHA)
        t = i / 16
        cx, cy = (TS + 10) // 2, (TS + 10) // 2

        # Expanding energy rings
        for ring in range(3):
            rt = max(0, t - ring * 0.12)
            if rt > 0:
                r = int(5 + 22 * rt)
                a = int(200 * (1 - rt))
                thickness = max(1, int(3 * (1 - rt)))
                pygame.draw.circle(s, (80, 180, 255, _clamp(a)), (cx, cy), r, thickness)
                # Inner glow
                pygame.draw.circle(s, (120, 210, 255, _clamp(int(a*0.3))), (cx, cy), max(1, r-2))

        # Center flash
        if t < 0.5:
            fa = int(255 * (1 - t * 2))
            pygame.draw.circle(s, (255, 255, 255, _clamp(fa)), (cx, cy), max(1, int(7 * (1 - t * 2))))

        # Corner sparkles
        for corner in range(6):
            angle = math.radians(corner * 60 + 30 + t * 240)
            dist = 6 + 18 * t
            sx = cx + math.cos(angle) * dist
            sy = cy + math.sin(angle) * dist
            sa = int(180 * (1 - t))
            size = max(1, int(2.5 * (1 - t)))
            pygame.draw.circle(s, (150, 220, 255, _clamp(sa)), (int(sx), int(sy)), size)

        frames.append(s)
    return frames

# ═══════════════════════════════════════════════
#  ITEMS - PREMIUM ICONS
# ═══════════════════════════════════════════════

def make_item_surface(kind):
    s = pygame.Surface((32, 32), pygame.SRCALPHA)
    cx, cy = 16, 16

    colors = {
        "health": (235, 55, 55), "shield": (55, 115, 235),
        "speed": (55, 235, 115), "star": (255, 95, 45),
        "money": (255, 215, 45), "life": (255, 45, 145),
        "rapid": (255, 145, 35), "multi": (215, 195, 35),
        "pierce": (75, 195, 255), "bomb": (95, 95, 100),
        "laser": (0, 250, 175), "plasma": (195, 45, 255),
    }
    c = colors.get(kind, (200, 200, 200))
    hi = _lighter(c, 50)

    # Outer glow ring
    g = pygame.Surface((32, 32), pygame.SRCALPHA)
    for r in range(15, 10, -1):
        ga = int(25 * (15 - r))
        pygame.draw.circle(g, (*c, ga), (cx, cy), r)
    s.blit(g, (0, 0))

    # Dark background plate
    pygame.draw.circle(s, (18, 18, 28), (cx, cy), 13)
    pygame.draw.circle(s, (12, 12, 20), (cx, cy), 11)
    # Colored border ring
    pygame.draw.circle(s, c, (cx, cy), 12, 2)

    # Draw unique icon for each type
    if kind == "health":
        pygame.draw.rect(s, c, (12, 8, 8, 16), border_radius=2)
        pygame.draw.rect(s, c, (8, 12, 16, 8), border_radius=2)
        pygame.draw.rect(s, hi, (13, 9, 6, 14), border_radius=1)
        pygame.draw.rect(s, hi, (9, 13, 14, 6), border_radius=1)
    elif kind == "life":
        # Heart
        for dx, dy in [(12, 10), (20, 10)]:
            pygame.draw.circle(s, c, (dx, dy), 4)
        pygame.draw.polygon(s, c, [(8, 12), (24, 12), (16, 23)])
        for dx, dy in [(12, 10), (20, 10)]:
            pygame.draw.circle(s, hi, (dx-1, dy-1), 2)
    elif kind == "shield":
        pts = [(10, 8), (22, 8), (22, 16), (16, 23), (10, 16)]
        pygame.draw.polygon(s, c, pts)
        pygame.draw.polygon(s, hi, pts, 2)
        pygame.draw.line(s, hi, (16, 9), (16, 21), 2)
        pygame.draw.line(s, hi, (11, 13), (21, 13), 1)
    elif kind == "speed":
        pts = [(17, 6), (11, 14), (15, 14), (14, 25), (22, 13), (17, 13)]
        pygame.draw.polygon(s, c, pts)
        pygame.draw.polygon(s, hi, pts, 1)
        # Inner lightning
        pygame.draw.line(s, (255, 255, 200), (16, 9), (14, 15), 1)
    elif kind == "star":
        # Nuke star
        star_pts = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = 9 if i % 2 == 0 else 4
            star_pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        pygame.draw.polygon(s, c, star_pts)
        pygame.draw.polygon(s, hi, star_pts, 1)
        pygame.draw.circle(s, (255, 255, 200), (cx, cy), 2)
    elif kind == "money":
        # Gold coin
        pygame.draw.circle(s, (210, 170, 0), (cx, cy), 9)
        pygame.draw.circle(s, (255, 210, 30), (cx, cy), 8)
        pygame.draw.circle(s, (255, 230, 80), (cx, cy), 6)
        pygame.draw.circle(s, (210, 170, 0), (cx, cy), 8, 1)
        # $ sign
        pygame.draw.line(s, (160, 120, 0), (cx, cy-5), (cx, cy+5), 2)
        pygame.draw.arc(s, (160, 120, 0), (cx-3, cy-5, 6, 6), math.pi*0.3, math.pi*1.5, 2)
        pygame.draw.arc(s, (160, 120, 0), (cx-3, cy-1, 6, 6), -math.pi*0.7, math.pi*0.5, 2)
        # Gloss
        pygame.draw.circle(s, (255, 255, 180, 60), (cx-2, cy-2), 3)
    elif kind == "rapid":
        # Double bullet
        pygame.draw.rect(s, c, (10, 8, 4, 14), border_radius=2)
        pygame.draw.rect(s, c, (18, 8, 4, 14), border_radius=2)
        pygame.draw.rect(s, hi, (11, 9, 2, 12), border_radius=1)
        pygame.draw.rect(s, hi, (19, 9, 2, 12), border_radius=1)
        # Speed lines
        pygame.draw.line(s, (*c, 100), (8, 18), (8, 24))
        pygame.draw.line(s, (*c, 100), (24, 18), (24, 24))
    elif kind == "multi":
        # Triple spread
        for ox, oy, angle in [(-3, 2, 20), (0, 0, 0), (3, 2, -20)]:
            pygame.draw.ellipse(s, c, (cx+ox-2, cy+oy-5, 4, 11))
            pygame.draw.ellipse(s, hi, (cx+ox-1, cy+oy-4, 2, 9))
    elif kind == "pierce":
        # Arrow
        pts = [(cx, 6), (cx-5, 16), (cx-2, 16), (cx-2, 24), (cx+2, 24), (cx+2, 16), (cx+5, 16)]
        pygame.draw.polygon(s, c, pts)
        pygame.draw.polygon(s, hi, pts, 1)
    elif kind == "bomb":
        # Bomb
        pygame.draw.circle(s, (55, 55, 58), (cx, cy+1), 7)
        pygame.draw.circle(s, (80, 80, 85), (cx, cy+1), 6)
        pygame.draw.circle(s, (100, 100, 108), (cx-1, cy), 3)
        pygame.draw.rect(s, (120, 100, 60), (cx-1, cy-8, 3, 4))
        pygame.draw.circle(s, (255, 180, 40), (cx, cy-8), 3)
        pygame.draw.circle(s, (255, 255, 150), (cx, cy-8), 1)
    elif kind == "laser":
        # Laser beam icon
        pygame.draw.rect(s, c, (7, cy-1, 18, 3), border_radius=1)
        pygame.draw.rect(s, hi, (8, cy, 16, 1))
        pygame.draw.circle(s, hi, (24, cy), 3)
        pygame.draw.circle(s, (255, 255, 255), (24, cy), 1)
        # Lens
        pygame.draw.circle(s, c, (8, cy), 4)
        pygame.draw.circle(s, hi, (7, cy-1), 2)
    elif kind == "plasma":
        # Plasma orb
        pygame.draw.circle(s, (*c, 50), (cx, cy), 9)
        pygame.draw.circle(s, (*c, 120), (cx, cy), 7)
        pygame.draw.circle(s, hi, (cx, cy), 5)
        pygame.draw.circle(s, (255, 220, 255), (cx, cy), 2)
        # Electric arcs
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            px = cx + math.cos(rad) * 8
            py = cy + math.sin(rad) * 8
            pygame.draw.line(s, (*c, 80), (cx, cy), (int(px), int(py)))

    # Top gloss
    gloss = pygame.Surface((18, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(gloss, (255, 255, 255, 35), (0, 0, 18, 8))
    s.blit(gloss, (7, 5))

    return s

# ═══════════════════════════════════════════════
#  CHICKEN & DOG - CUTE SPRITES
# ═══════════════════════════════════════════════

def make_chicken_frames_ultra(num_frames=8):
    frames = []
    for i in range(num_frames):
        s = pygame.Surface((32, 32), pygame.SRCALPHA)
        bob = math.sin(i * 0.8) * 2
        by = int(12 + bob)
        # Shadow
        pygame.draw.ellipse(s, (0, 0, 0, 30), (8, 24, 16, 6))
        # Body
        pygame.draw.ellipse(s, (245, 220, 70), (6, by, 20, 16))
        pygame.draw.ellipse(s, (255, 240, 120), (8, by+2, 16, 12))
        # Wing
        wing_flap = 3 if i % 2 == 0 else 0
        pygame.draw.ellipse(s, (255, 235, 100), (5, by+3-wing_flap, 10, 9+wing_flap))
        # Head
        pygame.draw.circle(s, (255, 240, 120), (22, int(10+bob)), 7)
        # Comb
        for cx_off in range(-2, 3, 2):
            pygame.draw.circle(s, (230, 50, 50), (22+cx_off, int(4+bob)), 3)
        # Beak
        pygame.draw.polygon(s, (255, 160, 40), [(28, int(10+bob)), (32, int(12+bob)), (28, int(14+bob))])
        # Eye
        pygame.draw.circle(s, (25, 25, 35), (24, int(9+bob)), 2)
        pygame.draw.circle(s, (255, 255, 255), (25, int(8+bob)), 1)
        # Feet
        for fx in [12, 18]:
            pygame.draw.line(s, (230, 140, 40), (fx, by+14), (fx-2, 28+int(bob//2)), 2)
            pygame.draw.line(s, (230, 140, 40), (fx, by+14), (fx+2, 28+int(bob//2)), 2)
        frames.append(s)
    return frames

def make_dog_frames_ultra():
    frames = {}
    body_c = (145, 105, 65)
    belly_c = (205, 165, 125)
    nose_c = (25, 25, 35)
    for d in ["up", "down", "left", "right"]:
        df = []
        for i in range(4):
            s = pygame.Surface((36, 36), pygame.SRCALPHA)
            walk = math.sin(i * 1.5) * 3
            # Shadow
            pygame.draw.ellipse(s, (0, 0, 0, 25), (8, 28, 20, 6))
            # Body
            pygame.draw.ellipse(s, body_c, (8, 12, 20, 16))
            pygame.draw.ellipse(s, belly_c, (10, 14, 16, 12))
            # Tail
            tail_wag = int(math.sin(i * 2) * 4)
            pygame.draw.line(s, body_c, (10, 18), (4+tail_wag, 14), 3)
            # Legs
            leg_off = int(walk)
            for lx in [12, 22]:
                pygame.draw.rect(s, _darker(body_c, 15), (lx, 24+leg_off, 3, 6))
                pygame.draw.rect(s, _darker(body_c, 25), (lx, 28+leg_off, 4, 3))
            # Head per direction
            if d == "right":
                pygame.draw.circle(s, body_c, (26, 15), 10)
                pygame.draw.ellipse(s, (110, 75, 45), (24, 6, 8, 10))  # Ear
                pygame.draw.circle(s, nose_c, (34, 16), 3)
                pygame.draw.circle(s, (50, 50, 60), (29, 12), 3)  # Eye
                pygame.draw.circle(s, (255, 255, 255), (30, 11), 1)
            elif d == "left":
                pygame.draw.circle(s, body_c, (10, 15), 10)
                pygame.draw.ellipse(s, (110, 75, 45), (4, 6, 8, 10))
                pygame.draw.circle(s, nose_c, (2, 16), 3)
                pygame.draw.circle(s, (50, 50, 60), (7, 12), 3)
                pygame.draw.circle(s, (255, 255, 255), (6, 11), 1)
            elif d == "up":
                pygame.draw.circle(s, body_c, (18, 10), 10)
                pygame.draw.ellipse(s, (110, 75, 45), (8, 5, 6, 10))
                pygame.draw.ellipse(s, (110, 75, 45), (22, 5, 6, 10))
            else:  # down
                pygame.draw.circle(s, body_c, (18, 18), 10)
                pygame.draw.ellipse(s, (110, 75, 45), (8, 12, 6, 10))
                pygame.draw.ellipse(s, (110, 75, 45), (22, 12, 6, 10))
                pygame.draw.circle(s, nose_c, (18, 24), 3)
                pygame.draw.circle(s, (50, 50, 60), (15, 17), 3)
                pygame.draw.circle(s, (50, 50, 60), (21, 17), 3)
                pygame.draw.circle(s, (255, 255, 255), (14, 16), 1)
                pygame.draw.circle(s, (255, 255, 255), (20, 16), 1)
            df.append(s)
        frames[d] = df
    return frames

# ═══════════════════════════════════════════════
#  WEATHER EFFECTS
# ═══════════════════════════════════════════════

def make_rain_drop():
    s = pygame.Surface((4, 14), pygame.SRCALPHA)
    pygame.draw.line(s, (140, 170, 255, 80), (2, 0), (1, 10), 1)
    pygame.draw.line(s, (170, 200, 255, 140), (2, 3), (1, 12), 1)
    pygame.draw.circle(s, (180, 210, 255, 60), (1, 12), 2)
    return s

def make_snow_flake():
    s = pygame.Surface((8, 8), pygame.SRCALPHA)
    pygame.draw.circle(s, (225, 230, 250, 120), (4, 4), 3)
    pygame.draw.circle(s, (240, 245, 255, 180), (4, 4), 2)
    pygame.draw.circle(s, (255, 255, 255, 200), (3, 3), 1)
    return s

def make_sand_particle():
    s = pygame.Surface((5, 5), pygame.SRCALPHA)
    pygame.draw.circle(s, (205, 185, 145, 70), (2, 2), 2)
    pygame.draw.circle(s, (220, 200, 160, 100), (2, 2), 1)
    return s

def make_ember_particle():
    s = pygame.Surface((6, 6), pygame.SRCALPHA)
    pygame.draw.circle(s, (255, 120, 20, 60), (3, 3), 3)
    pygame.draw.circle(s, (255, 180, 40, 120), (3, 3), 2)
    pygame.draw.circle(s, (255, 230, 100), (3, 3), 1)
    return s

# ═══════════════════════════════════════════════
#  MINIMAP ICONS
# ═══════════════════════════════════════════════

def make_minimap_player_icon():
    s = pygame.Surface((6, 6), pygame.SRCALPHA)
    pygame.draw.rect(s, (80, 255, 120), (0, 0, 6, 6))
    pygame.draw.rect(s, (200, 255, 220), (1, 1, 4, 4))
    return s

def make_minimap_enemy_icon():
    s = pygame.Surface((4, 4), pygame.SRCALPHA)
    pygame.draw.rect(s, (255, 70, 70), (0, 0, 4, 4))
    return s

def make_minimap_base_icon():
    s = pygame.Surface((6, 6), pygame.SRCALPHA)
    pygame.draw.rect(s, (255, 220, 50), (0, 0, 6, 6))
    pygame.draw.rect(s, (255, 240, 120), (1, 1, 4, 4))
    return s

# ═══════════════════════════════════════════════
#  UI ELEMENTS
# ═══════════════════════════════════════════════

def make_button_bg(w, h, color=(35, 55, 95), border_color=(75, 125, 200)):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    # Shadow
    pygame.draw.rect(s, (0, 0, 0, 40), (2, 2, w, h), border_radius=8)
    # Main button
    pygame.draw.rect(s, (*color, 230), (0, 0, w, h), border_radius=8)
    # Inner gradient
    for i in range(h // 3):
        a = int(40 * (1 - i / (h / 3)))
        pygame.draw.line(s, (255, 255, 255, max(0, a)), (4, i + 2), (w - 4, i + 2))
    # Border
    pygame.draw.rect(s, border_color, (0, 0, w, h), 2, border_radius=8)
    return s

def make_panel_bg(w, h, color=(18, 22, 38)):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    # Shadow
    pygame.draw.rect(s, (0, 0, 0, 50), (3, 3, w, h), border_radius=12)
    # Main panel
    pygame.draw.rect(s, (*color, 235), (0, 0, w, h), border_radius=12)
    # Top highlight
    for i in range(min(6, h)):
        a = int(20 * (1 - i / 6))
        pygame.draw.line(s, (255, 255, 255, max(0, a)), (6, i + 3), (w - 6, i + 3))
    # Border
    pygame.draw.rect(s, (55, 75, 125), (0, 0, w, h), 2, border_radius=12)
    return s

def make_score_popup_font():
    try: f = pygame.font.SysFont("consolas", 16, bold=True)
    except: f = pygame.font.Font(None, 20)
    return {v: f.render(f"+{v}", True, (255, 255, 255)) for v in [50, 100, 150, 200, 500]}

# ═══════════════════════════════════════════════
#  SPRITE CACHE
# ═══════════════════════════════════════════════

class SpriteCache:
    def __init__(self):
        print("Loading HYPER PREMIUM sprites v5.0...")

        # Tiles
        self.brick = make_brick_tile_ultra()
        self.steel = make_steel_tile_ultra()
        self.grass = make_grass_tile_ultra()
        self.crate = make_crate_tile_ultra()
        self.base = make_base_tile_ultra()
        self.water_frames = [make_water_tile_ultra(i) for i in range(12)]

        # Floor themes
        self.floors = {}
        for theme in ["default", "desert", "snow", "city", "jungle", "lava"]:
            self.floors[theme] = make_floor_tile_ultra(theme)
        self.floor = self.floors["default"]

        # Tanks
        self.tanks = {k: [make_tank_surface_ultra(k, d) for d in range(4)] for k in TANK_COLORS}

        # Bullets
        self.bullet = make_bullet()
        self.bullet_enemy = make_bullet((255, 100, 100))
        self.bullet_pierce = make_bullet_advanced("pierce")
        self.bullet_bomb = make_bullet_advanced("bomb")
        self.bullet_laser = make_bullet_advanced("laser")
        self.bullet_plasma = make_bullet_advanced("plasma")

        # Effects
        self.explosion = make_explosion_ultra()
        self.muzzle_flash = make_muzzle_flash_ultra()
        self.spawn_effect = make_spawn_effect_ultra()

        # Items
        all_items = ["health", "shield", "speed", "star", "money", "life",
                     "rapid", "multi", "pierce", "bomb", "laser", "plasma"]
        self.items = {k: make_item_surface(k) for k in all_items}

        # Score popups
        self.score_popups = make_score_popup_font()

        # Entities
        self.chicken_frames = make_chicken_frames_ultra()
        self.dog_frames = make_dog_frames_ultra()

        # Weather
        self.rain_drop = make_rain_drop()
        self.snow_flake = make_snow_flake()
        self.sand_particle = make_sand_particle()
        self.ember = make_ember_particle()

        # Minimap icons
        self.minimap_player = make_minimap_player_icon()
        self.minimap_enemy = make_minimap_enemy_icon()
        self.minimap_base = make_minimap_base_icon()

        print("Sprites loaded successfully!")

    def set_floor_theme(self, theme):
        if theme in self.floors:
            self.floor = self.floors[theme]
