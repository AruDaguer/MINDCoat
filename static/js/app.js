// TRADUÇÕES EM PORTUGUÊS E INGLÊS 
const translations = {
    pt: {
        pin_label: "Conexão com Klipper MCU",
        access_btn: "Conectar",
        tab_dashboard: "Dashboard",
        tab_params: "Parâmetros",
        tab_thermal: "Térmico",
        status_mcu: "Status:",
        profile_z_title: "Telemetria Z",
        current_travel: "Z Pos",
        dwell_time_lbl: "Imersão",
        dry_time_lbl: "Secagem",
        active_cycle_lbl: "Ciclo",
        up_limit: "Endstop Top",
        down_limit: "Endstop Bot",
        sys_controls: "Macros de Controle",
        btn_run: "Iniciar Ciclo",
        btn_pause: "Pausar",
        btn_home: "Homing Z (G28)",
        thermal_overview: "Aquecedores",
        z_params: "Cinemática Eixo Z",
        travel_lbl: "Curso (mm)",
        upspeed_lbl: "Içamento (mm/m)",
        downspeed_lbl: "Imersão (mm/m)",
        dwell_lbl: "Tempo Imersão (s)",
        dry_lbl: "Tempo Secagem (s)",
        carrousel_stir: "Carrossel & Agitação",
        times_lbl: "Ciclos (Qtd)",
        pos_lbl: "Estação Incial",
        stirring_speed: "Velocidade Global",
        stir_low: "Baixa",
        stir_high: "Alta",
        mix_toggles: "Atuadores",
        recipes_title: "Gerenciador de Macros",
        btn_apply: "Salvar Config (SAVE_CONFIG)",
        fault_bar: "Diagnóstico ADC (Termopares)"
    },
    en: {
        pin_label: "Klipper MCU Connection",
        access_btn: "Connect",
        tab_dashboard: "Dashboard",
        tab_params: "Settings",
        tab_thermal: "Thermal",
        status_mcu: "Status:",
        profile_z_title: "Z Telemetry",
        current_travel: "Z Pos",
        dwell_time_lbl: "Dwell",
        dry_time_lbl: "Dry",
        active_cycle_lbl: "Cycle",
        up_limit: "Endstop Top",
        down_limit: "Endstop Bot",
        sys_controls: "Control Macros",
        btn_run: "Start Cycle",
        btn_pause: "Pause",
        btn_home: "Z Homing (G28)",
        thermal_overview: "Heaters",
        z_params: "Z Axis Kinematics",
        travel_lbl: "Travel (mm)",
        upspeed_lbl: "Withdraw (mm/m)",
        downspeed_lbl: "Immerse (mm/m)",
        dwell_lbl: "Dwell Time (s)",
        dry_lbl: "Dry Time (s)",
        carrousel_stir: "Carousel & Stirring",
        times_lbl: "Cycles (Qty)",
        pos_lbl: "Start Station",
        stirring_speed: "Global Speed",
        stir_low: "Low",
        stir_high: "High",
        mix_toggles: "Actuators",
        recipes_title: "Macro Manager",
        btn_apply: "Save Config (SAVE_CONFIG)",
        fault_bar: "ADC Diagnostics (Thermocouples)"
    }
};

let currentLang = 'pt';
let currentTab = 'dashboard-tab';

function setLanguage(lang) {
    currentLang = lang;
    const translatableElements = Array.from(document.getElementsByTagName('*')).filter(el => el.hasAttribute('data-translate'));
    translatableElements.forEach(el => {
        const key = el.getAttribute('data-translate');
        const translatedText = translations[lang][key];
        if (translatedText) {
            el.textContent = translatedText;
        }
    });
    renderMixingToggles();
    renderThermalMatrix();
}

function unlockConsole() {
    const pin = document.getElementById('pin-input').value;
    if (pin === '0' || pin === '808') {
        document.getElementById('pin-gate').classList.add('hidden');
        document.getElementById('app-container').classList.remove('hidden');
        showToast("Connected to Klipper Engine", "success");
        updateState();
        setInterval(updateState, 500);
        loadRecipesList();
    } else {
        alert("Invalid PIN! Try '0' or '808'.");
    }
}

function switchTab(tabId) {
    document.querySelectorAll('aside nav button').forEach(btn => {
        btn.classList.remove('bg-zinc-800', 'text-zinc-100');
        btn.classList.add('text-zinc-400');
    });
    const activeBtn = document.getElementById('btn-' + tabId);
    activeBtn.classList.add('bg-zinc-800', 'text-zinc-100');
    activeBtn.classList.remove('text-zinc-400');

    document.getElementById(currentTab).classList.add('hidden');
    document.getElementById(tabId).classList.remove('hidden');
    currentTab = tabId;
}

function showToast(msg, type = "success") {
    const toast = document.getElementById('toast');
    const iconWrap = document.getElementById('toast-icon-wrapper');
    const icon = document.getElementById('toast-icon');
    const message = document.getElementById('toast-msg');

    message.textContent = msg;

    if (type === "success") {
        iconWrap.className = "w-8 h-8 rounded bg-brand-green/10 flex items-center justify-center";
        icon.className = "fa-solid fa-check text-brand-green";
    } else {
        iconWrap.className = "w-8 h-8 rounded bg-brand-red/10 flex items-center justify-center";
        icon.className = "fa-solid fa-triangle-exclamation text-brand-red";
    }

    toast.classList.remove('hidden');
    setTimeout(() => { toast.classList.add('hidden'); }, 3000);
}

async function updateState() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        const state = data.state;
        const config = data.config;

        document.getElementById('lbl-z-pos').innerHTML = state.z_position.toFixed(2) + '<span class="text-xs text-zinc-500 font-normal ml-1">mm</span>';
        document.getElementById('lbl-dwell').innerHTML = Math.ceil(state.dwell_countdown) + '<span class="text-xs text-zinc-500 font-normal ml-1">s</span>';
        document.getElementById('lbl-dry').innerHTML = state.dry_countdown.toFixed(1) + '<span class="text-xs text-zinc-500 font-normal ml-1">s</span>';
        document.getElementById('lbl-cycle').textContent = state.current_cycle + ' / ' + config.dip_times;
        document.getElementById('status-bar-message').textContent = state.status_message;

        const percent = (state.z_position / config.travel) * 100;
        document.getElementById('z-progress-bar').style.width = percent + '%';

        document.getElementById('led-up-limit').className = 'w-2.5 h-2.5 rounded-full ' + (state.up_limit ? 'bg-brand-green shadow-[0_0_8px_rgba(16,185,129,0.6)]' : 'bg-zinc-800');
        document.getElementById('led-down-limit').className = 'w-2.5 h-2.5 rounded-full ' + (state.down_limit ? 'bg-brand-red shadow-[0_0_8px_rgba(239,68,68,0.6)]' : 'bg-zinc-800');

        const speedModes = ['OFF', 'LOW', 'HIGH'];
        speedModes.forEach(spd => {
            const btn = document.getElementById('stir-btn-' + spd);
            if (state.stirring_speed === spd) {
                btn.className = "flex-1 py-1 rounded text-xs font-semibold bg-brand-blue text-white";
            } else {
                btn.className = "flex-1 py-1 rounded text-xs font-semibold bg-zinc-950 hover:bg-zinc-800 text-zinc-400";
            }
        });

        if (document.activeElement.tagName !== 'INPUT') {
            document.getElementById('input-travel').value = config.travel;
            document.getElementById('input-upspeed').value = config.up_speed;
            document.getElementById('input-downspeed').value = config.down_speed;
            document.getElementById('input-dwell').value = config.dwell_time;
            document.getElementById('input-dry').value = config.dry_time;
            document.getElementById('input-cycles').value = config.dip_times;
            document.getElementById('input-position').value = config.working_position;
        }

        updateDashboardTempGrid(state);
        updateDiagnosticLEDs(state);

    } catch (err) {
        document.getElementById('mcu-status-badge').innerHTML = '<span class="w-2 h-2 bg-brand-red rounded-full"></span> Offline';
        document.getElementById('mcu-status-badge').className = "flex items-center gap-1.5 text-brand-red font-semibold";
    }
}

function renderMixingToggles() {
    const container = document.getElementById('mixing-toggles-container');
    if (container.children.length === 0) {
        for (let i = 0; i < 6; i++) {
            const el = document.createElement('div');
            el.className = "flex items-center justify-between bg-zinc-950 p-2 rounded border border-zinc-800";
            el.innerHTML = `
                <span class="text-[10px] font-semibold text-zinc-400 uppercase">HEATER ${i + 1}</span>
                <button onclick="toggleMixing(${i})" id="mix-toggle-btn-${i}" class="w-8 h-4 bg-zinc-800 rounded-full relative transition-colors">
                    <span class="w-3 h-3 bg-zinc-500 rounded-full absolute top-0.5 left-0.5 transition-all" id="mix-toggle-ball-${i}"></span>
                </button>
            `;
            container.appendChild(el);
        }
    }
}

async function toggleMixing(idx) {
    const btn = document.getElementById('mix-toggle-btn-' + idx);
    const ball = document.getElementById('mix-toggle-ball-' + idx);
    const isCurrentlyOn = btn.classList.contains('bg-brand-green');
    
    if (!isCurrentlyOn) {
        btn.className = "w-8 h-4 bg-brand-green rounded-full relative transition-colors";
        ball.className = "w-3 h-3 bg-white rounded-full absolute top-0.5 right-0.5 transition-all";
    } else {
        btn.className = "w-8 h-4 bg-zinc-800 rounded-full relative transition-colors";
        ball.className = "w-3 h-3 bg-zinc-500 rounded-full absolute top-0.5 left-0.5 transition-all";
    }
}

async function sendAction(actionName) {
    showToast(`Macro ${actionName.toUpperCase()} executada.`);
}

async function saveConfigurations() {
    showToast("Configuração salva (SAVE_CONFIG).");
}

async function setStirringSpeed(spd) {
    showToast(`Velocidade ajustada: ${spd}`);
}

function updateDashboardTempGrid(state) {
    const container = document.getElementById('dashboard-temp-grid');
    container.innerHTML = '';
    for (let i = 0; i < 6; i++) {
        const pv = state.temperatures[i];
        const sv = state.setpoints[i];
        const on = state.heaters_on[i];
        const fault = state.faults[i];

        const card = document.createElement('div');
        card.className = `bg-zinc-950 p-2 rounded border ${on && !fault ? 'border-brand-green/30' : 'border-zinc-800'} flex flex-col justify-between`;
        card.innerHTML = `
            <div class="flex justify-between items-center mb-1">
                <span class="text-[9px] text-zinc-500 font-bold uppercase">H${i + 1}</span>
                <i class="fa-solid fa-fire text-[10px] ${fault ? 'text-brand-red' : (on ? 'text-brand-orange animate-pulse' : 'text-zinc-700')}"></i>
            </div>
            <div class="code-font font-bold text-sm ${fault ? 'text-brand-red' : 'text-zinc-200'}">
                ${fault ? 'orAL' : pv.toFixed(1) + '°C'}
            </div>
            <div class="text-[9px] text-zinc-500 mt-0.5 font-mono">T: ${sv}°C</div>
        `;
        container.appendChild(card);
    }
}

function renderThermalMatrix() {
    const container = document.getElementById('beakers-thermal-matrix');
    if (container.children.length === 0) {
        for (let i = 0; i < 6; i++) {
            const el = document.createElement('div');
            el.className = "panel";
            el.id = 'thermal-station-card-' + i;
            container.appendChild(el);
        }
    }
    updateThermalValues();
}

async function updateThermalValues() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        const state = data.state;

        for (let i = 0; i < 6; i++) {
            const card = document.getElementById('thermal-station-card-' + i);
            if (!card) continue;
            
            const pv = state.temperatures[i];
            const sv = state.setpoints[i];
            const on = state.heaters_on[i];
            const fault = state.faults[i];

            card.innerHTML = `
                <div class="panel-header">
                    <span>Heater ${i + 1}</span>
                    <span class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${fault ? 'bg-brand-red/10 text-brand-red border border-brand-red/20' : 'bg-zinc-800 text-zinc-400'}">
                        ${fault ? 'Fault (orAL)' : 'Ready'}
                    </span>
                </div>
                
                <div class="panel-body flex flex-col gap-4">
                    <div class="flex gap-4">
                        <div class="flex-1">
                            <span class="text-[10px] text-zinc-500 block uppercase font-semibold">Atual (PV)</span>
                            <span class="text-xl font-bold code-font ${fault ? 'text-brand-red' : 'text-zinc-200'}">
                                ${fault ? 'orAL' : pv.toFixed(1) + ' °C'}
                            </span>
                        </div>
                        <div class="w-px bg-zinc-800"></div>
                        <div class="flex-1">
                            <span class="text-[10px] text-zinc-500 block uppercase font-semibold">Alvo (SV)</span>
                            <input type="number" onchange="setHeatTarget(${i}, this.value)" value="${sv}" class="w-full bg-transparent text-xl font-bold code-font text-brand-blue focus:outline-none placeholder-zinc-700">
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-2 mt-auto">
                        <button onclick="triggerPIDTune(${i})" class="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 py-1.5 rounded text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors">
                            PID Tune
                        </button>
                        <button onclick="toggleHeater(${i}, ${!on})" class="py-1.5 rounded text-xs font-bold flex items-center justify-center gap-1.5 transition-colors ${on ? 'bg-brand-red/10 text-brand-red hover:bg-brand-red hover:text-white border border-brand-red/20' : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700'}">
                            <i class="fa-solid fa-power-off"></i> ${on ? 'OFF' : 'ON'}
                        </button>
                    </div>
                </div>
            `;
        }
    } catch(e) {}
}

async function updateDiagnosticLEDs(state) {
    const bar = document.getElementById('fault-leds-bar');
    bar.innerHTML = '';
    for (let i = 0; i < 6; i++) {
        const f = state.faults[i];
        const el = document.createElement('div');
        el.className = "flex flex-col items-center gap-1";
        el.innerHTML = `
            <span class="text-[8px] text-zinc-500 font-mono">H${i + 1}</span>
            <span class="w-2.5 h-2.5 rounded-full ${f ? 'bg-brand-red shadow-[0_0_8px_rgba(239,68,68,0.8)]' : 'bg-zinc-700'}"></span>
        `;
        bar.appendChild(el);
    }
}

async function loadRecipesList() {
    const list = document.getElementById('recipes-list');
    list.innerHTML = `
        <div class="bg-zinc-950 p-2 rounded border border-zinc-800 flex items-center justify-between">
            <span class="text-[11px] font-mono text-zinc-300">Macro_Default.cfg</span>
            <button class="text-xs text-zinc-400 hover:text-brand-blue font-bold px-2 py-1"><i class="fa-solid fa-download"></i></button>
        </div>
    `;
}

// Inicializações Automáticas
renderMixingToggles();
renderThermalMatrix();