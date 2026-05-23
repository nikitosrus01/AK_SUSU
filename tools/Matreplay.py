import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
from pathlib import Path

# ==================== ЗАГРУЗКА ДАННЫХ ====================
csv_path = Path(__file__).parent / "flight.csv"
if not csv_path.exists():
    print(f"Ошибка: файл {csv_path} не найден!")
    exit(1)

data = pd.read_csv(csv_path)
if 'TIME_MS' in data.columns:
    data['TIME_S'] = data['TIME_MS'] / 1000.0
elif 'TIME_S' not in data.columns:
    print("Нет колонки TIME_MS или TIME_S")
    exit(1)

if 'SPEED_M_S' not in data.columns:
    data['SPEED_M_S'] = -np.gradient(data['ALTITUDE_M'], data['TIME_S'])
    data['SPEED_M_S'] = data['SPEED_M_S'].abs()

state_names = ['Подъём/падение', 'Тормозной', 'Основной', 'ОПОРЫ', 'ПОСАДКА']
state_colors = ['blue', 'orange', 'red', 'green', 'purple']

# ==================== ГРАФИКИ ====================
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
fig.subplots_adjust(bottom=0.2, left=0.1, top=0.92)
fig.suptitle("Симуляция полёта: интерактивная реконструкция", fontsize=14)

ax1.set_ylabel('Высота (м)')
ax1.grid(True)
line_height, = ax1.plot([], [], 'b-', lw=2)
point_height, = ax1.plot([], [], 'ro', markersize=8)
ax1.set_ylim(0, data['ALTITUDE_M'].max() * 1.05)

ax2.set_ylabel('Скорость (м/с)')
ax2.grid(True)
line_speed, = ax2.plot([], [], 'g-', lw=2)
point_speed, = ax2.plot([], [], 'ro', markersize=8)
max_speed = data['SPEED_M_S'].max()
ax2.set_ylim(0, max_speed * 1.1 if max_speed > 0 else 5)

ax3.set_xlabel('Время (с)')
ax3.set_ylabel('Состояние')
ax3.set_yticks(range(len(state_names)))
ax3.set_yticklabels(state_names)
ax3.grid(True, axis='x')
for i in range(len(data)-1):
    state = int(data.iloc[i]['STATE'])
    if state < len(state_names):
        ax3.axvspan(data.iloc[i]['TIME_S'], data.iloc[i+1]['TIME_S'],
                    alpha=0.3, color=state_colors[state])
point_state, = ax3.plot([], [], 'ro', markersize=10)
ax3.set_xlim(data['TIME_S'].iloc[0], data['TIME_S'].iloc[-1])

info_text = ax1.text(0.02, 0.95, '', transform=ax1.transAxes, fontsize=10,
                     bbox=dict(facecolor='white', alpha=0.8))

# ==================== ИНТЕРАКТИВНЫЕ ЭЛЕМЕНТЫ ====================
ax_play = plt.axes([0.15, 0.05, 0.1, 0.04])
ax_pause = plt.axes([0.27, 0.05, 0.1, 0.04])
ax_reset = plt.axes([0.39, 0.05, 0.1, 0.04])
ax_step = plt.axes([0.51, 0.05, 0.1, 0.04])
ax_slider = plt.axes([0.15, 0.12, 0.65, 0.03])

btn_play = Button(ax_play, '▶ Play')
btn_pause = Button(ax_pause, '⏸ Pause')
btn_reset = Button(ax_reset, '⟳ Reset')
btn_step = Button(ax_step, '⏩ Step')
slider = Slider(ax_slider, 'Время (с)', data['TIME_S'].iloc[0], data['TIME_S'].iloc[-1], valinit=0, valfmt='%.2f')

# Глобальные переменные
current_frame = 0
is_playing = False
timer = None

def update_display(frame):
    """Обновление графиков по номеру кадра"""
    if frame >= len(data):
        return
    t = data['TIME_S'].iloc[frame]
    alt = data['ALTITUDE_M'].iloc[frame]
    sp = data['SPEED_M_S'].iloc[frame]
    state = int(data['STATE'].iloc[frame])

    t_data = data['TIME_S'].iloc[:frame+1]
    alt_data = data['ALTITUDE_M'].iloc[:frame+1]
    sp_data = data['SPEED_M_S'].iloc[:frame+1]

    line_height.set_data(t_data, alt_data)
    point_height.set_data([t], [alt])
    line_speed.set_data(t_data, sp_data)
    point_speed.set_data([t], [sp])
    point_state.set_data([t], [state])

    info_text.set_text(f'Время: {t:.2f} с\nВысота: {alt:.1f} м\nСкорость: {sp:.1f} м/с\nСостояние: {state_names[state]}')
    ax1.set_title(f'Этап: {state_names[state]}', color=state_colors[state])

    slider.eventson = False
    slider.set_val(t)
    slider.eventson = True

    fig.canvas.draw_idle()

def play_animation(event):
    global is_playing, current_frame, timer
    if is_playing:
        return
    is_playing = True
    def step():
        global current_frame, is_playing, timer
        if is_playing and current_frame < len(data) - 1:
            current_frame += 1
            update_display(current_frame)
            timer = fig.canvas.new_timer(interval=50)
            timer.add_callback(step)
            timer.start()
        else:
            is_playing = False
    step()

def pause_animation(event):
    global is_playing, timer
    is_playing = False
    if timer:
        timer.stop()

def reset_animation(event):
    global current_frame, is_playing, timer
    is_playing = False
    if timer:
        timer.stop()
    current_frame = 0
    update_display(0)

def step_forward(event):
    global current_frame, is_playing, timer
    is_playing = False
    if timer:
        timer.stop()
    if current_frame < len(data) - 1:
        current_frame += 1
        update_display(current_frame)

def on_slider(val):
    global current_frame, is_playing, timer
    is_playing = False
    if timer:
        timer.stop()
    t = val
    idx = np.argmin(np.abs(data['TIME_S'] - t))
    current_frame = idx
    update_display(current_frame)

btn_play.on_clicked(play_animation)
btn_pause.on_clicked(pause_animation)
btn_reset.on_clicked(reset_animation)
btn_step.on_clicked(step_forward)
slider.on_changed(on_slider)

update_display(0)
plt.show()