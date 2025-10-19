import pygame
import math
import time
import random

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Creepy-Crawler Cursor Tracker")

# Colors
BG = (15, 15, 20)
BUG_MAIN = (225, 140, 35)       # main body color
BUG_DARK = (150, 90, 20)        # darker shade for segments/shadow
EYE_COLOR = (255, 255, 255)
PUPIL_COLOR = (20, 20, 20)
SHADOW_COLOR = (10, 10, 10, 120)  # RGBA shadow, drawn with a surface

# Bug properties
bug_pos = [400.0, 300.0]
bug_speed = 3.5
segment_spacing = 14
segment_sizes = [(18, 16), (26, 20), (34, 26)]  # head, thorax, abdomen radii
leg_count_per_side = 3

clock = pygame.time.Clock()
running = True
start_time = time.time()

# Helper: draw an anti-aliased filled ellipse on a temporary surface (for shadows)
def draw_ellipse_alpha(surface, color, rect):
    tmp = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.ellipse(tmp, color, (0, 0, rect[2], rect[3]))
    surface.blit(tmp, (rect[0], rect[1]))


def draw_bug(surface, pos, heading, t, moving):
    """
    Draw a multi-segment crawling bug with legs and antennae.
    pos: (x, y) center of thorax
    heading: normalized vector pointing toward movement direction (hx, hy)
    t: time in seconds (for animation)
    moving: 0..1 movement intensity
    """
    x, y = pos
    hx, hy = heading
    if hx == 0 and hy == 0:
        hx, hy = 1.0, 0.0
    # perpendicular vector for lateral offsets
    px, py = -hy, hx

    # slight vertical bob when moving
    bob = math.sin(t * 6.0) * 2.0 * moving

    # shadow
    shadow_w = 60
    shadow_h = 26
    draw_ellipse_alpha(surface, SHADOW_COLOR, (x - shadow_w // 2, y + 18, shadow_w, shadow_h))

    # segment centers along heading: head -> thorax(center) -> abdomen
    thorax = (x, y + bob)
    head = (x + hx * segment_spacing * 0.9, y + hy * segment_spacing * 0.9 + bob)
    abdomen = (x - hx * segment_spacing * 1.2, y - hy * segment_spacing * 1.2 + bob)

    # draw abdomen (largest, darker)
    ab_w, ab_h = segment_sizes[2]
    pygame.draw.ellipse(surface, BUG_DARK, (abdomen[0] - ab_w//2, abdomen[1] - ab_h//2, ab_w, ab_h))
    # draw thorax (center)
    th_w, th_h = segment_sizes[1]
    pygame.draw.ellipse(surface, BUG_MAIN, (thorax[0] - th_w//2, thorax[1] - th_h//2, th_w, th_h))
    # draw head
    hd_w, hd_h = segment_sizes[0]
    pygame.draw.ellipse(surface, BUG_MAIN, (head[0] - hd_w//2, head[1] - hd_h//2, hd_w, hd_h))
    # add highlight on head
    pygame.draw.ellipse(surface, (255, 200, 120), (head[0] - hd_w//4, head[1] - hd_h//3, hd_w//3, hd_h//3))

    # eyes on head (offset slightly toward heading)
    eye_offset = 6
    ex = head[0] + hx * 4
    ey = head[1] + hy * 4
    left_eye = (ex + px * 5 - hx * 2, ey + py * 5 - hy * 2)
    right_eye = (ex - px * 5 - hx * 2, ey - py * 5 - hy * 2)
    pygame.draw.circle(surface, EYE_COLOR, (int(left_eye[0]), int(left_eye[1])), 4)
    pygame.draw.circle(surface, EYE_COLOR, (int(right_eye[0]), int(right_eye[1])), 4)
    pygame.draw.circle(surface, PUPIL_COLOR, (int(left_eye[0] + hx * 1), int(left_eye[1] + hy * 1)), 2)
    pygame.draw.circle(surface, PUPIL_COLOR, (int(right_eye[0] + hx * 1), int(right_eye[1] + hy * 1)), 2)

    # antennae - two curved lines with little tip jitter
    ant_len = 26 + moving * 10
    for side in (-1, 1):
        ax0 = head[0] + px * (side * 4) - hx * 4
        ay0 = head[1] + py * (side * 4) - hy * 4
        # control points for a simple quadratic curve simulated with line segments
        ant_mid_x = ax0 + hx * (ant_len * 0.5) + px * (side * 6)
        ant_mid_y = ay0 + hy * (ant_len * 0.5) + py * (side * 6) - math.sin(t * 8 + side) * 3 * moving
        ant_tip_x = ax0 + hx * ant_len + px * (side * 10) - hy * math.sin(t * 10) * 2 * side * moving
        ant_tip_y = ay0 + hy * ant_len + py * (side * 10) + hx * math.cos(t * 10) * 2 * side * moving
        pygame.draw.aaline(surface, BUG_DARK, (ax0, ay0), (ant_mid_x, ant_mid_y))
        pygame.draw.aaline(surface, BUG_DARK, (ant_mid_x, ant_mid_y), (ant_tip_x, ant_tip_y))
        pygame.draw.circle(surface, BUG_DARK, (int(ant_tip_x), int(ant_tip_y)), 2)

    # legs - alternate lifting using sine wave
    leg_base_positions = [
        # relative positions from thorax/abdomen for 3 legs per side (closer to head = front)
        (thorax, -6),  # front on thorax
        (thorax, 0),   # middle on thorax
        (abdomen, 6)   # rear on abdomen
    ]
    leg_reach = 22
    for i, (base_seg, longitudinal_offset) in enumerate(leg_base_positions):
        bx, by = base_seg
        # use direction factor: front legs point forward (dir=1),
        # middle and rear legs point backward (dir=-1) to look more spider-like
        dir_factor = -1 if i >= 1 else 1
        for side_idx, side in enumerate((-1, 1)):
            # phase offset creates alternating gait
            phase = i * 1.2 + side_idx * math.pi
            lift = math.sin(t * 12 + phase) * 1.0 * moving
            # leg root point (still offset laterally from the segment)
            root_x = bx + px * (side * (8 + i * 3)) + hx * (longitudinal_offset)
            root_y = by + py * (side * (8 + i * 3)) + hy * (longitudinal_offset)
            # mid joint (lifted when moving) - direction-aware so rear legs bend backwards
            mid_x = root_x + hx * (leg_reach * 0.4 * dir_factor) + px * (side * 6) - hy * lift * 8 * dir_factor
            mid_y = root_y + hy * (leg_reach * 0.4 * dir_factor) + py * (side * 6) + hx * lift * 8 * dir_factor
            # foot: extend in direction of leg (forward for front legs, backward for rear legs)
            foot_x = root_x + hx * leg_reach * dir_factor + px * (side * (leg_reach * 0.6))
            foot_y = root_y + hy * leg_reach * dir_factor + py * (side * (leg_reach * 0.6))
            # add a small lift to the foot when leg is in lifting phase (respect dir)
            foot_x += -hy * lift * 6 * dir_factor
            foot_y += hx * lift * 6 * dir_factor

            # draw segments: upper leg (root->mid) and lower leg (mid->foot)
            pygame.draw.aaline(surface, BUG_DARK, (root_x, root_y), (mid_x, mid_y))
            pygame.draw.aaline(surface, BUG_DARK, (mid_x, mid_y), (foot_x, foot_y))
            # little foot dot
            pygame.draw.circle(surface, BUG_DARK, (int(foot_x), int(foot_y)), 2)


def normalized(vx, vy):
    mag = math.hypot(vx, vy)
    if mag == 0:
        return 0.0, 0.0
    return vx / mag, vy / mag


# Main loop
while running:
    screen.fill(BG)

    # Get mouse position
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # Calculate direction vector from bug to mouse
    dx = mouse_x - bug_pos[0]
    dy = mouse_y - bug_pos[1]
    distance = math.hypot(dx, dy)

    # movement intensity 0..1
    move_intensity = min(distance / 120.0, 1.0)

    # avoid jitter when very close: small random twitch if not moving
    if distance > 5:
        hx, hy = normalized(dx, dy)
        bug_pos[0] += hx * bug_speed * (0.6 + 0.8 * move_intensity)
        bug_pos[1] += hy * bug_speed * (0.6 + 0.8 * move_intensity)
    else:
        # subtle idle twitch
        bug_pos[0] += (random.random() - 0.5) * 0.6
        bug_pos[1] += (random.random() - 0.5) * 0.6
        hx, hy = 1.0, 0.0

    # animation time
    t = time.time() - start_time

    # draw the bug centered on thorax position
    draw_bug(screen, (bug_pos[0], bug_pos[1]), (hx, hy), t, move_intensity)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
