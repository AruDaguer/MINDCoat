# -*- coding: utf-8 -*-
"""
MINDCoat OS - Backend de Controle para o Dip Coater PTL-6PB
"""

import os
import time
from flask import Flask, render_template, jsonify, request

# Determina caminho absoluto automático da pasta templates para evitar TemplateNotFound
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')
app = Flask(__name__, template_folder=template_dir)

# Estado inicial completo para as 6 estações 
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
    "dwell_countdown": 0.0,
    "dry_countdown": 0.0,
    "stirring_speed": "OFF", # OFF, LOW, HIGH
    "mixing_status": {0: False, 1: False, 2: False, 3: False, 4: False, 5: False},
    "temperatures": {0: 20.0, 1: 20.0, 2: 20.0, 3: 20.0, 4: 20.0, 5: 20.0},
    "setpoints": {0: 50.0, 1: 50.0, 2: 50.0, 3: 50.0, 4: 50.0, 5: 50.0},
    "heaters_on": {0: False, 1: False, 2: False, 3: False, 4: False, 5: False},
    "faults": {0: False, 1: False, 2: False, 3: False, 4: False, 5: False},
    "current_cycle": 1,
    "total_cycles": 1
}

# Configurações padrão de movimento do Eixo Z
motion_config = {
    "travel": 85.0,
    "up_speed": 400.0,
    "down_speed": 400.0,
    "dwell_time": 10,
    "dry_time": 5,
    "dip_times": 1,
    "working_position": 1
}

# Banco de dados de receitas em memória para o protótipo
recipes_db = dict()

# Variáveis para controle dinâmico da simulação sem threads
sim_start_time = 0.0
sim_pause_time = 0.0
sim_accumulated_pause = 0.0
sim_temp_last_update = time.time()

def update_simulation():
    """
    Simulador determinístico. Calcula as físicas térmica e mecânica do robô
    de forma linear no exato momento da requisição, garantindo estabilidade.
    """
    global sim_accumulated_pause, sim_temp_last_update
    current_time = time.time()
    
    # 1. Simulação Térmica das 6 Estações (Aquecimento e Perda de Calor)
    temp_elapsed = current_time - sim_temp_last_update
    sim_temp_last_update = current_time
    
    for i in range(6):
        setpoint = machine_state.get("setpoints").get(i)
        heater_on = machine_state.get("heaters_on").get(i)
        fault = machine_state.get("faults").get(i)
        current_temp = machine_state.get("temperatures").get(i)
        
        if fault:
            # Em caso de quebra simulada do termopar (orAL), a leitura despenca
            machine_state.get("temperatures").__setitem__(i, max(0.0, current_temp - 2.0 * temp_elapsed))
            continue
            
        target_temp = setpoint if heater_on else 22.0 # temperatura ambiente
        diff = target_temp - current_temp
        if abs(diff) > 0.1:
            step = diff * 0.1 * temp_elapsed
            machine_state.get("temperatures").__setitem__(i, round(current_temp + step, 2))
        else:
            machine_state.get("temperatures").__setitem__(i, round(target_temp, 1))

    # 2. Simulação Cinemática do Eixo Z (Com suporte a múltiplos ciclos de imersão)
    if machine_state.get("is_running") and not machine_state.get("is_paused"):
        elapsed = current_time - sim_start_time - sim_accumulated_pause
        
        # Tempos de trânsito em segundos
        time_down = motion_config.get("travel") / (motion_config.get("down_speed") / 60.0)
        time_dwell = motion_config.get("dwell_time")
        time_up = motion_config.get("travel") / (motion_config.get("up_speed") / 60.0)
        time_dry = motion_config.get("dry_time")
        
        single_cycle = time_down + time_dwell + time_up + time_dry
        total_duration = single_cycle * motion_config.get("dip_times")
        
        if elapsed < total_duration:
            # Identifica em qual ciclo de imersão o processo se encontra
            cycle_index = int(elapsed // single_cycle)
            machine_state["current_cycle"] = cycle_index + 1
            
            # Tempo decorrido no ciclo atual
            cycle_elapsed = elapsed % single_cycle
            
            # Fase 1: Descendo
            if cycle_elapsed < time_down:
                speed_per_sec = motion_config.get("down_speed") / 60.0
                machine_state["z_position"] = round(cycle_elapsed * speed_per_sec, 2)
                machine_state["status_message"] = f"Mergulhando... (Ciclo {machine_state.get('current_cycle')} - {machine_state.get('z_position')} mm)"
                machine_state["dwell_countdown"] = float(motion_config.get("dwell_time"))
                machine_state["dry_countdown"] = float(motion_config.get("dry_time"))
                machine_state["up_limit"] = False
                machine_state["down_limit"] = False
                
            # Fase 2: Tempo de Imersão (Dwell)
            elif cycle_elapsed < (time_down + time_dwell):
                machine_state["z_position"] = motion_config.get("travel")
                machine_state["down_limit"] = True
                remaining_dwell = (time_down + time_dwell) - cycle_elapsed
                machine_state["dwell_countdown"] = round(remaining_dwell, 1)
                machine_state["status_message"] = f"Imerso na Estação {machine_state.get('working_position')}. Restam {machine_state.get('dwell_countdown')} s"
                
            # Fase 3: Subida (Içamento)
            elif cycle_elapsed < (time_down + time_dwell + time_up):
                machine_state["down_limit"] = False
                up_elapsed = cycle_elapsed - (time_down + time_dwell)
                speed_per_sec = motion_config.get("up_speed") / 60.0
                machine_state["z_position"] = round(motion_config.get("travel") - (up_elapsed * speed_per_sec), 2)
                machine_state["z_position"] = max(0.00, machine_state.get("z_position"))
                machine_state["status_message"] = f"Içando... (Ciclo {machine_state.get('current_cycle')} - {machine_state.get('z_position')} mm)"
                
            # Fase 4: Tempo de Secagem (Dry)
            else:
                machine_state["z_position"] = 0.0
                machine_state["up_limit"] = True
                remaining_dry = (time_down + time_dwell + time_up + time_dry) - cycle_elapsed
                machine_state["dry_countdown"] = round(remaining_dry, 1)
                machine_state["status_message"] = f"Secando... (Ciclo {machine_state.get('current_cycle')} - Restam {machine_state.get('dry_countdown')} s)"
                
        else:
            # Fim de todas as repetições
            machine_state["z_position"] = 0.0
            machine_state["is_running"] = False
            machine_state["up_limit"] = True
            machine_state["dwell_countdown"] = 0.0
            machine_state["dry_countdown"] = 0.0
            machine_state["current_cycle"] = motion_config.get("dip_times")
            machine_state["status_message"] = "Processo de recobrimento finalizado!"
            
    elif not machine_state.get("is_running"):
        machine_state["dwell_countdown"] = 0.0
        machine_state["dry_countdown"] = 0.0

def get_serializable_state():
    """
    Converte os dicionários de mapeamento interno do Python em listas
    ordenadas para serem processadas corretamente pelo front-end em JavaScript.
    """
    state_copy = dict()
    for k, v in machine_state.items():
        if isinstance(v, dict):
            state_copy[k] = list(v.get(x) for x in range(6))
        else:
            state_copy[k] = v
    return state_copy

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/api/status')
def get_status():
    update_simulation()
    return jsonify({
        "state": get_serializable_state(),
        "config": motion_config
    })

@app.post('/api/config')
def update_config():
    global motion_config, machine_state
    data = request.json
    try:
        motion_config["travel"] = float(data.get("travel", motion_config.get("travel")))
        motion_config["up_speed"] = float(data.get("up_speed", motion_config.get("up_speed")))
        motion_config["down_speed"] = float(data.get("down_speed", motion_config.get("down_speed")))
        motion_config["dwell_time"] = int(data.get("dwell_time", motion_config.get("dwell_time")))
        motion_config["dry_time"] = int(data.get("dry_time", motion_config.get("dry_time")))
        motion_config["dip_times"] = int(data.get("dip_times", motion_config.get("dip_times")))
        motion_config["working_position"] = int(data.get("working_position", motion_config.get("working_position")))
        
        machine_state["working_position"] = motion_config.get("working_position")
        return jsonify({"status": "success", "config": motion_config})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.post('/api/control')
def control_action():
    global machine_state, sim_start_time, sim_pause_time, sim_accumulated_pause
    action = request.json.get("action")
    current_time = time.time()
    
    if action == "run":
        if not machine_state.get("is_running"):
            machine_state["is_running"] = True
            machine_state["is_paused"] = False
            machine_state["z_position"] = 0.00
            sim_start_time = current_time
            sim_accumulated_pause = 0.0
            machine_state["current_cycle"] = 1
            machine_state["status_message"] = "Iniciando ciclo..."
        elif machine_state.get("is_paused"):
            machine_state["is_paused"] = False
            sim_accumulated_pause += (current_time - sim_pause_time)
            machine_state["status_message"] = "Retomando ciclo..."
    elif action == "pause":
        if machine_state.get("is_running") and not machine_state.get("is_paused"):
            machine_state["is_paused"] = True
            sim_pause_time = current_time
            machine_state["status_message"] = "Processo pausado"
    elif action == "stop":
        machine_state["is_running"] = False
        machine_state["is_paused"] = False
        machine_state["z_position"] = 0.00
        machine_state["status_message"] = "Processo interrompido pelo operador"
    elif action == "home":
        machine_state["is_running"] = False
        machine_state["is_paused"] = False
        machine_state["z_position"] = 0.00
        machine_state["up_limit"] = True
        machine_state["down_limit"] = False
        machine_state["status_message"] = "Eixo Z retornado ao ponto zero."
        
    return jsonify({"status": "success", "state": get_serializable_state()})

@app.post('/api/temperature')
def control_temperature():
    global machine_state
    data = request.json
    index = int(data.get("index"))
    
    if "setpoint" in data:
        machine_state.get("setpoints").__setitem__(index, float(data.get("setpoint")))
    if "heater_on" in data:
        machine_state.get("heaters_on").__setitem__(index, bool(data.get("heater_on")))
    if "fault" in data:
        machine_state.get("faults").__setitem__(index, bool(data.get("fault")))
        
    return jsonify({"status": "success", "state": get_serializable_state()})

@app.post('/api/tuning')
def trigger_autotune():
    index = int(request.json.get("index"))
    return jsonify({
        "status": "success", 
        "message": f"Auto-sintonia PID iniciada para a Estação {index + 1}."
    })

@app.post('/api/stirring')
def control_stirring():
    global machine_state
    data = request.json
    if "speed" in data:
        machine_state["stirring_speed"] = data.get("speed")
    if "mixing" in data:
        mixing_list = data.get("mixing")
        for x in range(6):
            machine_state.get("mixing_status").__setitem__(x, bool(mixing_list.__getitem__(x)))
    return jsonify({"status": "success", "state": get_serializable_state()})

@app.route('/api/recipes', methods={'GET', 'POST'})
def handle_recipes():
    if request.method == 'POST':
        data = request.json
        name = data.get("name")
        config_data = data.get("config")
        recipes_db.update({name: config_data})
        return jsonify({"status": "success", "recipes": recipes_db})
    return jsonify({"recipes": recipes_db})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)