import tkinter as tk
from tkinter import colorchooser, messagebox
import json
from pathlib import Path
import sys, random, math, threading
import pygame

# ── Palette ────────────────────────────────────────────────────────────────────
BG       = "#0d0d0f"
PANEL    = "#13131a"
BORDER   = "#1e1e2e"
ACCENT   = "#7c6af7"
ACCENT2  = "#a78bfa"
TEXT     = "#e2e2f0"
MUTED    = "#5a5a7a"
DANGER   = "#f87171"
ENTRY_BG = "#0a0a12"

FONT_HEAD  = ("Courier New", 11, "bold")
FONT_LABEL = ("Courier New", 9)
FONT_MONO  = ("Courier New", 10)

# ── Simulation classes ─────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, velocityX, velocityY, accelerationX, accelerationY, colour, radius, mass=2):
        self.x, self.y = x, y
        self.vx, self.vy = velocityX, velocityY
        self.ax, self.ay = accelerationX, accelerationY
        self.colour = colour
        self.radius = radius
        self.mass = mass

class Plane:
    def __init__(self, x=500, y=500, colour=(0, 0, 0)):
        self.x, self.y, self.colour = x, y, colour

def hex_to_rgb(hex_colour):
    h = hex_colour.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# ── Simulation logic ───────────────────────────────────────────────────────────

def run_simulation(cfg):
    # Screen dimensions via tkinter (already destroyed by now, use pygame fullscreen info)
    pygame.init()
    info = pygame.display.Info()
    width, height = info.current_w, info.current_h
    pygame.quit()

    fps           = int(cfg["fps"])
    noParticles   = int(cfg["num_particles"])
    maxVelocity   = int(cfg["max_velocity"])
    maxAccel      = int(maxVelocity / 5)
    planeColours  = [hex_to_rgb(c) for c in cfg["particle_colours"]]
    bgColour      = hex_to_rgb(cfg["background_colour"])

    plane     = Plane(width, height, bgColour)
    particles = []
    used_cords = set()

    def genParticles(no_particles):
        radius = 10
        while len(particles) < no_particles:
            x = random.randrange(0, plane.x)
            if x <=0:
                x = x+radius
            if x >=plane.x:
                x = x-radius

            y = random.randrange(0, plane.y)
            if y <=0:
                y = y+radius
            if y >=plane.y:
                y = y-radius

            if (x, y) in used_cords:
                continue
            used_cords.add((x, y))
            vx = random.randrange(-maxVelocity, maxVelocity)
            vy = random.randrange(-maxVelocity, maxVelocity)
            ax = random.randrange(1, max(2, maxAccel))
            ay = random.randrange(1, max(2, maxAccel))
            colour = random.choice(planeColours)
            particles.append(Particle(x, y, vx, vy, ax, ay, colour, radius))

    def resolve_particle_collision(p1, p2):
        dx = p1.x - p2.x
        dy = p1.y - p2.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0:
            return
        if dist < (p1.radius + p2.radius):
            overlap = (p1.radius + p2.radius) - dist
            nx, ny = dx / dist, dy / dist
            p1.x += nx * overlap / 2;  p1.y += ny * overlap / 2
            p2.x -= nx * overlap / 2;  p2.y -= ny * overlap / 2
            vx1 = ((p1.mass - p2.mass)*p1.vx + 2*p2.mass*p2.vx) / (p1.mass + p2.mass)
            vy1 = ((p1.mass - p2.mass)*p1.vy + 2*p2.mass*p2.vy) / (p1.mass + p2.mass)
            vx2 = (2*p1.mass*p1.vx + (p2.mass - p1.mass)*p2.vx) / (p1.mass + p2.mass)
            vy2 = (2*p1.mass*p1.vy + (p2.mass - p1.mass)*p2.vy) / (p1.mass + p2.mass)
            p1.vx, p1.vy = vx1, vy1
            p2.vx, p2.vy = vx2, vy2

    def simulate():
        t = 1 / fps
        epsilon = 1e-6
        for p1 in particles:
            p1.x += p1.vx * t;  p1.y += p1.vy * t
            p1.vx += p1.ax * t; p1.vy += p1.ay * t
            if p1.x - p1.radius <= 0 or p1.x + p1.radius >= plane.x:
                p1.vx = -p1.vx
            if p1.y - p1.radius <= 0 or p1.y + p1.radius >= plane.y:
                p1.vy = -p1.vy
            for p2 in particles:
                if p1 is not p2:
                    dist = math.sqrt((p1.x-p2.x)**2 + (p1.y-p2.y)**2)
                    if dist <= (p1.radius + p2.radius) + epsilon:
                        resolve_particle_collision(p1, p2)

    genParticles(noParticles)


    # UI

    pygame.init()
    window = pygame.display.set_mode((plane.x, plane.y))
    pygame.display.set_caption("Fluxium")
    clock = pygame.time.Clock()

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        simulate()
        window.fill(plane.colour)
        for p in particles:
            pygame.draw.circle(window, p.colour, (int(p.x), int(p.y)), p.radius)
        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()

# ── UI widgets ─────────────────────────────────────────────────────────────────

class ColorSwatch(tk.Frame):
    def __init__(self, parent, color: str, on_remove, **kwargs):
        super().__init__(parent, bg=PANEL, **kwargs)
        self.color = color
        self.on_remove = on_remove
        tk.Label(self, bg=color, width=3, height=1, relief="flat", cursor="hand2").pack(side="left", padx=(0, 2))
        tk.Label(self, text=color, bg=PANEL, fg=TEXT, font=FONT_LABEL, cursor="hand2").pack(side="left")
        btn = tk.Label(self, text="✕", bg=PANEL, fg=DANGER, font=FONT_LABEL, cursor="hand2")
        btn.pack(side="left", padx=(4, 0))
        btn.bind("<Button-1>", lambda _: self.on_remove(self))

class SectionLabel(tk.Frame):
    def __init__(self, parent, text, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        tk.Label(self, text=text, bg=BG, fg=ACCENT2, font=FONT_HEAD).pack(side="left", padx=(0, 8))
        tk.Frame(self, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, pady=6)

class StyledEntry(tk.Frame):
    def __init__(self, parent, width=18, default="", **kwargs):
        super().__init__(parent, bg=BORDER, bd=0, **kwargs)
        inner = tk.Frame(self, bg=ENTRY_BG, padx=1, pady=1)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        self.var = tk.StringVar(value=default)
        self.entry = tk.Entry(inner, textvariable=self.var, bg=ENTRY_BG, fg=TEXT,
                              insertbackground=ACCENT2, relief="flat", font=FONT_MONO, width=width, bd=4)
        self.entry.pack(fill="both", expand=True)
        self.entry.bind("<FocusIn>",  lambda _: self.configure(bg=ACCENT))
        self.entry.bind("<FocusOut>", lambda _: self.configure(bg=BORDER))

    def get(self): return self.var.get()
    def set(self, val): self.var.set(val)

# ── Main UI ────────────────────────────────────────────────────────────────────

class FluxiumUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FLUXIUM")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._particle_colors: list[ColorSwatch] = []
        self._bg_color = "#000000"
        self._build()
        self._center_window()

    def _build(self):
        hdr = tk.Frame(self, bg=BG, pady=24)
        hdr.pack(fill="x", padx=32)
        tk.Label(hdr, text="FLUXIUM", bg=BG, fg=TEXT, font=("Courier New", 28, "bold")).pack(side="left")
        tk.Label(hdr, text="  // particle engine", bg=BG, fg=MUTED, font=FONT_HEAD).pack(side="left", pady=6)

        body = tk.Frame(self, bg=BG, padx=32)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        SectionLabel(left, "SIMULATION").pack(fill="x", pady=(0, 10))
        self._sim_fields(left)
        SectionLabel(left, "PARTICLE COLOURS").pack(fill="x", pady=(20, 10))
        self._colour_panel(left)

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        SectionLabel(right, "ENVIRONMENT").pack(fill="x", pady=(0, 10))
        self._env_fields(right)
        SectionLabel(right, "PREVIEW").pack(fill="x", pady=(20, 10))
        self._preview_panel(right)

        footer = tk.Frame(self, bg=BG, pady=24, padx=32)
        footer.pack(fill="x")
        self._action_row(footer)

    def _sim_fields(self, parent):
        grid = tk.Frame(parent, bg=BG)
        grid.pack(fill="x")
        fields = [("FPS", "fps", "60"), ("PARTICLES", "num_particles", "50"), ("MAX VELOCITY", "max_vel", "200")]
        self._entries: dict[str, StyledEntry] = {}
        for i, (label, key, default) in enumerate(fields):
            tk.Label(grid, text=label, bg=BG, fg=MUTED, font=FONT_LABEL, anchor="w", width=14).grid(row=i, column=0, pady=5, sticky="w")
            e = StyledEntry(grid, default=default, width=16)
            e.grid(row=i, column=1, pady=5, sticky="w")
            self._entries[key] = e

    def _colour_panel(self, parent):
        self._colour_list = tk.Frame(parent, bg=BG)
        self._colour_list.pack(fill="x")
        tk.Button(parent, text="+ ADD COLOUR", bg=PANEL, fg=ACCENT2, font=FONT_LABEL,
                  activebackground=BORDER, activeforeground=ACCENT, relief="flat", bd=0,
                  pady=6, padx=12, cursor="hand2", command=self._pick_particle_color).pack(anchor="w", pady=(8, 0))
        for c in ("#7c6af7", "#4ade80", "#f87171"):
            self._add_color_swatch(c)

    def _env_fields(self, parent):
        grid = tk.Frame(parent, bg=BG)
        grid.pack(fill="x")
        tk.Label(grid, text="BG COLOUR", bg=BG, fg=MUTED, font=FONT_LABEL, anchor="w", width=14).grid(row=0, column=0, pady=5, sticky="w")
        self._bg_swatch_frame = tk.Frame(grid, bg=BORDER, width=100, height=28, cursor="hand2")
        self._bg_swatch_frame.grid(row=0, column=1, pady=5, sticky="w")
        self._bg_swatch_frame.pack_propagate(False)
        self._bg_swatch = tk.Label(self._bg_swatch_frame, bg=self._bg_color, text="", width=12, cursor="hand2")
        self._bg_swatch.pack(fill="both", expand=True, padx=1, pady=1)
        self._bg_swatch.bind("<Button-1>", lambda _: self._pick_bg_color())
        self._bg_swatch_frame.bind("<Button-1>", lambda _: self._pick_bg_color())
        self._bg_hex_lbl = tk.Label(grid, text=self._bg_color, bg=BG, fg=TEXT, font=FONT_MONO)
        self._bg_hex_lbl.grid(row=0, column=2, padx=8, sticky="w")

    def _preview_panel(self, parent):
        self._canvas = tk.Canvas(parent, width=220, height=150, bg=self._bg_color,
                                 highlightthickness=1, highlightbackground=BORDER)
        self._canvas.pack(anchor="w")
        self._refresh_preview()

    def _action_row(self, parent):
        btn_cfg = dict(font=FONT_HEAD, relief="flat", bd=0, pady=10, padx=22, cursor="hand2")
        tk.Button(parent, text="RESET", bg=PANEL, fg=MUTED, activebackground=BORDER,
                  activeforeground=TEXT, command=self._reset, **btn_cfg).pack(side="left")
        tk.Button(parent, text="EXPORT CONFIG", bg=PANEL, fg=TEXT, activebackground=BORDER,
                  activeforeground=ACCENT2, command=self._export, **btn_cfg).pack(side="left", padx=8)
        tk.Button(parent, text="▶  LAUNCH SIMULATION", bg=ACCENT, fg="#ffffff",
                  activebackground=ACCENT2, activeforeground="#ffffff",
                  command=self._launch, **btn_cfg).pack(side="right")

    def _pick_particle_color(self):
        color = colorchooser.askcolor(title="Pick Particle Colour", parent=self)[1]
        if color:
            self._add_color_swatch(color)
            self._refresh_preview()

    def _add_color_swatch(self, color):
        swatch = ColorSwatch(self._colour_list, color, on_remove=self._remove_color_swatch)
        swatch.pack(anchor="w", pady=2)
        self._particle_colors.append(swatch)

    def _remove_color_swatch(self, swatch):
        self._particle_colors.remove(swatch)
        swatch.destroy()
        self._refresh_preview()

    def _pick_bg_color(self):
        color = colorchooser.askcolor(color=self._bg_color, title="Pick Background Colour", parent=self)[1]
        if color:
            self._bg_color = color
            self._bg_swatch.configure(bg=color)
            self._bg_hex_lbl.configure(text=color)
            self._canvas.configure(bg=color)
            self._refresh_preview()

    def _refresh_preview(self):
        self._canvas.delete("all")
        colors = [s.color for s in self._particle_colors] or [MUTED]
        for _ in range(80):
            x, y, r = random.randint(4, 216), random.randint(4, 146), random.randint(2, 5)
            self._canvas.create_oval(x-r, y-r, x+r, y+r, fill=random.choice(colors), outline="")

    def _get_config(self):
        try:
            fps  = int(self._entries["fps"].get())
            npar = int(self._entries["num_particles"].get())
            mvel = float(self._entries["max_vel"].get())
            assert fps > 0 and npar > 0 and mvel > 0
        except (ValueError, AssertionError):
            messagebox.showerror("Invalid Input", "FPS and Particles must be positive integers.\nMax Velocity must be a positive number.", parent=self)
            return None
        return {
            "fps": fps,
            "num_particles": npar,
            "max_velocity": mvel,
            "particle_colours": [s.color for s in self._particle_colors],
            "background_colour": self._bg_color,
        }

    def _launch(self):
        cfg = self._get_config()
        if cfg is None:
            return
        # Run simulation in a background thread so the UI stays open
        t = threading.Thread(target=run_simulation, args=(cfg,), daemon=True)
        t.start()

    def _export(self):
        cfg = self._get_config()
        if cfg is None:
            return
        path = Path(__file__).parent / "fluxium_config.json"
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2)
        messagebox.showinfo("Config Exported", f"Saved to {path}", parent=self)

    def _reset(self):
        self._entries["fps"].set("60")
        self._entries["num_particles"].set("50")
        self._entries["max_vel"].set("200")
        for s in list(self._particle_colors):
            s.destroy()
        self._particle_colors.clear()
        for c in ("#7c6af7", "#4ade80", "#f87171"):
            self._add_color_swatch(c)
        self._bg_color = "#000000"
        self._bg_swatch.configure(bg=self._bg_color)
        self._bg_hex_lbl.configure(text=self._bg_color)
        self._canvas.configure(bg=self._bg_color)
        self._refresh_preview()

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    app = FluxiumUI()
    app.mainloop()
