from vpython import *
import pandas as pd
import numpy as np
import time
from pathlib import Path

# ==================== ЗАГРУЗКА ДАННЫХ ====================
csv_path = Path(__file__).parent / "flight.csv"
if not csv_path.exists():
    print("Ошибка: flight.csv не найден! Генерирую демо-данные...")
    t = np.linspace(0, 12, 300)
    alt = 50 * (1 - t/12)**1.5
    state = np.zeros_like(t, dtype=int)
    for i, tt in enumerate(t):
        if tt < 2.5:
            state[i] = 0
        elif tt < 6:
            state[i] = 1
        elif tt < 8.5:
            state[i] = 2
        elif tt < 9.5:
            state[i] = 3
        else:
            state[i] = 4
    df = pd.DataFrame({'TIME_S': t, 'ALTITUDE_M': alt, 'STATE': state})
    df['SPEED_M_S'] = -np.gradient(alt, t)
    df.to_csv(csv_path, index=False)
    data = df
else:
    data = pd.read_csv(csv_path)
    if 'TIME_MS' in data.columns:
        data['TIME_S'] = data['TIME_MS'] / 1000.0
    if 'SPEED_M_S' not in data.columns:
        data['SPEED_M_S'] = -np.gradient(data['ALTITUDE_M'], data['TIME_S'])
        data['SPEED_M_S'] = np.abs(data['SPEED_M_S'])

state_names = ['Подъём', 'Тормозной', 'Основной', 'Опоры', 'Посадка']
state_colors = [color.blue, color.orange, color.red, color.green, color.magenta]
max_alt = max(data['ALTITUDE_M'].max(), 1)

# ==================== СЦЕНА ====================
scene = canvas(title="3D Симуляция", width=1200, height=800,
               background=vector(0.1, 0.2, 0.4), center=vector(0, max_alt/2, 0))
scene.forward = vector(0, -0.25, -1)
scene.ambient = vector(0.3, 0.3, 0.3)

ground = box(pos=vector(0, -1.5, 0), size=vector(120, 0.2, 120), color=vector(0.2, 0.5, 0.1), texture=textures.rough)

for i in range(200):
    x = np.random.uniform(-55, 55)
    z = np.random.uniform(-55, 55)
    grass_blade = cylinder(pos=vector(x, -1.3, z), axis=vector(0, np.random.uniform(0.1,0.3), 0), radius=0.05, color=vector(0,0.7,0))

sun = local_light(pos=vector(100, 80, 50), color=vector(1,1,0.9))
ambient_light = local_light(pos=vector(-30, 30, -40), color=vector(0.4,0.4,0.5))

clouds = []
for _ in range(15):
    xc = np.random.uniform(-60,60)
    zc = np.random.uniform(-50,50)
    yc = max_alt+4 + np.random.uniform(0,4)
    cloud = compound([sphere(pos=vector(0,0,0), radius=2.2, color=color.white, opacity=0.8),
                      sphere(pos=vector(1.5,0.5,1), radius=1.8, color=color.white, opacity=0.8),
                      sphere(pos=vector(-1.2,0.3,1.2), radius=1.9, color=color.white, opacity=0.8)],
                      pos=vector(xc, yc, zc))
    clouds.append(cloud)

# ==================== КРАСИВЫЙ МОДУЛЬ  ====================
body_main = cylinder(pos=vector(0,0,0), axis=vector(0,1.6,0), radius=0.65, color=vector(0.85,0.85,0.95), shininess=0.8)
body_upper = cylinder(pos=vector(0,1.6,0), axis=vector(0,0.6,0), radius=0.55, color=vector(0.9,0.9,1.0), shininess=0.8)
nose_cone = cone(pos=vector(0,2.2,0), axis=vector(0,0.9,0), radius=0.5, color=vector(0.9,0.2,0.2), shininess=0.9)
window = sphere(pos=vector(0,1.2,0.65), radius=0.2, color=color.cyan, opacity=0.7, shininess=0.9)
antenna = cylinder(pos=vector(0,3.0,0), axis=vector(0,0.4,0), radius=0.05, color=color.yellow)

fins = []
for ang in [0, 90, 180, 270]:
    rad = np.radians(ang)
    x = 0.65 * np.cos(rad)
    z = 0.65 * np.sin(rad)
    fin = pyramid(pos=vector(x, 0.2, z), size=vector(0.2, 0.7, 0.4), color=vector(1,0.5,0), shininess=0.6)
    fin.rotate(angle=rad, axis=vector(0,1,0), origin=vector(0,0,0))
    fins.append(fin)

legs = []
leg_pos = [(-0.6, -0.1, 0), (0.6, -0.1, 0), (0, -0.1, 0.7)]
for lp in leg_pos:
    leg_base = cylinder(pos=vector(lp[0], lp[1], lp[2]), axis=vector(0,-0.7,0), radius=0.1, color=vector(0.2,0.7,0.8), visible=False)
    leg_foot = sphere(pos=vector(lp[0], lp[1]-0.7, lp[2]), radius=0.13, color=vector(0.1,0.5,0.6), visible=False)
    legs.append((leg_base, leg_foot))

drogue = compound([
    cone(pos=vector(0,0,0), axis=vector(0,-0.5,0), radius=1.0, color=vector(1,0.8,0.2)),
    ring(pos=vector(0,-0.5,0), radius=1.0, thickness=0.07, color=vector(1,0.6,0)),
    cylinder(pos=vector(0.6,0,0), axis=vector(0,-0.5,0), radius=0.02, color=color.white),
    cylinder(pos=vector(-0.6,0,0), axis=vector(0,-0.5,0), radius=0.02, color=color.white),
    cylinder(pos=vector(0,0,0.6), axis=vector(0,-0.5,0), radius=0.02, color=color.white),
    cylinder(pos=vector(0,0,-0.6), axis=vector(0,-0.5,0), radius=0.02, color=color.white),
], visible=False)

main_chute = compound([
    cone(pos=vector(0,0,0), axis=vector(0,-0.7,0), radius=2.2, color=vector(0.9,0.2,0.2)),
    ring(pos=vector(0,-0.2,0), radius=2.0, thickness=0.1, color=color.white),
    ring(pos=vector(0,-0.5,0), radius=1.8, thickness=0.08, color=color.white),
    ring(pos=vector(0,-0.7,0), radius=1.5, thickness=0.07, color=color.white),
], visible=False)


main_lines = []
for i in range(8):
    line = cylinder(radius=0.03, color=vector(0.8,0.6,0.4), visible=False)
    main_lines.append(line)

rocket_parts = [body_main, body_upper, nose_cone, window, antenna] + fins

# ==================== ТЕКСТОВЫЕ МЕТКИ ====================
info_label = label(pos=vector(-7, max_alt+3, -8), text='', height=16, box=False, color=color.white,
                   background=vector(0,0,0), opacity=0.6)
state_label = label(pos=vector(0, max_alt+5.5, -7), text='', height=22, box=True, color=color.white, border=5,
                    background=vector(0,0,0))
instr = label(pos=vector(-6, -2, -12), text="ПРОБЕЛ – пауза | → ← – кадры | R – сброс", height=13, box=False, color=color.gray(0.8))

# ==================== АНИМАЦИЯ ====================
current_frame = 0
total_frames = len(data)
animate = True
last_update = time.time()
frame_time = 1.0 / 25  # 25 fps

def update_frame():
    global current_frame
    if current_frame >= total_frames:
        state_label.text = "ПОЛЁТ ЗАВЕРШЁН"
        return
    row = data.iloc[current_frame]
    alt = row['ALTITUDE_M']
    state = int(row['STATE'])
    speed = row['SPEED_M_S']
    t = row['TIME_S']

    y_pos = alt - 1.2  
    for part in rocket_parts:
        part.pos.y = y_pos
    for leg_base, leg_foot in legs:
        leg_base.pos.y = y_pos - 0.1
        leg_foot.pos.y = y_pos - 0.8
    drogue.pos = vector(0, y_pos + 1.8, 0)
    main_chute.pos = vector(0, y_pos + 3.2, 0)

    drogue.visible = (state >= 1)
    main_chute.visible = (state >= 2)

    if state >= 2:
        for i, line in enumerate(main_lines):
            angle = i * 45
            rad = np.radians(angle)
            x = 1.8 * np.cos(rad)
            z = 1.8 * np.sin(rad)
            line.pos = vector(x, y_pos + 2.8, z)
            line.axis = vector(-x, 0.7, -z)
            line.visible = True
    else:
        for line in main_lines:
            line.visible = False

    for leg_base, leg_foot in legs:
        leg_base.visible = (state >= 3)
        leg_foot.visible = (state >= 3)

    if state == 4 and alt < 1.5:
        if np.random.random() < 0.3:
            dust = sphere(pos=vector(np.random.uniform(-1.5,1.5), -0.9, np.random.uniform(-1.5,1.5)),
                          radius=0.12, color=vector(0.5,0.3,0.1), make_trail=False, emissive=False)
            dust.v = vector(np.random.uniform(-1.5,1.5), np.random.uniform(1.5,3.5), np.random.uniform(-1.5,1.5))
            def animate_dust(d):
                d.pos += d.v * 0.05
                d.radius *= 0.96
                if d.radius < 0.02:
                    d.visible = False
            scene.append(dust)


    if state >= 1:
        angle_rot = np.sin(time.time() * 4) * 0.05
        for part in rocket_parts:
            part.rotate(angle=angle_rot, axis=vector(0,0,1), origin=vector(0,y_pos,0))
    else:
        for part in rocket_parts:
            part.rotation = vector(0,0,0)

    info_label.text = f"🕒 {t:.2f} с\n📏 {alt:.1f} м\n⚡ {speed:.1f} м/с"
    state_label.text = state_names[state]
    state_label.color = state_colors[state]

    scene.center = vector(0, y_pos + 3, 0)

# Управление
def on_keydown(ev):
    global animate, current_frame
    if ev.key == ' ':
        animate = not animate
    elif ev.key == 'right':
        animate = False
        if current_frame < total_frames - 1:
            current_frame += 1
            update_frame()
    elif ev.key == 'left':
        animate = False
        if current_frame > 0:
            current_frame -= 1
            update_frame()
    elif ev.key == 'r':
        animate = True
        current_frame = 0
        update_frame()

scene.bind('keydown', on_keydown)

update_frame()
while True:
    rate(60)
    if animate:
        now = time.time()
        if now - last_update >= frame_time:
            if current_frame < total_frames - 1:
                current_frame += 1
                update_frame()
            else:
                animate = False
            last_update = now