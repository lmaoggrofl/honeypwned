import configparser
import logging
import threading
import sys
from socket import socket, timeout
from flask import Flask, render_template, send_from_directory
import os
from ipwhois import IPWhois
from ipaddress import ip_address, ip_network

def handle_client(client_socket, port, ip, remote_port):
    is_vpn = check_vpn(ip)
    if is_vpn:
        vpnstring = "[VPN]"
    else:
        vpnstring = ""
    logger.info("Connection Received on port: %s from %s:%d %s" % (port, ip, remote_port, vpnstring))
    client_socket.settimeout(4)
    try:
        data = client_socket.recv(64)
        logger.info("Data received: %s from %s:%d - %s %s" % (port, ip, remote_port, data, vpnstring))
        client_socket.send("Access Denied.\n".encode('utf8'))

        is_vpn = check_vpn(ip)
        if is_vpn:
            vpnstring = "[VPN]"
        else:
            vpnstring = ""
    except timeout:
        pass
    except ConnectionResetError as e:
        logger.error("Connection Reset Error occurred")
    client_socket.close()

def check_vpn(ip):
    private_ip_ranges = [
        ip_network('10.0.0.0/8'),           # Class A private network
        ip_network('172.16.0.0/12'),        # Class B private network
        ip_network('192.168.0.0/16'),       # Class C private network
    ]
    
    # Loopback address
    loopback_address = '127.0.0.1'

    # Check if the IP is in the private IP ranges or loopback address
    if ip == loopback_address:
        return False  # Skip VPN check for loopback address
    
    for private_range in private_ip_ranges:
        if ip_address(ip) in private_range:
            return False  # Skip VPN check for private IP addresses

    try:
        obj = IPWhois(ip)
        result = obj.lookup_whois()
        # Check if the IP is associated with a VPN service
        if 'vp' in result['nets'][0]['description'].lower():
            return True
    except Exception as e:
        logger.error(f"Error checking VPN for IP {ip}: {str(e)}")
    return False

def start_new_listener_thread(port):
    listener = socket()
    listener.bind((BIND_IP, int(port)))
    listener.listen(5)

    while True:
        client, addr = listener.accept()
        client_handler = threading.Thread(target=handle_client, args=(client, port, addr[0], addr[1]))
        client_handler.start()

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname) -8s %(message)s', datefmt='%Y-%m-%d %H:%M:%s', filename=logfile, filemode='w')
    logger = logging.getLogger('')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    return logger

def get_files():
    # Specify the directory where your files are stored
    directory = 'static'
    # Get the list of files in the directory
    files = os.listdir(directory)
    # Return the list of files
    return files

def start_flask_server():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return render_template('index.html')

    # Define route for the download page
    @app.route('/download')
    def download_page():
        # Define the directory path
        directory = os.path.join(app.root_path, 'static', 'tools')
        # Get the list of files in the directory
        files = os.listdir(directory)
        # Render the download page template and pass the list of files
        return render_template('download.html', files=files)

    # Route to serve files for download
    @app.route('/download/<path:filename>')
    def download_file(filename):
        # Specify the directory where your files are stored
        directory = os.path.join('static', 'tools')
        # Return the requested file for download
        return send_from_directory(directory, filename, as_attachment=True)

    # Define route for the documents page
    @app.route('/document')
    def document_page():
        # Define the directory path
        directory = os.path.join(app.root_path, 'static', 'document')
        # Get the list of files in the directory
        files = os.listdir(directory)
        # Render the download page template and pass the list of files
        return render_template('document.html', files=files)
    
        # Route to serve files for download
    @app.route('/document/<path:filename>')
    def download_document(filename):
        # Specify the directory where your files are stored
        directory = os.path.join('static', 'document')
        # Return the requested file for download
        return send_from_directory(directory, filename, as_attachment=True)

    app.run(host='0.0.0.0', port=80)

BIND_IP = '0.0.0.0'
config_filepath = 'honeypwned.ini'

config = configparser.ConfigParser()
config.read(config_filepath)

ports = config.get('default', 'ports', raw=True, fallback="22,80,443,8080,8888,9999")
logfile = config.get('default', 'logfile', raw=True, fallback="honeypwned.log")
logger = setup_logging()


print("[*] Ports: %s" % ports)
print("[*] Logfile: %s" % logfile)

ports_list = []
listeners_thread = {}

# Try splitting the ports
try:
    ports_list = ports.split(',')
except Exception as e:
    print('[!] Error getting ports: %s', ports)
    sys.exit(1)

# Check if there are any ports provided in ini file
if len(ports) < 1:
    print('[!] No ports provided.')
    sys.exit(1)

# Check if port 80 is in the ports list
if '80' in ports_list:
    ports_list.remove('80')
    flask_thread = threading.Thread(target=start_flask_server)
    flask_thread.start()

# Start listener threads for other ports
for port in ports_list:
    listeners_thread[port] = threading.Thread(target=start_new_listener_thread, args=(port,))
    listeners_thread[port].start()
