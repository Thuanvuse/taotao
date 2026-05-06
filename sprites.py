"""
PREMIUM ULTRA DELUXE Sprite Engine v3.0
Tank Dai Chien - ULTIMATE EDITION
Enhanced visuals, detailed tanks, premium tiles, weather effects, minimap support
"""
import os
import pygame, math, random
from enum import Enum

TS = 32

# Reference asset image — used to override a few item icons with pixel-art
# sprites sliced directly from the original art reference. If the file is
# missing or anything fails, the procedural icons are used as fallback.
ASSET_IMAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "assets", "tank_battle_assets.png")

# Item kind -> (left, top, right, bottom) bounding box in the asset image.
# Coordinates target the cleaner bottom rows of the items grid.
PIXEL_ART_ITEM_BOXES = {
    "freeze":    (470, 250, 545, 320),  # CLOCK (FREEZE)
    "max_power": (545, 320, 620, 390),  # PISTOL (MAX POWER)
    "grenade":   (620, 250, 695, 320),  # GRENADE (BOMB)
    "life":      (620, 320, 695, 390),  # HEART (EXTRA LIFE)
}


def _slice_pixel_art_item(asset_surface, box, output_size=30):
    """Slice a single item icon out of the asset image and key out the
    dark cell background + colored border by sampling edge colors."""
    left, top, right, bottom = box
    w = right - left
    h = bottom - top
    if (left < 0 or top < 0 or
            right > asset_surface.get_width() or
            bottom > asset_surface.get_height()):
        return None

    cell = pygame.Surface((w, h), pygame.SRCALPHA)
    src_rect = pygame.Rect(left, top, w, h)
    cell.blit(asset_surface, (0, 0), src_rect)

    # Sample edge pixels (border + cell background) — these will be removed.
    samples = []
    step = max(1, w // 8)
    for x in range(0, w, step):
        samples.append(cell.get_at((x, 0))[:3])
        samples.append(cell.get_at((x, h - 1))[:3])
    step = max(1, h // 8)
    for y in range(0, h, step):
        samples.append(cell.get_at((0, y))[:3])
        samples.append(cell.get_at((w - 1, y))[:3])

    # Build a 32-bit RGBA copy and mask out background pixels.
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            r, g, b, _ = cell.get_at((x, y))
            keep = True
            # Mask very dark pixels (cell background)
            if r + g + b < 60:
                keep = False
            else:
                for sr, sg, sb in samples:
                    dr, dg, db = r - sr, g - sg, b - sb
                    if dr * dr + dg * dg + db * db < 25 * 25:
                        keep = False
                        break
            if keep:
                out.set_at((x, y), (r, g, b, 255))

    return pygame.transform.scale(out, (output_size, output_size))


def try_load_pixel_art_items(asset_path=ASSET_IMAGE_PATH):
    """Try to load the asset image and slice item icons from it.

    Returns a dict mapping item kind -> pygame.Surface for any items that
    were successfully sliced. On any failure (missing file, bad image,
    etc.) returns an empty dict so the caller can fall back to procedural
    sprites.
    """
    if not os.path.exists(asset_path):
        return {}
    try:
        asset = pygame.image.load(asset_path).convert_alpha()
    except Exception as exc:  # noqa: BLE001
        print(f"[sprites] Could not load pixel art asset: {exc}")
        return {}

    result = {}
    for kind, box in PIXEL_ART_ITEM_BOXES.items():
        try:
            icon = _slice_pixel_art_item(asset, box)
            if icon is not None:
                result[kind] = icon
        except Exception as exc:  # noqa: BLE001
            print(f"[sprites] Slice failed for {kind}: {exc}")
    return result

# ═══════════════════════════════════════════════
#  MATERIAL & COLOR SYSTEM
# ═══════════════════════════════════════════════
class Material(Enum):
    MATTE = 0
    METALLIC = 1
    RUSTY = 2
    CAMO = 3
    CHROME = 4
    NEON = 5

bullet_colors = {
    "normal": (255, 225, 80),
    "enemy": (255, 110, 85),
    "pierce": (80, 200, 255),
    "bomb": (255, 100, 50),
    "laser": (0, 255, 180),
    "plasma": (200, 50, 255),
}

TANK_COLORS = {
    "player": {
        "body_base": (50, 200, 80), "body_shadow": (30, 140, 45), "body_highlight": (120, 255, 150),
        "body_specular": (200, 255, 220), "material": Material.METALLIC,
        "turret_base": (40, 170, 60), "turret_highlight": (100, 220, 130),
        "barrel_base": (70, 210, 100), "barrel_highlight": (150, 245, 170),
        "track_base": (30, 70, 35), "track_highlight": (55, 110, 60), "track_rivet": (80, 140, 85),
        "accent": (200, 255, 180), "eye_bg": (255, 255, 245), "pupil": (20, 20, 25),
        "blush": (255, 140, 140), "camo_color": (100, 200, 70),
        "stripe": (255, 220, 50), "emblem": (255, 255, 255),
    },
    "enemy_a": {
        "body_base": (220, 60, 60), "body_shadow": (160, 30, 30), "body_highlight": (255, 130, 120),
        "body_specular": (255, 190, 180), "material": Material.RUSTY,
        "turret_base": (190, 45, 45), "turret_highlight": (240, 120, 110),
        "barrel_base": (245, 95, 85), "barrel_highlight": (255, 160, 150),
        "track_base": (100, 30, 30), "track_highlight": (140, 50, 50), "track_rivet": (170, 70, 70),
        "accent": (255, 180, 170), "eye_bg": (255, 245, 240), "pupil": (25, 20, 20),
        "blush": (255, 160, 160), "camo_color": (190, 70, 50),
        "stripe": (200, 40, 40), "emblem": (255, 200, 200),
    },
    "enemy_b": {
        "body_base": (60, 90, 220), "body_shadow": (30, 50, 160), "body_highlight": (110, 140, 255),
        "body_specular": (170, 200, 255), "material": Material.METALLIC,
        "turret_base": (45, 65, 190), "turret_highlight": (110, 130, 240),
        "barrel_base": (80, 110, 245), "barrel_highlight": (140, 170, 255),
        "track_base": (25, 40, 100), "track_highlight": (45, 65, 140), "track_rivet": (65, 85, 170),
        "accent": (170, 190, 255), "eye_bg": (245, 248, 255), "pupil": (20, 20, 25),
        "blush": (160, 180, 255), "camo_color": (50, 70, 190),
        "stripe": (100, 130, 255), "emblem": (200, 220, 255),
    },
    "elite": {
        "body_base": (50, 50, 55), "body_shadow": (25, 25, 30), "body_highlight": (90, 90, 100),
        "body_specular": (140, 140, 155), "material": Material.CHROME,
        "turret_base": (40, 40, 45), "turret_highlight": (80, 80, 95),
        "barrel_base": (70, 70, 80), "barrel_highlight": (120, 120, 135),
        "track_base": (20, 20, 25), "track_highlight": (40, 40, 50), "track_rivet": (60, 60, 70),
        "accent": (255, 80, 30), "eye_bg": (255, 250, 245), "pupil": (255, 40, 10),
        "blush": (100, 10, 10), "camo_color": (35, 35, 40),
        "stripe": (255, 150, 0), "emblem": (255, 50, 50),
    },
    "boss": {
        "body_base": (80, 20, 100), "body_shadow": (50, 10, 65), "body_highlight": (140, 60, 180),
        "body_specular": (200, 120, 240), "material": Material.NEON,
        "turret_base": (70, 15, 90), "turret_highlight": (130, 50, 170),
        "barrel_base": (120, 40, 160), "barrel_highlight": (180, 100, 220),
        "track_base": (40, 10, 55), "track_highlight": (60, 20, 80), "track_rivet": (90, 40, 110),
        "accent": (255, 0, 200), "eye_bg": (255, 200, 255), "pupil": (255, 0, 100),
        "blush": (200, 50, 200), "camo_color": (100, 20, 130),
        "stripe": (255, 0, 255), "emblem": (255, 150, 255),
    },
}

# Player tier palettes (yellow -> gold -> orange -> red-orange -> premium)
# Mirrors the 5-tier player tanks in the asset reference image.
PLAYER_TIER_COLORS = [
    {  # Tier 0 - basic yellow
        "body_base": (220, 180, 50), "body_shadow": (160, 120, 25), "body_highlight": (255, 220, 110),
        "body_specular": (255, 240, 180), "material": Material.METALLIC,
        "turret_base": (200, 160, 40), "turret_highlight": (240, 200, 90),
        "barrel_base": (210, 170, 60), "barrel_highlight": (245, 215, 130),
        "track_base": (80, 60, 25), "track_highlight": (120, 95, 40), "track_rivet": (160, 130, 60),
        "accent": (255, 230, 150), "eye_bg": (255, 250, 240), "pupil": (40, 30, 10),
        "blush": (255, 180, 100), "camo_color": (200, 160, 50),
        "stripe": (255, 240, 80), "emblem": (255, 255, 220),
    },
    {  # Tier 1 - brighter gold
        "body_base": (235, 195, 50), "body_shadow": (170, 130, 20), "body_highlight": (255, 230, 120),
        "body_specular": (255, 245, 195), "material": Material.METALLIC,
        "turret_base": (215, 175, 40), "turret_highlight": (245, 215, 100),
        "barrel_base": (225, 185, 60), "barrel_highlight": (250, 225, 140),
        "track_base": (70, 50, 20), "track_highlight": (115, 90, 35), "track_rivet": (160, 130, 60),
        "accent": (255, 245, 170), "eye_bg": (255, 250, 240), "pupil": (40, 30, 10),
        "blush": (255, 200, 110), "camo_color": (220, 180, 50),
        "stripe": (255, 255, 100), "emblem": (255, 255, 230),
    },
    {  # Tier 2 - orange tint
        "body_base": (240, 160, 50), "body_shadow": (170, 100, 20), "body_highlight": (255, 200, 110),
        "body_specular": (255, 230, 180), "material": Material.METALLIC,
        "turret_base": (215, 145, 40), "turret_highlight": (245, 185, 95),
        "barrel_base": (225, 155, 60), "barrel_highlight": (255, 200, 130),
        "track_base": (75, 45, 20), "track_highlight": (115, 75, 35), "track_rivet": (160, 110, 55),
        "accent": (255, 225, 160), "eye_bg": (255, 250, 240), "pupil": (40, 25, 10),
        "blush": (255, 170, 90), "camo_color": (220, 145, 50),
        "stripe": (255, 220, 70), "emblem": (255, 255, 220),
    },
    {  # Tier 3 - deep orange / red trim
        "body_base": (240, 130, 40), "body_shadow": (170, 75, 15), "body_highlight": (255, 175, 90),
        "body_specular": (255, 215, 165), "material": Material.METALLIC,
        "turret_base": (215, 110, 30), "turret_highlight": (245, 165, 80),
        "barrel_base": (220, 130, 50), "barrel_highlight": (255, 180, 110),
        "track_base": (75, 35, 15), "track_highlight": (115, 60, 30), "track_rivet": (160, 90, 45),
        "accent": (255, 200, 130), "eye_bg": (255, 250, 240), "pupil": (40, 20, 10),
        "blush": (255, 150, 80), "camo_color": (220, 110, 40),
        "stripe": (255, 80, 50), "emblem": (255, 240, 200),
    },
    {  # Tier 4 - max power, premium look
        "body_base": (245, 110, 35), "body_shadow": (170, 55, 10), "body_highlight": (255, 160, 80),
        "body_specular": (255, 220, 180), "material": Material.CHROME,
        "turret_base": (220, 85, 25), "turret_highlight": (250, 150, 70),
        "barrel_base": (230, 105, 40), "barrel_highlight": (255, 170, 100),
        "track_base": (60, 30, 15), "track_highlight": (110, 55, 25), "track_rivet": (180, 100, 50),
        "accent": (255, 230, 180), "eye_bg": (255, 250, 240), "pupil": (255, 60, 30),
        "blush": (255, 130, 70), "camo_color": (220, 90, 30),
        "stripe": (255, 240, 80), "emblem": (255, 255, 255),
    },
]

# ═══════════════════════════════════════════════
#  HELPER DRAWING FUNCTIONS
# ═══════════════════════════════════════════════

def draw_bevel_rect(surf, color, rect, bevel_depth=2, border_radius=0):
    pygame.draw.rect(surf, color, rect, border_radius=border_radius)
    x, y, w, h = rect
    hl = [min(255, c + 50) for c in color]
    sh = [max(0, c - 50) for c in color]
    for i in range(bevel_depth):
        a = int(220 * (1 - i / max(1, bevel_depth)))
        pygame.draw.line(surf, (*hl[:3],), (x+i, y+i), (x+w-i-1, y+i), 1)
        pygame.draw.line(surf, (*hl[:3],), (x+i, y+i), (x+i, y+h-i-1), 1)
        pygame.draw.line(surf, (*sh[:3],), (x+w-i-1, y+i+1), (x+w-i-1, y+h-i-1), 1)
        pygame.draw.line(surf, (*sh[:3],), (x+i+1, y+h-i-1), (x+w-i-1, y+h-i-1), 1)

def draw_gloss_overlay(surf, rect, intensity=120):
    x, y, w, h = rect
    gloss = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h // 2):
        a = int(intensity * (1 - i / (h / 2)) * 0.5)
        pygame.draw.line(gloss, (255, 255, 255, max(0, a)), (0, i), (w, i))
    surf.blit(gloss, (x, y))

def draw_noise_texture(surf, rect, base_color, variance=15, density=0.4):
    x, y, w, h = rect
    for _ in range(int(w * h * density)):
        px = x + random.randint(0, w - 1)
        py = y + random.randint(0, h - 1)
        offset = random.randint(-variance, variance)
        nc = tuple(max(0, min(255, c + offset)) for c in base_color)
        surf.set_at((px, py), nc)

def draw_metallic_streak(surf, rect):
    x, y, w, h = rect
    for i in range(0, w + h, 3):
        dist = abs(i - (w + h) // 3)
        if dist < 12:
            a = int(100 * (1 - dist / 12))
            pygame.draw.line(surf, (255, 255, 255, max(0, a)), 
                           (x + min(i, w-1), y), (x + max(0, i - h), y + min(i, h-1)), 1)

# ═══════════════════════════════════════════════
#  MAP TILES - ULTRA PREMIUM
# ═══════════════════════════════════════════════

def make_brick_tile_ultra():
    s = pygame.Surface((TS, TS))
    s.fill((165, 80, 48))
    for y in range(0, TS, 8):
        offset = 8 if (y // 8) % 2 == 1 else 0
        pygame.draw.line(s, (90, 45, 28), (0, y), (TS, y), 1)
        for x in range(0, TS, 16):
            bx = (x + offset) % TS
            pygame.draw.line(s, (90, 45, 28), (bx, y), (bx, y + 8), 1)
            brick_c = (random.randint(160, 195), random.randint(70, 100), random.randint(40, 60))
            draw_bevel_rect(s, brick_c, (bx + 1, y + 1, 14, 6), 1)
            for _ in range(2):
                px, py = bx + random.randint(2, 12), y + random.randint(2, 5)
                if 0 <= px < TS and 0 <= py < TS:
                    s.set_at((px, py), (random.randint(130, 160), random.randint(60, 80), random.randint(35, 50)))
    return s

def make_steel_tile_ultra():
    s = pygame.Surface((TS, TS))
    s.fill((145, 150, 165))
    draw_bevel_rect(s, (165, 170, 190), (2, 2, TS - 4, TS - 4), 4)
    for i in range(2, TS - 2, 4):
        a = 30 + int(abs(math.sin(i * 0.3)) * 20)
        pygame.draw.line(s, (180, 185, 200), (i, 2), (i, TS - 3), 1)
    for dx, dy in [(6, 6), (TS - 7, 6), (6, TS - 7), (TS - 7, TS - 7)]:
        pygame.draw.circle(s, (110, 115, 125), (dx, dy), 3)
        pygame.draw.circle(s, (80, 85, 95), (dx, dy), 3, 1)
        pygame.draw.circle(s, (160, 165, 175), (dx - 1, dy - 1), 1)
    center = TS // 2
    pygame.draw.line(s, (120, 125, 140), (center - 4, center), (center + 4, center), 2)
    pygame.draw.line(s, (120, 125, 140), (center, center - 4), (center, center + 4), 2)
    draw_gloss_overlay(s, (2, 2, TS - 4, TS - 4), 60)
    return s

def make_grass_tile_ultra():
    s = pygame.Surface((TS, TS), pygame.SRCALPHA)
    for _ in range(40):
        gx = random.randint(0, TS - 1)
        gy = random.randint(0, TS - 1)
        height = random.randint(5, 12)
        sway = random.randint(-2, 2)
        gc = (random.randint(30, 70), random.randint(140, 210), random.randint(30, 70))
        width = random.randint(1, 2)
        pygame.draw.line(s, gc, (gx, gy), (gx + sway, gy - height), width)
    for _ in range(5):
        fx = random.randint(4, TS - 5)
        fy = random.randint(4, TS - 5)
        fc = random.choice([(255, 255, 100), (255, 200, 150), (200, 150, 255)])
        pygame.draw.circle(s, fc, (fx, fy), 2)
    return s

def make_crate_tile_ultra():
    s = pygame.Surface((TS, TS))
    s.fill((150, 110, 65))
    draw_bevel_rect(s, (170, 130, 80), (2, 2, TS - 4, TS - 4), 3)
    pygame.draw.rect(s, (90, 65, 40), (2, 2, TS - 4, TS - 4), 2)
    pygame.draw.line(s, (90, 65, 40), (2, 2), (TS - 3, TS - 3), 2)
    pygame.draw.line(s, (90, 65, 40), (TS - 3, 2), (2, TS - 3), 2)
    pygame.draw.circle(s, (100, 70, 40), (TS // 2, TS // 2), 4)
    pygame.draw.circle(s, (80, 55, 30), (TS // 2, TS // 2), 4, 1)
    draw_noise_texture(s, (3, 3, TS - 6, TS - 6), (160, 120, 75), 10, 0.15)
    return s

def make_water_tile_ultra(frame=0):
    s = pygame.Surface((TS, TS))
    base_b = 170 + int(math.sin(frame * 0.3) * 15)
    s.fill((35, 75, base_b))
    off = int(math.sin(frame * 0.25) * 5)
    off2 = int(math.cos(frame * 0.18) * 3)
    for y in range(0, TS, 3):
        wave_off = int(math.sin((y + frame * 2) * 0.15) * 3)
        c1 = (55 + wave_off * 2, 95 + wave_off * 3, min(255, 230 + wave_off * 2))
        pygame.draw.line(s, c1, (off + wave_off, y), (off + TS + wave_off, y), 1)
        c2 = (90, 140, 255)
        pygame.draw.line(s, c2, (off2, y + 1), (off2 + TS, y + 1), 1)
    for _ in range(3):
        sx = random.randint(4, TS - 8) + int(math.sin(frame * 0.1) * 2)
        sy = random.randint(4, TS - 8)
        pygame.draw.ellipse(s, (120, 180, 255, 80), (sx, sy, 6, 3))
    return s

def make_floor_tile_ultra(theme="default"):
    s = pygame.Surface((TS, TS))
    if theme == "desert":
        s.fill((180, 160, 120))
        for _ in range(8):
            px, py = random.randint(0, TS-1), random.randint(0, TS-1)
            c = (random.randint(170, 195), random.randint(150, 175), random.randint(110, 135))
            pygame.draw.circle(s, c, (px, py), random.randint(1, 2))
    elif theme == "snow":
        s.fill((220, 225, 235))
        for _ in range(6):
            px, py = random.randint(0, TS-1), random.randint(0, TS-1)
            c = (random.randint(210, 240), random.randint(215, 245), random.randint(225, 250))
            pygame.draw.circle(s, c, (px, py), random.randint(1, 3))
    elif theme == "city":
        s.fill((60, 62, 70))
        for y in range(0, TS, 16):
            for x in range(0, TS, 16):
                pygame.draw.rect(s, (55, 57, 64), (x, y, 15, 15))
                pygame.draw.line(s, (70, 72, 80), (x, y), (x + 15, y), 1)
                pygame.draw.line(s, (70, 72, 80), (x, y), (x, y + 15), 1)
    elif theme == "jungle":
        s.fill((35, 55, 30))
        for _ in range(12):
            px, py = random.randint(0, TS-1), random.randint(0, TS-1)
            c = (random.randint(25, 50), random.randint(45, 70), random.randint(20, 40))
            pygame.draw.circle(s, c, (px, py), random.randint(1, 2))
    elif theme == "lava":
        s.fill((40, 15, 10))
        for _ in range(5):
            px, py = random.randint(0, TS-1), random.randint(0, TS-1)
            c = (random.randint(60, 90), random.randint(15, 30), random.randint(5, 15))
            pygame.draw.circle(s, c, (px, py), random.randint(1, 3))
    else:
        s.fill((28, 30, 38))
        for _ in range(10):
            px, py = random.randint(0, TS-1), random.randint(0, TS-1)
            pygame.draw.circle(s, (38, 40, 48), (px, py), 1)
    return s

def make_base_tile_ultra():
    s = pygame.Surface((TS, TS), pygame.SRCALPHA)
    pygame.draw.circle(s, (240, 200, 60), (TS // 2, TS // 2), TS // 2 - 1)
    pygame.draw.circle(s, (200, 160, 40), (TS // 2, TS // 2), TS // 2 - 4)
    pygame.draw.circle(s, (255, 220, 80), (TS // 2, TS // 2), TS // 2 - 4, 2)
    pygame.draw.circle(s, (160, 120, 30), (TS // 2, TS // 2), TS // 2 - 1, 2)
    star_pts = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = 8 if i % 2 == 0 else 4
        star_pts.append((TS // 2 + math.cos(angle) * r, TS // 2 + math.sin(angle) * r))
    pygame.draw.polygon(s, (255, 240, 150), star_pts)
    draw_gloss_overlay(s, (4, 4, TS - 8, TS // 2 - 4), 80)
    return s

# ═══════════════════════════════════════════════
#  TANK SPRITES - ULTRA DETAILED
# ═══════════════════════════════════════════════

def make_tank_surface_from_colors(c, direction):
    s = pygame.Surface((TS, TS), pygame.SRCALPHA)

    # TRACKS with tread detail
    track_l = (2, 5, 6, 22)
    track_r = (24, 5, 6, 22)
    for tr in [track_l, track_r]:
        draw_bevel_rect(s, c["track_base"], tr, 2, 2)
        tx, ty, tw, th = tr
        for i in range(ty + 2, ty + th - 2, 3):
            pygame.draw.line(s, c["track_highlight"], (tx + 1, i), (tx + tw - 2, i), 1)
        for i in range(ty + 1, ty + th - 1, 6):
            pygame.draw.circle(s, c["track_rivet"], (tx + tw // 2, i), 1)

    # BODY with armor plates
    body_rect = (4, 6, 24, 20)
    draw_bevel_rect(s, c["body_base"], body_rect, 3, 3)

    # Armor panel lines
    pygame.draw.line(s, c["body_shadow"], (8, 8), (8, 24), 1)
    pygame.draw.line(s, c["body_shadow"], (24, 8), (24, 24), 1)
    pygame.draw.line(s, c["body_shadow"], (6, 14), (26, 14), 1)

    # Material effect
    if c["material"] == Material.METALLIC:
        draw_gloss_overlay(s, body_rect, 80)
    elif c["material"] == Material.CHROME:
        draw_gloss_overlay(s, body_rect, 120)
        draw_metallic_streak(s, body_rect)
    elif c["material"] == Material.RUSTY:
        draw_noise_texture(s, body_rect, c["body_base"], 20, 0.2)
    elif c["material"] == Material.NEON:
        glow_s = pygame.Surface((28, 24), pygame.SRCALPHA)
        pygame.draw.rect(glow_s, (*c["accent"][:3], 40), (0, 0, 28, 24), border_radius=4)
        s.blit(glow_s, (2, 4))

    # Stripe decoration on body
    stripe_c = c.get("stripe", c["accent"])
    pygame.draw.line(s, stripe_c, (10, 10), (22, 10), 2)

    # TURRET with detail
    tur_cx, tur_cy = TS // 2, TS // 2 + 1
    pygame.draw.circle(s, c["turret_base"], (tur_cx, tur_cy), 9)
    pygame.draw.circle(s, c["turret_highlight"], (tur_cx, tur_cy), 7)
    pygame.draw.circle(s, c["turret_base"], (tur_cx, tur_cy), 7, 1)
    pygame.draw.circle(s, c["body_specular"], (tur_cx - 2, tur_cy - 2), 2)

    # BARREL with muzzle detail
    barrel_w, barrel_h = 6, 16
    barrel = pygame.Surface((barrel_w, barrel_h), pygame.SRCALPHA)
    draw_bevel_rect(barrel, c["barrel_base"], (0, 0, barrel_w, barrel_h), 1, 1)
    pygame.draw.rect(barrel, c["barrel_highlight"], (1, 0, barrel_w - 2, 3), border_radius=1)
    pygame.draw.rect(barrel, c["body_shadow"], (1, barrel_h - 3, barrel_w - 2, 2))
    muzzle_c = (min(255, c["barrel_base"][0] + 30), min(255, c["barrel_base"][1] + 30), min(255, c["barrel_base"][2] + 30))
    pygame.draw.rect(barrel, muzzle_c, (0, 0, barrel_w, 2), border_radius=1)

    # Compose final with rotation
    final = pygame.Surface((TS, TS), pygame.SRCALPHA)
    if direction == 0:
        final.blit(s, (0, 0))
        final.blit(barrel, (TS // 2 - 3, -2))
    elif direction == 1:
        rs = pygame.transform.rotate(s, -90)
        rb = pygame.transform.rotate(barrel, -90)
        final.blit(rs, (0, 0))
        final.blit(rb, (TS - 14, TS // 2 - 3))
    elif direction == 2:
        rs = pygame.transform.rotate(s, 180)
        rb = pygame.transform.rotate(barrel, 180)
        final.blit(rs, (0, 0))
        final.blit(rb, (TS // 2 - 3, TS - 14))
    elif direction == 3:
        rs = pygame.transform.rotate(s, 90)
        rb = pygame.transform.rotate(barrel, 90)
        final.blit(rs, (0, 0))
        final.blit(rb, (-2, TS // 2 - 3))

    return final

def make_tank_surface_ultra(tank_key, direction):
    return make_tank_surface_from_colors(TANK_COLORS[tank_key], direction)

def make_player_tier_surface(tier, direction):
    tier = max(0, min(len(PLAYER_TIER_COLORS) - 1, tier))
    return make_tank_surface_from_colors(PLAYER_TIER_COLORS[tier], direction)

# ═══════════════════════════════════════════════
#  BULLETS - ENHANCED
# ═══════════════════════════════════════════════

def make_bullet(color=(255, 225, 80)):
    s = pygame.Surface((12, 12), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color[:3], 60), (6, 6), 5)
    pygame.draw.circle(s, (*color[:3], 180), (6, 6), 3)
    pygame.draw.circle(s, (255, 255, 255, 220), (5, 5), 1)
    return s

def make_bullet_advanced(kind="pierce"):
    s = pygame.Surface((16, 16), pygame.SRCALPHA)
    if kind == "pierce":
        pygame.draw.ellipse(s, (80, 200, 255, 60), (0, 2, 16, 12))
        pygame.draw.ellipse(s, (80, 200, 255, 200), (2, 4, 12, 8))
        pygame.draw.ellipse(s, (200, 240, 255), (4, 6, 8, 4))
    elif kind == "bomb":
        pygame.draw.circle(s, (60, 60, 60), (8, 8), 7)
        pygame.draw.circle(s, (255, 120, 50), (8, 8), 5)
        pygame.draw.circle(s, (255, 200, 100), (8, 8), 3)
        pygame.draw.circle(s, (40, 40, 40), (8, 8), 7, 1)
    elif kind == "laser":
        pygame.draw.rect(s, (0, 255, 180, 60), (2, 6, 12, 4))
        pygame.draw.rect(s, (0, 255, 180, 200), (4, 7, 8, 2))
        pygame.draw.rect(s, (200, 255, 240), (5, 7, 6, 1))
    elif kind == "plasma":
        pygame.draw.circle(s, (200, 50, 255, 60), (8, 8), 7)
        pygame.draw.circle(s, (200, 50, 255, 180), (8, 8), 5)
        pygame.draw.circle(s, (255, 200, 255), (8, 8), 2)
    return s

# ═══════════════════════════════════════════════
#  EXPLOSIONS - CINEMATIC
# ═══════════════════════════════════════════════

def make_explosion_ultra(num_frames=24):
    frames = []
    for i in range(num_frames):
        s = pygame.Surface((96, 96), pygame.SRCALPHA)
        t = i / num_frames

        # Outer fire ring
        r_out = int(8 + 40 * t)
        a_out = int(200 * (1 - t))
        fire_c = (255, max(0, int(200 - 200 * t)), max(0, int(50 - 50 * t)), max(0, a_out))
        pygame.draw.circle(s, fire_c, (48, 48), r_out)

        # Middle glow
        r_mid = int(6 + 30 * t)
        a_mid = int(255 * max(0, 1 - t * 1.3))
        glow_c = (255, max(0, int(255 - 200 * t)), max(0, int(100 - 100 * t)), max(0, a_mid))
        pygame.draw.circle(s, glow_c, (48, 48), r_mid)

        # Core bright
        if t < 0.5:
            r_core = int(4 + 15 * t)
            a_core = int(255 * (1 - t * 2))
            pygame.draw.circle(s, (255, 255, max(0, int(200 - 200 * t)), max(0, a_core)), (48, 48), r_core)

        # Sparks
        if t < 0.7:
            for j in range(6):
                angle = math.radians(j * 60 + i * 15)
                dist = 10 + 35 * t
                sx = 48 + math.cos(angle) * dist
                sy = 48 + math.sin(angle) * dist
                spark_a = int(200 * (1 - t / 0.7))
                pygame.draw.circle(s, (255, 200, 50, max(0, spark_a)), (int(sx), int(sy)), max(1, int(3 * (1 - t))))

        # Smoke ring
        if t > 0.3:
            smoke_t = (t - 0.3) / 0.7
            r_smoke = int(20 + 25 * smoke_t)
            a_smoke = int(80 * (1 - smoke_t))
            pygame.draw.circle(s, (100, 100, 100, max(0, a_smoke)), (48, 48), r_smoke, max(1, int(4 * (1 - smoke_t))))

        frames.append(s)
    return frames

def make_muzzle_flash_ultra():
    frames = []
    for i in range(8):
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        t = i / 8
        r = int(4 + 8 * (1 - t))
        a = int(255 * (1 - t))
        pygame.draw.circle(s, (255, 255, 200, max(0, a)), (12, 12), r)
        if t < 0.5:
            pygame.draw.circle(s, (255, 255, 255, max(0, int(200 * (1 - t * 2)))), (12, 12), max(1, r // 2))
        frames.append(s)
    return frames

def make_spawn_effect_ultra():
    frames = []
    for i in range(16):
        s = pygame.Surface((TS + 8, TS + 8), pygame.SRCALPHA)
        t = i / 16
        cx, cy = (TS + 8) // 2, (TS + 8) // 2

        # Expanding rings
        for ring in range(3):
            rt = max(0, t - ring * 0.1) / (1 - ring * 0.1)
            if rt > 0:
                r = int(4 + 20 * rt)
                a = int(180 * (1 - rt))
                pygame.draw.circle(s, (100, 200, 255, max(0, a)), (cx, cy), r, 2)

        # Center flash
        if t < 0.5:
            fa = int(255 * (1 - t * 2))
            pygame.draw.circle(s, (255, 255, 255, max(0, fa)), (cx, cy), max(1, int(6 * (1 - t * 2))))

        # Corner sparks
        for corner in range(4):
            angle = math.radians(corner * 90 + 45 + t * 180)
            dist = 5 + 15 * t
            sx = cx + math.cos(angle) * dist
            sy = cy + math.sin(angle) * dist
            sa = int(150 * (1 - t))
            pygame.draw.circle(s, (150, 220, 255, max(0, sa)), (int(sx), int(sy)), max(1, int(2 * (1 - t))))

        frames.append(s)
    return frames

# ═══════════════════════════════════════════════
#  ITEMS - PREMIUM QUALITY
# ═══════════════════════════════════════════════

def make_item_surface(kind):
    s = pygame.Surface((30, 30), pygame.SRCALPHA)

    colors = {
        "health": (240, 60, 60), "shield": (60, 120, 240),
        "speed": (60, 240, 120), "star": (255, 100, 50),
        "money": (255, 220, 50), "life": (255, 50, 150),
        "rapid": (255, 150, 40), "multi": (220, 200, 40),
        "pierce": (80, 200, 255), "bomb": (100, 100, 100),
        "laser": (0, 255, 180), "plasma": (200, 50, 255),
        "freeze": (120, 220, 255), "max_power": (255, 200, 60),
        "grenade": (90, 180, 90),
    }
    c = colors.get(kind, (200, 200, 200))
    gl = (min(255, c[0] + 60), min(255, c[1] + 60), min(255, c[2] + 60))

    # Outer glow
    glow = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*c, 30), (15, 15), 14)
    s.blit(glow, (0, 0))

    # Base plate
    pygame.draw.circle(s, (20, 20, 30), (15, 15), 13)
    pygame.draw.circle(s, (10, 10, 18), (15, 15), 11)
    pygame.draw.circle(s, c, (15, 15), 11, 2)

    # Icon
    if kind == "health":
        pygame.draw.rect(s, c, (11, 7, 8, 16), border_radius=2)
        pygame.draw.rect(s, c, (7, 11, 16, 8), border_radius=2)
        pygame.draw.rect(s, gl, (12, 8, 6, 14), border_radius=1)
        pygame.draw.rect(s, gl, (8, 12, 14, 6), border_radius=1)
    elif kind == "life":
        pygame.draw.ellipse(s, gl, (8, 8, 8, 10))
        pygame.draw.ellipse(s, gl, (14, 8, 8, 10))
        pygame.draw.polygon(s, gl, [(8, 14), (22, 14), (15, 22)])
    elif kind == "shield":
        pts = [(9, 8), (21, 8), (21, 15), (15, 22), (9, 15)]
        pygame.draw.polygon(s, c, pts)
        pygame.draw.polygon(s, gl, pts, 2)
        pygame.draw.line(s, gl, (15, 8), (15, 20), 2)
    elif kind == "speed":
        pts = [(16, 6), (10, 14), (15, 14), (14, 24), (21, 12), (16, 12)]
        pygame.draw.polygon(s, gl, pts)
    elif kind == "star":
        pygame.draw.circle(s, gl, (15, 15), 4)
        for angle in [0, 120, 240]:
            rad = math.radians(angle - 90)
            x = 15 + math.cos(rad) * 8
            y = 15 + math.sin(rad) * 8
            pygame.draw.circle(s, c, (int(x), int(y)), 4)
    elif kind == "money":
        pygame.draw.circle(s, (255, 200, 0), (15, 15), 8)
        pygame.draw.circle(s, (255, 255, 100), (15, 15), 8, 1)
        pygame.draw.line(s, (150, 100, 0), (15, 10), (15, 20), 2)
        pygame.draw.arc(s, (150, 100, 0), (12, 10, 6, 6), math.pi / 2, math.pi * 1.5, 2)
        pygame.draw.arc(s, (150, 100, 0), (12, 14, 6, 6), -math.pi / 2, math.pi / 2, 2)
    elif kind in ["rapid", "multi"]:
        if kind == "multi":
            pygame.draw.ellipse(s, gl, (13, 8, 4, 10))
            pygame.draw.ellipse(s, gl, (8, 10, 4, 10))
            pygame.draw.ellipse(s, gl, (18, 10, 4, 10))
        else:
            pygame.draw.rect(s, gl, (10, 8, 4, 12), border_radius=2)
            pygame.draw.rect(s, gl, (16, 8, 4, 12), border_radius=2)
    elif kind == "pierce":
        pts = [(15, 6), (9, 16), (12, 16), (12, 22), (18, 22), (18, 16), (21, 16)]
        pygame.draw.polygon(s, gl, pts)
    elif kind == "bomb":
        pygame.draw.circle(s, (60, 60, 60), (14, 16), 6)
        pygame.draw.circle(s, c, (14, 16), 4)
        pygame.draw.rect(s, gl, (12, 8, 4, 4))
    elif kind == "laser":
        pygame.draw.line(s, gl, (8, 15), (22, 15), 3)
        pygame.draw.circle(s, (255, 255, 255), (22, 15), 2)
    elif kind == "plasma":
        pygame.draw.circle(s, gl, (15, 15), 6)
        pygame.draw.circle(s, (255, 200, 255), (15, 15), 3)
    elif kind == "freeze":
        # Clock face
        pygame.draw.circle(s, (235, 245, 255), (15, 15), 8)
        pygame.draw.circle(s, (60, 80, 120), (15, 15), 8, 2)
        # Top button
        pygame.draw.rect(s, (60, 80, 120), (13, 4, 4, 3), border_radius=1)
        # Hour markers
        for ang in (0, 90, 180, 270):
            rad = math.radians(ang)
            x = 15 + math.cos(rad) * 6
            y = 15 + math.sin(rad) * 6
            pygame.draw.circle(s, (60, 80, 120), (int(x), int(y)), 1)
        # Hands
        pygame.draw.line(s, (40, 60, 100), (15, 15), (15, 10), 2)
        pygame.draw.line(s, (40, 60, 100), (15, 15), (19, 17), 2)
        # Frost glint
        pygame.draw.circle(s, (180, 230, 255), (12, 12), 2)
    elif kind == "max_power":
        # Pistol body
        pygame.draw.rect(s, (60, 60, 70), (6, 12, 14, 5))
        pygame.draw.rect(s, gl, (6, 12, 14, 5), 1)
        # Barrel
        pygame.draw.rect(s, (40, 40, 50), (16, 10, 8, 4))
        pygame.draw.rect(s, gl, (24, 11, 1, 2))
        # Grip
        pygame.draw.polygon(s, (90, 60, 40), [(8, 17), (14, 17), (12, 24), (10, 24)])
        pygame.draw.polygon(s, (140, 90, 50), [(8, 17), (14, 17), (12, 24), (10, 24)], 1)
        # Trigger guard
        pygame.draw.circle(s, (60, 60, 70), (13, 18), 2, 1)
    elif kind == "grenade":
        # Grenade body
        pygame.draw.rect(s, (60, 90, 50), (10, 12, 10, 12), border_radius=2)
        pygame.draw.rect(s, c, (10, 12, 10, 12), 1, border_radius=2)
        # Grid texture
        for gy in range(14, 23, 3):
            pygame.draw.line(s, (40, 60, 35), (11, gy), (19, gy), 1)
        for gx in range(12, 20, 3):
            pygame.draw.line(s, (40, 60, 35), (gx, 13), (gx, 23), 1)
        # Cap
        pygame.draw.rect(s, (180, 180, 60), (12, 9, 6, 3))
        # Pin
        pygame.draw.circle(s, (220, 220, 80), (19, 8), 2, 1)
        pygame.draw.line(s, (200, 200, 70), (18, 9), (15, 11), 1)
    else:
        pygame.draw.circle(s, c, (15, 15), 8)

    # Top gloss
    gloss = pygame.Surface((20, 10), pygame.SRCALPHA)
    pygame.draw.ellipse(gloss, (255, 255, 255, 40), (0, 0, 20, 10))
    s.blit(gloss, (5, 5))

    return s

# ═══════════════════════════════════════════════
#  MISC SPRITES
# ═══════════════════════════════════════════════

def make_score_popup_font():
    try:
        f = pygame.font.SysFont("consolas", 16, bold=True)
    except Exception:
        f = pygame.font.Font(None, 20)
    return {v: f.render(f"+{v}", True, (255, 255, 255)) for v in [50, 100, 150, 200, 500]}

def make_chicken_frames_ultra(num_frames=8):
    frames = []
    for i in range(num_frames):
        s = pygame.Surface((32, 32), pygame.SRCALPHA)
        bob = math.sin(i * 0.8) * 2
        pygame.draw.ellipse(s, (255, 230, 80), (6, int(12 + bob), 20, 16))
        pygame.draw.ellipse(s, (255, 240, 120), (8, int(14 + bob), 16, 12))
        pygame.draw.circle(s, (255, 240, 120), (22, int(10 + bob)), 7)
        pygame.draw.ellipse(s, (240, 60, 60), (20, int(3 + bob), 6, 6))
        pygame.draw.polygon(s, (255, 140, 40), [(28, int(10 + bob)), (32, int(12 + bob)), (28, int(14 + bob))])
        wing_w = 12 if i % 2 == 0 else 8
        pygame.draw.ellipse(s, (255, 255, 180), (8, int(14 + bob), wing_w, 8))
        pygame.draw.circle(s, (20, 20, 40), (24, int(9 + bob)), 2)
        pygame.draw.circle(s, (255, 255, 255), (24, int(8 + bob)), 1)
        frames.append(s)
    return frames

def make_dog_frames_ultra():
    frames = {}
    colors = {"body": (140, 100, 60), "belly": (200, 160, 120), "nose": (20, 20, 30)}
    for d in ["up", "down", "left", "right"]:
        df = []
        for i in range(4):
            s = pygame.Surface((36, 36), pygame.SRCALPHA)
            walk = math.sin(i * 1.5) * 3
            pygame.draw.ellipse(s, colors["body"], (8, 12, 20, 14))
            pygame.draw.ellipse(s, colors["belly"], (10, 14, 16, 10))
            tail_w = 6 if i % 2 == 0 else 2
            pygame.draw.line(s, colors["body"], (10, 18), (4, 18 + tail_w), 3)
            if d == "right":
                pygame.draw.circle(s, colors["body"], (26, 15), 10)
                pygame.draw.ellipse(s, (100, 70, 40), (22, 12, 6, 12))
                pygame.draw.circle(s, colors["nose"], (34, 16), 3)
                pygame.draw.circle(s, (40, 40, 50), (28, 13), 2)
            elif d == "left":
                pygame.draw.circle(s, colors["body"], (10, 15), 10)
                pygame.draw.ellipse(s, (100, 70, 40), (8, 12, 6, 12))
                pygame.draw.circle(s, colors["nose"], (2, 16), 3)
                pygame.draw.circle(s, (40, 40, 50), (8, 13), 2)
            elif d == "up":
                pygame.draw.circle(s, colors["body"], (18, 10), 10)
                pygame.draw.ellipse(s, (100, 70, 40), (8, 8, 6, 10))
                pygame.draw.ellipse(s, (100, 70, 40), (22, 8, 6, 10))
            else:
                pygame.draw.circle(s, colors["body"], (18, 20), 10)
                pygame.draw.ellipse(s, (100, 70, 40), (8, 15, 6, 12))
                pygame.draw.ellipse(s, (100, 70, 40), (22, 15, 6, 12))
                pygame.draw.circle(s, colors["nose"], (18, 26), 3)
                pygame.draw.circle(s, (40, 40, 50), (16, 18), 2)
                pygame.draw.circle(s, (40, 40, 50), (20, 18), 2)
            df.append(s)
        frames[d] = df
    return frames

# ═══════════════════════════════════════════════
#  WEATHER EFFECTS
# ═══════════════════════════════════════════════

def make_rain_drop():
    s = pygame.Surface((4, 12), pygame.SRCALPHA)
    pygame.draw.line(s, (150, 180, 255, 120), (2, 0), (1, 11), 1)
    return s

def make_snow_flake():
    s = pygame.Surface((6, 6), pygame.SRCALPHA)
    pygame.draw.circle(s, (230, 235, 255, 150), (3, 3), 2)
    return s

def make_sand_particle():
    s = pygame.Surface((4, 4), pygame.SRCALPHA)
    pygame.draw.circle(s, (200, 180, 140, 100), (2, 2), 2)
    return s

# ═══════════════════════════════════════════════
#  MINIMAP ICONS
# ═══════════════════════════════════════════════

def make_minimap_player_icon():
    s = pygame.Surface((6, 6), pygame.SRCALPHA)
    pygame.draw.rect(s, (80, 255, 120), (0, 0, 6, 6))
    pygame.draw.rect(s, (255, 255, 255), (1, 1, 4, 4))
    return s

def make_minimap_enemy_icon():
    s = pygame.Surface((4, 4), pygame.SRCALPHA)
    pygame.draw.rect(s, (255, 80, 80), (0, 0, 4, 4))
    return s

def make_minimap_base_icon():
    s = pygame.Surface((6, 6), pygame.SRCALPHA)
    pygame.draw.rect(s, (255, 220, 50), (0, 0, 6, 6))
    return s

# ═══════════════════════════════════════════════
#  UI ELEMENTS
# ═══════════════════════════════════════════════

def make_button_bg(w, h, color=(40, 60, 100), border_color=(80, 130, 200)):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, 220), (0, 0, w, h), border_radius=8)
    pygame.draw.rect(s, border_color, (0, 0, w, h), 2, border_radius=8)
    draw_gloss_overlay(s, (2, 2, w - 4, h // 2), 40)
    return s

def make_panel_bg(w, h, color=(20, 25, 40)):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, 230), (0, 0, w, h), border_radius=12)
    pygame.draw.rect(s, (60, 80, 130), (0, 0, w, h), 2, border_radius=12)
    return s

# ═══════════════════════════════════════════════
#  SPRITE CACHE
# ═══════════════════════════════════════════════

class SpriteCache:
    def __init__(self):
        print("Loading ULTRA PREMIUM sprites v3.0...")

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

        # Tanks (including boss)
        self.tanks = {k: [make_tank_surface_ultra(k, d) for d in range(4)] for k in TANK_COLORS}

        # Player tier sprites (5 tiers x 4 directions)
        self.player_tiers = [[make_player_tier_surface(t, d) for d in range(4)]
                             for t in range(len(PLAYER_TIER_COLORS))]

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
                     "rapid", "multi", "pierce", "bomb", "laser", "plasma",
                     "freeze", "max_power", "grenade"]
        self.items = {k: make_item_surface(k) for k in all_items}

        # Try to override a few items with pixel art sliced from the
        # reference asset image. Silently falls back to procedural icons.
        pixel_art = try_load_pixel_art_items()
        if pixel_art:
            print(f"Loaded {len(pixel_art)} pixel-art item(s) from asset image: "
                  f"{sorted(pixel_art.keys())}")
            self.items.update(pixel_art)

        # Score popups
        self.score_popups = make_score_popup_font()

        # Entities
        self.chicken_frames = make_chicken_frames_ultra()
        self.dog_frames = make_dog_frames_ultra()

        # Weather
        self.rain_drop = make_rain_drop()
        self.snow_flake = make_snow_flake()
        self.sand_particle = make_sand_particle()

        # Minimap icons
        self.minimap_player = make_minimap_player_icon()
        self.minimap_enemy = make_minimap_enemy_icon()
        self.minimap_base = make_minimap_base_icon()

        print("Sprites loaded successfully!")

    def set_floor_theme(self, theme):
        if theme in self.floors:
            self.floor = self.floors[theme]
