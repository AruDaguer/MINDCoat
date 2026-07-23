from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Rota principal que renderiza a interface
@app.route('/')
def index():
    return render_template('index.html')

# Mocks das APIs para o painel não dar erro de "Offline"
@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "state": {
            "z_position": 12.5,
            "dwell_countdown": 5,
            "dry_countdown": 0.0,
            "current_cycle": 1,
            "status_message": "Idle",
            "up_limit": False,
            "down_limit": False,
            "stirring_speed": "OFF",
            "mixing_status": [False, False, False, False, False, False],
            "temperatures": [25.0, 24.8, 25.1, 24.9, 25.0, 25.2],
            "setpoints": [0, 0, 0, 0, 0, 0],
            "heaters_on": [False, False, False, False, False, False],
            "faults": [False, False, False, False, False, False]
        },
        "config": {
            "travel": 150.0,
            "up_speed": 300,
            "down_speed": 300,
            "dwell_time": 10,
            "dry_time": 5,
            "dip_times": 3,
            "working_position": 1
        }
    })

@app.route('/api/control', methods=['POST'])
def control():
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)