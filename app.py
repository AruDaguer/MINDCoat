# -*- coding: utf-8 -*-
"""
MINDCoat OS - Backend de Controle para o Dip Coater PTL-6PB
Desenvolvido para MINDLab
"""

from flask import Flask, render_template, jsonify, request
import json
import os
import time
import threading

app = Flask(__name__)

# Arquivo para persistência de receitas
RECIPE_FILE = os.path.join(os.path.dirname(__file__), 'recipes.json')

# Estado inicial simulado da máquina (caso o Klipper/Moonraker não esteja respondendo)
machine_state = {
    "connected": True,
    "z_position": 0.00,
    "target_z_position": 0.00,
    "working_position": 1,
    "up_limit": False,
    "down_limit": False,
    "is_running": False,
    "is_paused": False,
    "status_message": "Pronto para operação",
    "dwell_countdown": 0,
    "dry_countdown": 0,
    "stirring_speed": "OFF", # OFF, LOW, HIGH
    "mixing_status": [False] * 6, # Estações 1 a 6
    "temperatures": [20.0] * 6, # PV
    "setpoints": [50.0] * 6, # SV
    "heaters_on": [False] * 6,
    "faults": [False] * 6,
    "current_cycle": 1,
    "total_cycles": 1
}

# Configurações padrão de movimento
motion_config = {
    "travel": 85.0,
    "up_speed": 400.0,
    "down_speed": 400.0,
    "dwell_time": 10,
    "dry_time": 5,
    "dip_times": 1,
    "working_position": 1
}

def load_recipes():
    if os.path.exists(RECIPE_FILE):
        try:
            with open(RECIPE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_recipes(recipes):
    with open(RECIPE_FILE, 'w') as f:
        json.dump(recipes, f, indent=4)

# Thread para simulação de comportamento físico do robô em background
def background_simulator():
    global machine_state, motion_config
    while True:
        time.sleep(0.1)
        
        # Simula o aquecimento/resfriamento físico com base nos Setpoints e PID
        for i in range(6):
            target = machine_state["setpoints"][i] if machine_state["heaters_on"][i] else 22.0 # temp ambiente
            diff = target - machine_state["temperatures"][i]
            
            if machine_state["faults"][i]:
                # Se houver falha (ex: termopar desconectado), despenca a leitura
                machine_state["temperatures"][i] = max(0.0, machine_state["temperatures"][i] - 2.0)
                continue
                
            if abs(diff) > 0.1:
                # Simulação dinâmica de inércia térmica
                step = diff * 0.05 if machine_state["heaters_on"][i] else diff * 0.02
                machine_state["temperatures"][i] = round(machine_state["temperatures"][i] + step, 1)
            else:
                machine_state["temperatures"][i] = round(target, 1)

        # Simula a execução do movimento de Dip Coating se estiver rodando
        if machine_state["is_running"] and not machine_state["is_paused"]:
            # Fase 1: Descida (Z vai de 0.00 até Travel)
            if machine_state["z_position"] < motion_config["travel"] and machine_state["dwell_countdown"] == 0 and machine_state["dry_countdown"] == 0:
                step_z = (motion_config["down_speed"] / 60.0) * 0.1 # mm por 100ms
                machine_state["z_position"] = min(motion_config["travel"], round(machine_state["z_position"] + step_z, 2))
                machine_state["status_message"] = f"Mergulhando substrato... ({machine_state['z_position']}mm)"
                if machine_state["z_position"] >= motion_config["travel"]:
                    machine_state["down_limit"] = True
                    machine_state["dwell_countdown"] = motion_config["dwell_time"]

            # Fase 2: Tempo de Imersão (Dwell)
            elif machine_state["dwell_countdown"] > 0:
                machine_state["status_message"] = f"Imerso na Estação {machine_state['working_position']}. Restam {round(machine_state['dwell_countdown'], 1)}s"
                machine_state["dwell_countdown"] = round(max(0, machine_state["dwell_countdown"] - 0.1), 1)
                
            # Fase 3: Subida (Z volta para 0.00)
            elif machine_state["z_position"] > 0.00 and machine_state["dry_countdown"] == 0:
                machine_state["down_limit"] = False
                step_z = (motion_config["up_speed"] / 60.0) * 0.1
                machine_state["z_position"] = max(0.00, round(machine_state["z_position"] - step_z, 2))
                machine_state["status_message"] = f"Içando substrato... ({machine_state['z_position']}mm)"
                if machine_state["z_position"] <= 0.00:
                    machine_state["up_limit"] = True
                    machine_state["dry_countdown"] = motion_config["dry_time"]

            # Fase 4: Tempo de Secagem (Dry)
            elif machine_state["dry_countdown"] > 0:
                machine_state["status_message"] = f"Secagem ativa. Restam {round(machine_state['dry_countdown'], 1)}s"
                machine_state["dry_countdown"] = round(max(0, machine_state["dry_countdown"] - 0.1), 1)
                
            # Fase 5: Próximo ciclo ou fim do processo
            else:
                machine_state["up_limit"] = False
                if machine_state["current_cycle"] < motion_config["dip_times"]:
                    machine_state["current_cycle"] += 1
                else:
                    # Conclusão do ciclo de imersão
                    machine_state["is_running"] = False
                    machine_state["current_cycle"] = 1
                    machine_state["status_message"] = "Processo de recobrimento finalizado!"

# Inicia thread de background
sim_thread = threading.Thread(target=background_simulator, daemon=True)
sim_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=)
def get_status():
    return jsonify({
        "state": machine_state,
        "config": motion_config
    })

@app.route('/api/config', methods=)
def update_config():
    global motion_config, machine_state
    data = request.json
    try:
        motion_config["travel"] = float(data.get("travel", motion_config["travel"]))
        motion_config["up_speed"] = float(data.get("up_speed", motion_config["up_speed"]))
        motion_config["down_speed"] = float(data.get("down_speed", motion_config["down_speed"]))
        motion_config["dwell_time"] = int(data.get("dwell_time", motion_config["dwell_time"]))
        motion_config["dry_time"] = int(data.get("dry_time", motion_config["dry_time"]))
        motion_config["dip_times"] = int(data.get("dip_times", motion_config["dip_times"]))
        motion_config["working_position"] = int(data.get("working_position", motion_config["working_position"]))
        
        machine_state["working_position"] = motion_config["working_position"]
        return jsonify({"status": "success", "config": motion_config})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/control', methods=)
def control_action():
    global machine_state
    action = request.json.get("action")
    
    if action == "run":
        if not machine_state["is_running"]:
            machine_state["is_running"] = True
            machine_state["is_paused"] = False
            machine_state["z_position"] = 0.00
            machine_state["dwell_countdown"] = 0
            machine_state["dry_countdown"] = 0
            machine_state["current_cycle"] = 1
    elif action == "pause":
        machine_state["is_paused"] = True
        machine_state["status_message"] = "Processo pausado pelo operador"
    elif action == "stop":
        machine_state["is_running"] = False
        machine_state["is_paused"] = False
        machine_state["z_position"] = 0.00
        machine_state["status_message"] = "Processo abortado. Retornando ao ponto zero."
    elif action == "home":
        machine_state["z_position"] = 0.00
        machine_state["up_limit"] = True
        machine_state["down_limit"] = False
        machine_state["status_message"] = "Retornado ao zero absoluto do Eixo Z."
        
    return jsonify({"status": "success", "state": machine_state})

@app.route('/api/temperature', methods=)
def control_temperature():
    global machine_state
    data = request.json
    index = int(data.get("index")) # Estação 0 a 5
    
    if "setpoint" in data:
        machine_state["setpoints"][index] = float(data["setpoint"])
    if "heater_on" in data:
        machine_state["heaters_on"][index] = bool(data["heater_on"])
    if "fault" in data:
        machine_state["faults"][index] = bool(data["fault"])
        
    return jsonify({"status": "success", "state": machine_state})

@app.route('/api/tuning', methods=)
def trigger_autotune():
    index = int(request.json.get("index"))
    return jsonify({
        "status": "success", 
        "message": f"Auto-sintonia PID (Calibration) iniciada para a Estação {index + 1}."
    })

@app.route('/api/stirring', methods=)
def control_stirring():
    global machine_state
    data = request.json
    if "speed" in data:
        machine_state["stirring_speed"] = data["speed"] # OFF, LOW, HIGH
    if "mixing" in data:
        machine_state["mixing_status"] = data["mixing"] # Lista de Booleanos (6)
    return jsonify({"status": "success", "state": machine_state})

@app.route('/api/recipes', methods=)
def handle_recipes():
    recipes = load_recipes()
    if request.method == 'POST':
        data = request.json
        name = data.get("name")
        config = data.get("config")
        recipes[name] = config
        save_recipes(recipes)
        return jsonify({"status": "success", "recipes": recipes})
    return jsonify({"recipes": recipes})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)