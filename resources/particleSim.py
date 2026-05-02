import random
import pygame
import math
import tkinter as tk

class Particle:
    def __init__(self, x, y, velocityX, velocityY, accelerationX, accelerationY, colour, radius, mass=2):
        self.x = x
        self.y = y

        self.vx = velocityX
        self.vy = velocityY

        self.ax = accelerationX
        self.ay = accelerationY

        self.colour = colour
        self.radius = radius
        self.mass = mass
    
class Plane:
    def __init__(self, x=500, y=500, colour=(0,0,0)):
        self.x = x
        self.y = y
        self.colour = colour


particles = []
used_cords = set()

fps = None

noParticles = None

planeX = None
planeY = None

planeColour = tuple(random.randint(0, 255) for _ in range(3))

maxVelocity = 150
maxAcceleration = 10

def setup(entries):
    global fps, noParticles, planeX, planeY, plane
    try:
        fps = int(entries[0].get())
        noParticles = int(entries[1].get())
        planeX = int(entries[2].get())
        planeY = int(entries[3].get())

        plane = Plane(planeX, planeY)

        particles.clear()
        used_cords.clear()

        print("FPS:", fps)
        print("Particles:", noParticles)
        print("Plane:", planeX, planeY)

        genParticles(noParticles)
        animate(plane)

    except ValueError:
        print("Please enter valid numbers!")
        errorTK = tk.Tk()

        errorTK.geometry("200x100")
        errorTK.title("Arlo's 2D Particle Sim")
        errorTK.config(bg="black")

        message = tk.Label(errorTK, text="Invalid Inputs!  ⚠️", bg="Black", fg="White", font=(10)).pack()
        ok = tk.Button(errorTK, text="OK", bg="red", fg="white", command=lambda: errorTK.destroy()).pack()

        errorTK.mainloop()




def menu():
    labels = ["FPS", "Particles", "X", "Y"]
    entries = []

    root = tk.Tk()

    # Basic Config
    root.geometry("300x300")
    root.title("Arlo's 2D Particle Sim")
    root.config(bg="black")

    title = tk.Label(root, text="2D Particle Sim", fg="white", bg="black", font=("Small Fonts", 30))
    title.pack(fill="x")


    ######## ENTRIES ########
    # Frames
    frame = tk.Frame(root, bg="black")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    for row in range(4):
        # Left column = label names
        label = tk.Label(
            frame,
            text=labels[row],
            bg="black",
            fg="white",
            font=("Small Fonts", 15)
        )
        label.grid(row=row, column=0, padx=10, pady=8, sticky="w")

        # Right column = entry boxes
        entry = tk.Entry(
            frame,
            width=15,
            font=("Small Fonts", 15)
        )
        entry.grid(row=row, column=1, padx=10, pady=8)

        entries.append(entry)
        #####################
    
    start_animation = tk.Button(root, bg="red", fg="white", text="Start Animation", command=lambda: setup(entries))
    start_animation.pack(fill="x")

    root.mainloop()


def genParticles(no_particles):
    while len(particles) < no_particles:
        x = random.randrange(0, plane.x)
        y = random.randrange(0, plane.y)
        cords = (x,y)

        if cords in used_cords:
            continue

        used_cords.add(cords)

        # velocities
        vx = random.randrange(-maxVelocity, maxVelocity)
        vy = random.randrange(-maxVelocity, maxVelocity)

        # acceleration
        ax = random.randrange(1, maxAcceleration)
        ay = random.randrange(1, maxAcceleration)

        # colour
        colour = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

        # create
        particle = Particle(x, y, vx, vy, ax, ay, colour, 10)
        particles.append(particle)

def resolve_particle_collision(part1, part2):
    dx = part1.x - part2.x
    dy = part1.y - part2.y
    distance = math.sqrt(dx**2 + dy**2)

    if distance == 0:
        return

    if distance < (part1.radius + part2.radius):

        overlap = (part1.radius + part2.radius) - distance

        # push particles away from eachother
        nx = dx / distance
        ny = dy / distance

        part1.x += nx * overlap / 2
        part1.y += ny * overlap / 2
        part2.x -= nx * overlap / 2  # Move part2 away from part1
        part2.y -= ny * overlap / 2

        # Particle 1
        vx1 = ((part1.mass - part2.mass) * part1.vx + (2*part2.mass*part2.vx)) / (part1.mass + part2.mass)
        vy1 = ((part1.mass - part2.mass) * part1.vy + (2*part2.mass*part2.vy)) / (part1.mass + part2.mass)

        # Particle 2
        vx2 = ((2*part1.mass*part1.vx) + (part2.mass - part1.mass) * part2.vx) / (part1.mass + part2.mass)
        vy2 = ((2*part1.mass*part1.vy) + (part2.mass - part1.mass) * part2.vy) / (part1.mass + part2.mass)

        part1.vx = vx1
        part1.vy = vy1
        part2.vx = vx2
        part2.vy = vy2


def simulate():
    t = 1/fps
    epsilon = 1e-6

    for part1 in particles:
        part1.x = part1.x + (part1.vx * t)
        part1.y = part1.y + (part1.vy * t)

        part1.vx = part1.vx + (part1.ax*t)
        part1.vy = part1.vy + (part1.ay*t)

        # boarder collision
        if part1.x - part1.radius <= 0 or part1.x + part1.radius >= plane.x:
            part1.vx = -part1.vx

        if part1.y - part1.radius <= 0 or part1.y + part1.radius >= plane.y:
            part1.vy = -part1.vy
        
        # Particle collision
        for part2 in particles:
            if part1 != part2:
                distance = math.sqrt((part1.x - part2.x)**2 + (part1.y - part2.y)**2)   # between centers

                if distance <= (part1.radius + part2.radius) + epsilon:
                    resolve_particle_collision(part1, part2)


def animate(plane):
    pygame.init()
    window = pygame.display.set_mode((planeX, planeY))
    pygame.display.set_caption("Particle Animation")

    clock = pygame.time.Clock()


    run = True

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        simulate()

        window.fill(plane.colour)

        for part in particles:
            pygame.draw.circle(window, part.colour, (part.x, part.y), part.radius)

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()


menu()