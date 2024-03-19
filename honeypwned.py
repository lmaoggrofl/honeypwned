import configparser
import logging
import threading
import sys
from socket import socket, timeout
from flask import Flask, render_template, send_from_directory
import os
import paramiko
import datetime

# Global Variable
BIND_IP = '0.0.0.0'
config_filepath = 'honeypwned.ini'
ssh_port = 22  # Default SSH port

def handle_client(client_socket, port, ip, remote_port):
    current_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%f")[:-3]
    logger.info("[%s] Connection Received on port: %s from %s:%d " % (current_time, port, ip, remote_port))
    client_socket.settimeout(4)
    try:
        data = client_socket.recv(64)
        logger.info("[%s] Data received on port: %s from %s:%d - %s" % (current_time, port, ip, remote_port, data))
        client_socket.send("Access Denied.\n".encode('utf8'))
    except timeout:
        pass
    except ConnectionResetError as e:
        logger.error("[%s] Connection Reset Error occurred" % current_time)
    client_socket.close()

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

def generate_or_read_ssh_key():
    key_folder = 'Files'
    key_path = os.path.join(key_folder, 'ssh_key')
    if not os.path.exists(key_path):
        # Generate SSH key if not exists
        key = paramiko.RSAKey.generate(2048)
        key.write_private_key_file(key_path)
    else:
        # Read SSH key
        key = paramiko.RSAKey(filename=key_path)
    return key

class SSHServer(paramiko.ServerInterface):
    def check_auth_password(self, username: str, password: str) -> int:
        current_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%f")[:-3]
        logger.info('[%s] SSH login attempts - %s %s' % (current_time, username, password))
        return paramiko.AUTH_FAILED

def start_ssh_server():
    global ssh_port
    ssh_key = generate_or_read_ssh_key()

    server_socket = socket()
    server_socket.bind((BIND_IP, ssh_port))
    server_socket.listen(5)

    while True:
        client, addr = server_socket.accept()
        current_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%f")[:-3]
        logger.info('[%s] Connection Received on port: 22 from: %s:%d' % (current_time, addr[0], addr[1]))
        
        try:
            transport = paramiko.Transport(client)
            transport.add_server_key(ssh_key)
            server = SSHServer()
            transport.start_server(server=server)
        except Exception as e:
            pass

logging.getLogger("paramiko").setLevel(logging.CRITICAL)

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

# Start SSH server if SSH port is configured
if '22' in ports_list:
    ports_list.remove('22')
    ssh_thread = threading.Thread(target=start_ssh_server)
    ssh_thread.start()

# Check if port 80 is in the ports list
if '80' in ports_list:
    ports_list.remove('80')
    flask_thread = threading.Thread(target=start_flask_server)
    flask_thread.start()

# Start listener threads for other ports
for port in ports_list:
    listeners_thread[port] = threading.Thread(target=start_new_listener_thread, args=(port,))
    listeners_thread[port].start()
