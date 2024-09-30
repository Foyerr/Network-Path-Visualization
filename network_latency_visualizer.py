from flask import Flask, render_template_string, request
import networkx as nx
import os
import time
import threading
import json
from pyvis.network import Network

app = Flask(__name__)
data_file_path = r'logpath'
parsed_data = []


def parse_log_file():
    global parsed_data
    with open(data_file_path, 'r') as file:
        parsed_data = []
        for line in file.readlines():
            if '|' in line and 'Hop' not in line:
                try:
                    parts = line.split('|')
                    hop = int(parts[0].strip())
                    ip = parts[1].strip()
                    domain = parts[2].strip()
                    latency = parts[5].strip()
                    if hop == '?':
                        continue
                    elif latency:
                        parsed_data.append({"hop": hop, "ip": ip, "domain": domain, "latency": float(latency)})
                    else:
                        parsed_data.append({"hop": hop, "ip": ip, "domain": domain, "latency": None})
                except:
                    continue


def monitor_file_changes():
    last_modified_time = 0
    while True:
        try:
            current_modified_time = os.path.getmtime(data_file_path)
            if current_modified_time != last_modified_time:
                last_modified_time = current_modified_time
                parse_log_file()
        except FileNotFoundError:
            pass
        time.sleep(5)


@app.route('/')
def index():
    if not parsed_data:
        parse_log_file()

    if not parsed_data:
        return "No data available."

    G = nx.DiGraph()

    hopCompare = {}
    ipCompare = []
    lastIP = None
    prevHopCount = 0

    # Add nodes and edges based on the data
    for i, d in enumerate(parsed_data):
        if d is None:
            continue
        label = f"{d['ip']} ({d['latency']} ms)"
        hopCount = d['hop']
        ip = d["ip"]

        if ip not in ipCompare:
            G.add_node(ip, label=label, title=f"IP: {d['ip']}<br>Latency: {d['latency']} ms")
            ipCompare.append(ip)

        if lastIP is not None:
            if hopCount > prevHopCount:
                G.add_edge(lastIP, ip)

        lastIP = ip
        prevHopCount = hopCount

    net = Network(height='750px', width='100%', directed=True)
    net.from_nx(G)
    net.show_buttons(filter_=['physics'])

    positions_file_path = 'positions.json'

    if os.path.exists(positions_file_path):
        with open(positions_file_path, 'r') as f:
            positions = json.load(f)
        # Set positions in net.nodes
        for node in net.nodes:
            node_id = node['id']
            if node_id in positions:
                node['x'] = positions[node_id]['x']
                node['y'] = positions[node_id]['y']

    # Generate the HTML content
    html_content = net.generate_html()

    # Insert JavaScript to send positions to server after stabilization
    js_code = '''
        <script type="text/javascript">
            // Add a button to the document
            var saveButton = document.createElement('button');
            saveButton.innerHTML = 'Save Positions';
            document.body.appendChild(saveButton);

            // Add an event listener to the button for saving positions
            saveButton.addEventListener('click', function () {
                var positions = network.getPositions();
                
                // Send the positions to the server via fetch
                fetch('/save_positions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(positions)
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Success:', data);
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
            });
        </script>
        </body>
    '''

    # Replace </body> with js_code
    html_content = html_content.replace('</body>', js_code)

    # Insert meta refresh tag to refresh the page every 10 seconds
    # html_content = html_content.replace(
    #     '</head>',
    #     '<meta http-equiv="refresh" content="10">\n</head>'
    # )

    # Insert the header with start and end IPs
    ips = [d['ip'] for d in parsed_data if d is not None]
    start_ip = ips[0]
    end_ip = ips[-1]

    html_content = html_content.replace('<div id="mynetwork">', f'<h1>{start_ip} -> {end_ip}</h1>\n<div id="mynetwork">')
    return render_template_string(html_content)


@app.route('/save_positions', methods=['POST'])
def save_positions():
    positions = request.get_json()
    positions_file_path = 'positions.json'
    with open(positions_file_path, 'w') as f:
        json.dump(positions, f)
    return 'OK'


if __name__ == '__main__':
    threading.Thread(target=monitor_file_changes, daemon=True).start()
    app.run(debug=True)
