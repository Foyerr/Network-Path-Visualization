from flask import Flask, render_template_string
import matplotlib.pyplot as plt
import networkx as nx
import io
import base64
import os
import time
import threading
import pydot
from networkx.drawing.nx_pydot import graphviz_layout
from collections import Counter
import logging


app = Flask(__name__)
data_file_path = 'Path to SolarWinds TracerouteNG log'
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
        time.sleep(5)  # Check every 5 seconds



@app.route('/')
def index():
    if not parsed_data:
        parse_log_file()

    G = nx.DiGraph()
    
    hopCompare = {}
    ipCompare = []
    lastIP = None
    prevHopCount = 0

    # Add nodes and edges based on the data
    for i, d in enumerate(parsed_data[:-1]):
        if d is None:
            continue
        label = f"{d['ip']} ({d['latency']} ms)"
        hopCount = d['hop']
        ip = f'"{d["ip"]}"'


        if(ip not in ipCompare):
            G.add_node(ip, label=label)
            ipCompare.append(ip)
            
        if lastIP is not None:
                if hopCount > prevHopCount: 
                    G.add_edge(lastIP, ip)
                

        lastIP = ip
        prevHopCount = hopCount

    
    pos = graphviz_layout(G, prog="dot",root=0)

    # Draw the graph
    plt.figure(figsize=(10, 8))
    nx.draw(G, pos, node_size=3000, node_color='lightgreen', edge_color='gray')
    nx.draw_networkx_labels(G, pos, labels=nx.get_node_attributes(G, 'label'), font_size=9)

    # Convert plot to PNG image
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    # Render the image in the HTML template
    html = '''
    <html>
    <body>
        <h1>Network Latency Visualization</h1>
        <img src="data:image/png;base64,{{image}}" />
        <meta http-equiv="refresh" content="10">
    </body>
    </html>
    '''
    return render_template_string(html, image=image_base64)

if __name__ == '__main__':
    threading.Thread(target=monitor_file_changes, daemon=True).start()
    app.run(debug=True)
