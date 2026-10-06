#!/usr/bin/env python3
"""Euclase Eddy — neon tide-hopper arcade for ElbowOS. Python 3 + pygame.

Hop a pale-blue crystal newt across drifting kelp rafts.
Coral eels sting. Bank the top shelf for a surge bonus.
A / D or arrows sidestep. W / Up / Space hop up. S / Down hop back.
"""
import math
import os
import random
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/EUCLASE_EDDY_ElbowOS.mp4")

NAVY = (6, 14, 28)
INK = (4, 10, 20)
TEAL = (12, 48, 78)
DEEP = (8, 32, 58)
ICE = (126, 224, 255)
MINT = (210, 255, 236)
CORAL = (255, 77, 109)
AMBER = (232, 160, 74)
GOLD = (255, 214, 92)
COPPER = (176, 96, 48)
WHITE = (240, 248, 255)
VIOLET = (168, 120, 255)

LANES = 7
TOP_Y = 300
LANE_H = 190
DOCK_Y = TOP_Y + LANES * LANE_H + 20


def wrap(x):
    return x % W


class Floater:
    def __init__(self, lane, y, speed, kind):
        self.lane = lane
        self.y = y
        self.w = random.randint(260, 440) if kind == "raft" else random.randint(150, 230)
        self.h = 72
        self.x = random.uniform(0, W)
        self.speed = speed
        self.kind = kind
        self.coin = kind == "raft" and random.random() < 0.4
        self.phase = random.random() * 6.28

    def step(self):
        self.x = wrap(self.x + self.speed)
        self.phase += 0.08

    def covers(self, px):
        px = wrap(px)
        rx = wrap(self.x)
        if rx + self.w <= W:
            return rx - 8 <= px <= rx + self.w + 8
        return px >= rx - 8 or px <= (rx + self.w) % W + 8


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            self.screen = pygame.Surface((W, H))
        pygame.display.set_caption("Euclase Eddy")
        self.font = pygame.font.Font(None, 92)
        self.mid = pygame.font.Font(None, 54)
        self.small = pygame.font.Font(None, 40)
        self.reset(full=True)

    def reset(self, full=False):
        if full:
            self.score = 0
            self.banks = 0
            self.speed_mul = 1.0
            self.t = 0
            self.splashes = []
            self.motes = [
                [random.uniform(0, W), random.uniform(200, H - 80), random.uniform(0.4, 1.6)]
                for _ in range(40)
            ]
        self.floaters = []
        for i in range(LANES):
            y = TOP_Y + i * LANE_H + 58
            direction = -1 if i % 2 == 0 else 1
            base = (2.4 + i * 0.35) * self.speed_mul * direction
            for k in range(3):
                kind = "eel" if (k == 2 and i % 2 == 1) else "raft"
                f = Floater(i, y, base * random.uniform(0.85, 1.15), kind)
                f.x = k * (W / 3) + random.uniform(-40, 40)
                self.floaters.append(f)
        self.lane = LANES  # dock
        self.x = W * 0.5
        self.hop = None
        self.riding = None
        self.alive_flash = 0
        self.combo = 0

    def lane_y(self, lane):
        if lane >= LANES:
            return DOCK_Y + 36
        if lane < 0:
            return 210
        return TOP_Y + lane * LANE_H + 90

    def safe(self, lane, x):
        if lane < 0 or lane >= LANES:
            return True
        for f in self.floaters:
            if f.lane == lane and f.kind == "raft" and f.covers(x):
                return True
        return False

    def threat(self, lane, x):
        if lane < 0 or lane >= LANES:
            return False
        for f in self.floaters:
            if f.lane == lane and f.kind == "eel" and f.covers(x):
                return True
        return False

    def hop_to(self, dlane, dx):
        if self.hop:
            return
        nl = max(-1, min(LANES, self.lane + dlane))
        nx = wrap(self.x + dx)
        self.hop = {
            "from": (self.x, self.lane_y(self.lane)),
            "to": (nx, self.lane_y(nl)),
            "lane": nl,
            "x": nx,
            "p": 0.0,
        }
        self.riding = None

    def land(self):
        self.lane = self.hop["lane"]
        self.x = self.hop["x"]
        self.hop = None
        if self.lane < 0:
            self.banks += 1
            self.score += 500 + self.combo * 40
            self.combo += 2
            self.speed_mul = min(2.2, self.speed_mul + 0.12)
            self.alive_flash = 12
            self.reset(full=False)
            self.lane = LANES
            self.x = random.uniform(180, W - 180)
            return
        if self.lane >= LANES:
            self.riding = None
            return
        hit = None
        for f in self.floaters:
            if f.lane == self.lane and f.covers(self.x):
                hit = f
                break
        if hit is None or hit.kind == "eel":
            self.splashes.append([self.x, self.lane_y(self.lane), 18])
            self.combo = 0
            self.lane = LANES
            self.x = W * 0.5
            self.score = max(0, self.score - 20)
            return
        self.riding = hit
        self.score += 100
        self.combo += 1
        if hit.coin:
            self.score += 50
            hit.coin = False

    def update(self, keys=None, auto=False):
        self.t += 1
        for f in self.floaters:
            f.step()
        for m in self.motes:
            m[1] -= m[2]
            if m[1] < 160:
                m[1] = H - 60
                m[0] = random.uniform(0, W)
        self.splashes = [[s[0], s[1], s[2] - 1] for s in self.splashes if s[2] > 1]
        if self.alive_flash:
            self.alive_flash -= 1
        if self.hop:
            self.hop["p"] += 0.14
            if self.hop["p"] >= 1:
                self.land()
            return
        if self.riding:
            self.x = wrap(self.x + self.riding.speed)
            if not self.riding.covers(self.x):
                self.splashes.append([self.x, self.lane_y(self.lane), 16])
                self.combo = 0
                self.riding = None
                self.lane = LANES
                self.x = W * 0.5
                return
        if auto:
            self.auto()
        elif keys:
            if keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]:
                self.hop_to(-1, 0)
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.hop_to(1, 0)
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.hop_to(0, -150)
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.hop_to(0, 150)

    def auto(self):
        if self.t % 4:
            return
        # Prefer an upward hop onto a raft (or the crystal bank).
        if self.lane > -1 and self.safe(self.lane - 1, self.x) and not self.threat(self.lane - 1, self.x):
            self.hop_to(-1, 0)
            return
        # Sidestep toward a gap that lines up with a raft above.
        for dx in (170, -170, 300, -300):
            nx = wrap(self.x + dx)
            if self.safe(self.lane, nx) or self.lane >= LANES:
                if self.lane > 0 and self.safe(self.lane - 1, nx):
                    self.hop_to(0, dx)
                    return
        if self.lane >= LANES and self.t % 8 == 0:
            self.hop_to(-1, random.choice([-80, 0, 80]))

    def px(self):
        if not self.hop:
            return self.x, self.lane_y(self.lane)
        p = self.hop["p"]
        a, b = self.hop["from"], self.hop["to"]
        arc = math.sin(p * math.pi) * 46
        return wrap(a[0] + (b[0] - a[0]) * p), a[1] + (b[1] - a[1]) * p - arc

    def draw_floater(self, surf, f):
        positions = [f.x]
        if f.x + f.w > W:
            positions.append(f.x - W)
        for x in positions:
            if f.kind == "raft":
                body = pygame.Rect(int(x), int(f.y - 18), f.w, f.h)
                pygame.draw.rect(surf, COPPER, body, border_radius=18)
                pygame.draw.rect(surf, AMBER, body.inflate(-10, -16), border_radius=12)
                for g in range(3):
                    pygame.draw.line(
                        surf, (140, 72, 32),
                        (body.left + 24, body.top + 18 + g * 16),
                        (body.right - 24, body.top + 18 + g * 16), 2,
                    )
                pygame.draw.circle(surf, ICE, (body.left + 28, body.centery), 10)
                pygame.draw.circle(surf, MINT, (body.right - 28, body.centery), 8)
                if f.coin:
                    pygame.draw.circle(surf, GOLD, (body.centerx, body.top - 8), 14)
                    pygame.draw.circle(surf, WHITE, (body.centerx - 4, body.top - 12), 4)
            else:
                cx = x + f.w * 0.5
                cy = f.y + math.sin(f.phase) * 8
                for i in range(6):
                    ox = -f.w * 0.4 + i * (f.w * 0.16)
                    oy = math.sin(f.phase + i * 0.7) * 14
                    rad = 18 - i
                    pygame.draw.circle(surf, CORAL, (int(cx + ox), int(cy + oy)), max(6, rad))
                pygame.draw.circle(surf, WHITE, (int(cx + f.w * 0.28), int(cy - 4)), 4)

    def draw(self, surf):
        surf.fill(NAVY)
        # eddy bands
        for i in range(LANES):
            y = TOP_Y + i * LANE_H
            col = TEAL if i % 2 == 0 else DEEP
            pygame.draw.rect(surf, col, (0, y, W, LANE_H))
            wave = int(math.sin(self.t * 0.05 + i) * 18)
            pygame.draw.line(surf, (40, 110, 150), (0, y + 24 + wave), (W, y + 40 - wave), 3)
        # crystal bank
        pygame.draw.rect(surf, (18, 42, 72), (0, 150, W, 150))
        for i in range(9):
            bx = 70 + i * 114
            hgt = 70 + (i * 37) % 50
            pts = [(bx, 290), (bx + 28, 290 - hgt), (bx + 56, 290)]
            pygame.draw.polygon(surf, ICE, pts)
            pygame.draw.polygon(surf, MINT, [(bx + 18, 290), (bx + 28, 290 - hgt + 16), (bx + 38, 290)])
        # dock
        pygame.draw.rect(surf, (28, 54, 78), (0, DOCK_Y - 10, W, H - DOCK_Y))
        pygame.draw.rect(surf, AMBER, (80, DOCK_Y + 10, W - 160, 28), border_radius=8)
        for m in self.motes:
            pygame.draw.circle(surf, (80, 160, 200), (int(m[0]), int(m[1])), 3)
        for f in self.floaters:
            self.draw_floater(surf, f)
        for s in self.splashes:
            pygame.draw.circle(surf, ICE, (int(s[0]), int(s[1])), s[2] + 6, 3)
            pygame.draw.circle(surf, WHITE, (int(s[0]) - 12, int(s[1]) - 8), 4)
        px, py = self.px()
        # newt
        squash = 1.15 if self.hop and self.hop["p"] < 0.3 else 1.0
        body = pygame.Rect(0, 0, int(64 * squash), int(48 / squash))
        body.center = (int(px), int(py))
        pygame.draw.ellipse(surf, ICE, body)
        pygame.draw.ellipse(surf, MINT, body.inflate(-22, -18))
        pygame.draw.circle(surf, INK, (body.centerx - 12, body.centery - 6), 5)
        pygame.draw.circle(surf, INK, (body.centerx + 12, body.centery - 6), 5)
        pygame.draw.circle(surf, WHITE, (body.centerx - 10, body.centery - 8), 2)
        tail = [(body.left + 4, body.centery), (body.left - 22, body.centery - 12), (body.left - 16, body.centery + 12)]
        pygame.draw.polygon(surf, (80, 190, 230), tail)
        # HUD
        title = self.font.render("EUCLASE EDDY", True, ICE)
        surf.blit(title, title.get_rect(center=(W // 2, 78)))
        sub = self.small.render("tide hopper", True, GOLD)
        surf.blit(sub, sub.get_rect(center=(W // 2, 128)))
        sc = self.mid.render(f"SCORE  {self.score}", True, WHITE)
        surf.blit(sc, sc.get_rect(center=(W // 2, H - 130)))
        tag = self.small.render("x.com/ElbowOS", True, MINT)
        surf.blit(tag, tag.get_rect(center=(W // 2, H - 72)))
        if self.alive_flash:
            pygame.draw.rect(surf, GOLD, (40, 160, W - 80, 8))

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            keys = pygame.key.get_pressed()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset(full=True)
            self.update(keys=keys, auto=False)
            self.draw(self.screen)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS),
            "-i", "-",
            "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "veryfast",
            "-movflags", "+faststart",
            OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        try:
            for _ in range(frames):
                self.update(auto=True)
                self.draw(self.screen)
                proc.stdin.write(pygame.image.tobytes(self.screen, "RGB"))
        finally:
            proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    random.seed(11)
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()


if __name__ == "__main__":
    main()
