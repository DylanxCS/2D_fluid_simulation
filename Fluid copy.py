import numpy as np
import math
import pygame


# Initialize variables
dt = 0.05
diffusion = 0.01
viscosity = 0.01
# Initialize arrays
N = 64
SCALE = 10
X = np.zeros((N,N), dtype=float)
Y = np.zeros((N,N), dtype=float)
X0 = np.zeros((N,N), dtype=float)
Y0 = np.zeros((N,N), dtype=float)
Vx = np.zeros((N,N), dtype=float)
Vy = np.zeros((N,N), dtype=float)
Vx0 = np.zeros((N,N), dtype=float)
Vy0 = np.zeros((N,N), dtype=float)
density = np.zeros((N,N), dtype=float)
#density0 = np.zeros((N,N), dtype=float)
s = np.zeros((N,N), dtype=float)
diff = np.zeros((N,N), dtype=float)


def Add_Density(x, y, amount):
    x = min(max(x,0),N-1)
    y = min(max(y,0),N-1)
    #print("Mouse Position:", x, y)
    density[x,y] += amount


def Add_Velocity(x, y, amount_x, amount_y):
    Vx[x,y] += amount_x
    Vy[x,y] += amount_y

def Render(screen):
    for i in range(N):
        for j in range(N):
            x = i * (SCALE)
            y = j * (SCALE)
            d = density[i,j]
            log_density = np.log10(d + 1)
            D = int((log_density / np.log10(256)) * 255)
            D = min(max(D, 0), 255)

            rectangle = pygame.Rect(x, y, SCALE, SCALE)
            pygame.draw.rect(screen, (D,D,D), rectangle)


def Walls(array, t, N): # 1 = sides, 2 = tops, 0 = corners
    if (t == "top"):
        array[0] = -array[1]
        array[N-1] = -array[N-2]
    if (t == "side"):
        array[:,0] = -array[:,1]
        array[:,N-1] = -array[:,N-2]
    # Corners
    array[0,0] = 0.5*(array[1,0]+array[0,1])
    array[0,N-1] = 0.5*(array[1,N-1]+array[0,N-2])
    array[N-1,0] = 0.5*(array[N-2,0]+array[N-1,1])
    array[N-1,N-1] = 0.5*(array[N-1,N-2]+array[N-2,N-1])


def Solver(array, array0, a, c, iter, t, N):
    for k in range(iter):
        for i in range(1,N-1):#may be out of bounds - we want the box inside the edges
            for j in range(1,N-1):
                array[i,j] = (array0[i,j] + a * (
                                array[i+1,j] + array[i-1,j]
                                + array[i,j+1] + array[i,j-1])
                            ) * (1/c)
        Walls(array,t,N)


def Diffuse(array, array0, diff, dt, iter, t, N): #check necessity of these. maybe they can be stored as global variables
    a = dt * diff * (N-2)**2
    Solver(array, array0, a, 1+4*a, iter, t, N)


def Project(Vx, Vy, p, div, iter, N):
    for i in range(1,N-1):
        for j in range(1,N-1):
            div[i,j] = -0.5 * (
                Vx[i+1,j] - Vx[i-1,j] +
                Vy[i,j+1] - Vy[i,j-1]
            ) / N
            p[i,j] = 0
    Walls(div,"",N)
    Walls(p,"",N)
    Solver(p,div,1,4,iter,"",N)
    #for j in range(1, N - 1):
    #        for i in range(1, N - 1):
     #           p[i][j] = (div[i][j] + p[i-1][j] + p[i+1][j] + p[i][j-1] + p[i][j+1]) / 4

    for i in range(1,N-1):
        for j in range(1,N-1):
            Vx -= 0.5 * (p[i+1,j] - p[i-1,j]) * N
            Vy -= 0.5 * (p[i,j+1] - p[i,j-1]) * N
    Walls(Vx,"side",N)
    Walls(Vy,"top",N)


def Advect(t, array, array0, Vx, Vy, dt, N):
    dtx = dty = dt * (N-2)
    for i in range(1,N-1):
        for j in range(1,N-1):
            tmp1 = dtx * Vx[i,j]
            tmp2 = dty * Vy[i,j]
            x = i - tmp1 #maybe x is global variable
            y = j - tmp2

            x = max(0.5, min(x, N + 0.5))
            y = max(0.5, min(y, N + 0.5))

            i0 = int(math.floor(x))
            i1 = i0 + 1
            j0 = int(math.floor(y))
            j1 = j0 + 1

            s1 = x - i0
            s0 = 1 - s1
            t1 = y - j0
            t0 = 1 - t1

            i0i, i1i = i0, i1
            j0i, j1i = j0, j1

            array[i,j] = (
                s0 * (t0 * array0[i0i, j0i]
                    + t1 * array[i0i, j1i])
                + s1 * (t0 * array0[i1i,j0i] 
                    + t1 * array0[i1i,j1i])
            )
    Walls(array,t,N)


def Step():
    Diffuse(Vx0, Vx, viscosity, dt, 4, "side", N)
    Diffuse(Vy0, Vy, viscosity, dt, 4, "top", N)
    Project(Vx0, Vy0, Vx, Vy, 4, N)
    Advect("side", Vx, Vx0, Vx0, Vy0, dt, N)
    Advect("top", Vy, Vy0, Vx0, Vy0, dt, N)
    Project(Vx, Vy, Vx, Vx0, 4, N)
    Diffuse(s, density, diffusion, dt, 4, 0, N)
    Advect(0, density, s, Vx, Vy, dt, N)