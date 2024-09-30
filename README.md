# Network Trace Visualization Tool

A Flask web application that monitors a log file, parses network trace data, and visualizes the network path using an interactive graph. The application leverages NetworkX and PyVis to create a dynamic network graph that updates in real-time as the log file changes.

## Features

- Monitors a [TraceRouteNG](https://www.solarwinds.com/free-tools/traceroute-ng) log file for changes.
- Parses network trace data from the log file.
- Visualizes the network path as an interactive directed graph.
- Allows users to save node positions for consistent visualization.
- Displays latency information between nodes.
- Refreshes data in real-time as the log file updates.

## Prerequisites

- Python 3.6 or higher
- Pip (Python package manager)
- Flask 
- Networkx
- Pyvis


![image](https://github.com/user-attachments/assets/6d9fc066-f70b-44f5-9a69-b2d7743d28ae)
