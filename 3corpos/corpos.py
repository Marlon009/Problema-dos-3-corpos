import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import deque

# ===================== CONSTANTES E FÍSICA =====================
G = 6.67430e-11  # Constante gravitacional (m³ kg⁻¹ s⁻²)
SCALE_FACTOR = 1e9  # 1 unidade = 1 milhão de quilômetros
DT = 86400  # Passo de tempo inicial (1 dia em segundos)

class Body:
    def __init__(self, mass, x, y, vx, vy, color):
        self.mass = mass
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.prev_x = x - vx * DT
        self.prev_y = y - vy * DT
        self.ax = 0.0
        self.ay = 0.0

def compute_forces(bodies):
    n = len(bodies)
    for i in range(n):
        bodies[i].ax = 0.0
        bodies[i].ay = 0.0

    for i in range(n):
        for j in range(i+1, n):
            dx = bodies[j].x - bodies[i].x
            dy = bodies[j].y - bodies[i].y
            r_sq = dx**2 + dy**2
            r = np.sqrt(r_sq) + 1e-10  # Evitar divisão por zero
            
            F = G * bodies[i].mass * bodies[j].mass / r_sq
            fx = F * dx / r
            fy = F * dy / r
            
            bodies[i].ax += fx / bodies[i].mass
            bodies[i].ay += fy / bodies[i].mass
            bodies[j].ax -= fx / bodies[j].mass
            bodies[j].ay -= fy / bodies[j].mass

def update_positions(bodies, dt):
    for b in bodies:
        new_x = 2 * b.x - b.prev_x + b.ax * dt**2
        new_y = 2 * b.y - b.prev_y + b.ay * dt**2
        b.prev_x, b.x = b.x, new_x
        b.prev_y, b.y = b.y, new_y

# ===================== INTERFACE GRÁFICA =====================
class SimulationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulação Gravitacional Interativa")
        self.geometry("1300x800")
        
        self.bodies = []
        self.is_running = False
        self.trail_length = 100
        self.dt = DT
        
        self.trails = []
        self.create_widgets()
        self.load_presets()
        self.load_selected_preset()

    def create_widgets(self):
        # Painel de controle
        control_frame = ttk.LabelFrame(self, text="Controles", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Seletor de presets
        self.preset_var = tk.StringVar()
        ttk.Label(control_frame, text="Presets:").pack(anchor=tk.W)
        self.preset_combobox = ttk.Combobox(control_frame, textvariable=self.preset_var, state="readonly")
        self.preset_combobox.pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Carregar", command=self.load_selected_preset).pack()

        # Controle de velocidade
        ttk.Label(control_frame, text="Passo temporal (dias):").pack(anchor=tk.W)
        self.dt_slider = ttk.Scale(control_frame, from_=0.1, to=30, command=lambda v: self.update_dt(float(v)))
        self.dt_slider.set(1)
        self.dt_slider.pack(fill=tk.X)

        # Controle de rastro
        ttk.Label(control_frame, text="Comprimento do rastro:").pack(anchor=tk.W, pady=(10,0))
        self.trail_slider = ttk.Scale(control_frame, from_=50, to=500, command=lambda v: setattr(self, 'trail_length', int(v)))
        self.trail_slider.set(100)
        self.trail_slider.pack(fill=tk.X)

        # Botões de controle
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="Iniciar", command=self.toggle_simulation)
        self.start_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="Reiniciar", command=self.reset_simulation).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Adicionar Corpo", command=self.add_body_dialog).pack(side=tk.LEFT, padx=2)

        # Área de visualização
        fig = Figure(figsize=(8, 8), dpi=100)
        self.ax = fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def load_presets(self):
        self.presets = {
            "Sistema Solar": [
                Body(1.9885e30, 0, 0, 0, 0, 'yellow'),
                Body(3.3011e23, 57.9e9, 0, 0, 47.36e3, 'gray'),
                Body(4.8675e24, 108.2e9, 0, 0, 35.02e3, 'orange'),
                Body(5.9724e24, 149.6e9, 0, 0, 29.78e3, 'blue'),
            ],
            "Estrela Binária": [
                Body(1e30, -1e10, 0, 0, 2e4, 'red'),
                Body(1e30, 1e10, 0, 0, -2e4, 'blue')
            ],
            "Órbita Lunar": [
                Body(5.9724e24, 0, 0, 0, 0, 'blue'),
                Body(7.342e22, 384.4e6, 0, 0, 1.022e3, 'gray')
            ]
        }
        self.preset_combobox['values'] = list(self.presets.keys())

    def load_selected_preset(self):
        preset_name = self.preset_var.get()
        if not preset_name:
            preset_name = "Sistema Solar"
            self.preset_var.set(preset_name)
        
        self.bodies = [Body(b.mass, b.x, b.y, b.vx, b.vy, b.color) for b in self.presets[preset_name]]
        self.trails = [deque(maxlen=self.trail_length) for _ in self.bodies]
        self.update_plot()

    def add_body_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Adicionar Novo Corpo")
        
        fields = [
            ('Massa (kg)', '1e24'),
            ('Posição X (m)', '0'),
            ('Posição Y (m)', '0'),
            ('Velocidade X (m/s)', '0'),
            ('Velocidade Y (m/s)', '0'),
            ('Cor', 'white')
        ]
        
        entries = {}
        for row, (label, default) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=row, column=0, padx=5, pady=2)
            entry = ttk.Entry(dialog)
            entry.insert(0, default)
            entry.grid(row=row, column=1, padx=5, pady=2)
            entries[label] = entry

        ttk.Button(dialog, text="Adicionar",
                 command=lambda: self.validate_new_body(entries, dialog)).grid(row=row+1, columnspan=2)

    def validate_new_body(self, entries, dialog):
        try:
            mass = float(entries['Massa (kg)'].get())
            x = float(entries['Posição X (m)'].get())
            y = float(entries['Posição Y (m)'].get())
            vx = float(entries['Velocidade X (m/s)'].get())
            vy = float(entries['Velocidade Y (m/s)'].get())
            color = entries['Cor'].get()
            
            new_body = Body(mass, x, y, vx, vy, color)
            self.bodies.append(new_body)
            self.trails.append(deque(maxlen=self.trail_length))
            dialog.destroy()
            self.update_plot()
        except Exception as e:
            messagebox.showerror("Erro", f"Valores inválidos!\n{str(e)}")

    def update_dt(self, days):
        self.dt = days * 86400  # Converter dias para segundos

    def toggle_simulation(self):
        self.is_running = not self.is_running
        self.start_btn.config(text="Pausar" if self.is_running else "Continuar")
        if self.is_running:
            self.run_simulation()

    def reset_simulation(self):
        self.is_running = False
        self.start_btn.config(text="Iniciar")
        self.load_selected_preset()

    def run_simulation(self):
        if self.is_running:
            compute_forces(self.bodies)
            update_positions(self.bodies, self.dt)
            
            # Atualizar rastros
            for i, body in enumerate(self.bodies):
                self.trails[i].append((body.x/SCALE_FACTOR, body.y/SCALE_FACTOR))
                if len(self.trails[i]) > self.trail_length:
                    self.trails[i].popleft()
            
            self.update_plot()
            self.after(10, self.run_simulation)

    def update_plot(self):
        self.ax.clear()
        
        # Desenhar rastros
        for i, trail in enumerate(self.trails):
            if trail:
                x, y = zip(*trail)
                self.ax.plot(x, y, color=self.bodies[i].color, alpha=0.3, linewidth=1)
        
        # Desenhar corpos
        for body in self.bodies:
            self.ax.plot(
                body.x/SCALE_FACTOR,
                body.y/SCALE_FACTOR,
                'o',
                markersize=np.log10(body.mass)/7 + 2,
                color=body.color,
                markeredgecolor='white'
            )
        
        # Ajustar limites
        if self.bodies:
            x_pos = [b.x/SCALE_FACTOR for b in self.bodies]
            y_pos = [b.y/SCALE_FACTOR for b in self.bodies]
            
            margin = 0.2
            x_min, x_max = min(x_pos), max(x_pos)
            y_min, y_max = min(y_pos), max(y_pos)
            
            x_center = (x_min + x_max) / 2
            y_center = (y_min + y_max) / 2
            x_range = max(x_max - x_min, 1e6) * (1 + margin)
            y_range = max(y_max - y_min, 1e6) * (1 + margin)
            
            self.ax.set_xlim(x_center - x_range/2, x_center + x_range/2)
            self.ax.set_ylim(y_center - y_range/2, y_center + y_range/2)
        
        self.ax.set_xlabel('Distância (milhões de km)')
        self.ax.set_ylabel('Distância (milhões de km)')
        self.ax.grid(True, linestyle='--', alpha=0.5)
        self.ax.set_facecolor('black')
        self.canvas.draw()

# ===================== EXECUÇÃO =====================
if __name__ == "__main__":
    app = SimulationApp()
    app.mainloop()