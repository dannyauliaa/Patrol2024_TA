import time 
import serial 
import json 
import os 
import cv2 
import base64 
import firebase_admin 
from firebase_admin import credentials, firestore, storage 
import schedule 

# Initialize Firebase Admin SDK with your service account key file 
cred = credentials.Certificate("/Users/andikanaufan/Documents/Telyutizen/Kuliah/Semester 8/TA/json/ta-obstac
map-firebase-adminsdk-l434r-d869dd41ad.json") 
firebase_admin.initialize_app(cred, { 
    'storageBucket': 'ta-obstac-map.appspot.com', 
    'databaseURL': 'https://console.firebase.google.com/u/0/project/ta-obstac-map/firestore/databases/-default
/data' 
}) 

# Retrieve the default app 
app = firebase_admin.get_app() 

# Initialize Firestore database 
db = firestore.client() 

def save_to_json(data, condition, latitude, longitude, image_path=None): 
    # Define the filename based on the condition 
    filename = f"{condition.replace(' ', '_').lower()}_data.json" 
    # Add latitude and longitude to the data dictionary 
    data["latitude"] = latitude 
    data["longitude"] = longitude 
    # Add image path if available 
    if image_path: 
    data["image_path"] = image_path 
    try: 

    # Check if the file already exists 
    if os.path.isfile(filename): 
        # Open the file in read mode to load existing data 
        with open(filename, "r") as json_file: 
                # Load existing JSON data 
                existing_data = json.load(json_file) 
            # Append new data to existing data 
            existing_data.append(data) 
            # Write all data back to the file 
            with open(filename, "w") as json_file: 
                json.dump(existing_data, json_file, indent=4) 
        else: 
            # Create a new JSON file and write the first data entry 
            with open(filename, "w") as json_file: 
                json.dump([data], json_file, indent=4) 
    except Exception as e: 
        print("Failed to save data to JSON file:", e) 
 
def get_latest_image_number(): 
    try: 
        # Check the latest image number in the JSON files 
        latest_number = 0 
        for filename in os.listdir(): 
            if filename.startswith("Kerusakan_B") and filename.endswith("_data.json"): 
                number = int(filename.split("_")[1]) 
                if number > latest_number: 
                    latest_number = number 
        return latest_number 
    except Exception as e: 
        print("Failed to get the latest image number:", e) 
        return None 
 
def dms_to_dd(dms): 
    if not dms: 
        print("Input DMS value is empty") 
        return 0.0 
     
    negative = True if dms.endswith('S') or dms.endswith('W') else False 
    degrees, minutes = divmod(float(dms[:-1]), 100) 
    dd = degrees + minutes / 60 
    # Apply negative sign if needed 
    dd = -dd if negative else dd 
    return dd 
 
def read_gps_data(portGPS): 
    try: 
        # Open serial port 
        with serial.Serial(portGPS, 9600, timeout=1) as ser: 
            # Read and decode GPS data 
            while True: 
                line = ser.readline().decode('utf-8').strip() 
                if line.startswith('$GPGGA'): 
                    # Split the GPGGA sentence into fields 
                    fields = line.split(',') 
                    # Extract latitude and longitude 
                    latitude_dms = fields[2] + fields[3] 
                    longitude_dms = fields[4] + fields[5] 
                    # Convert DMS to DD 
                    latitude_dd = dms_to_dd(latitude_dms) 
                    longitude_dd = dms_to_dd(longitude_dms) 
                    return latitude_dd, longitude_dd 
    except Exception as e: 
        print("Failed to read GPS data:", e) 
        return 0, 0 
 
def capture_image(condition): 
    try: 
        # Get the latest image number 
        latest_number = get_latest_image_number() + 1 if get_latest_image_number() else 1 
         
        # Open the camera 
        cap = cv2.VideoCapture(0) 
 
        # Set camera properties to increase brightness and exposure 
        cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.8)  # Adjust brightness (0.0 - 1.0) 
        cap.set(cv2.CAP_PROP_EXPOSURE, 0.5)    # Adjust exposure (-7.0 - 7.0) 
 
        # Delay for 3 seconds 
        time.sleep(3) 
 
        # Capture a frame 
        ret, frame = cap.read() 
        # Define the filename 
        filename = f"Kerusakan_B{latest_number}.jpg" 
        # Save the image 
        cv2.imwrite(filename, frame) 
        print("Image captured for", condition) 
        # Release the camera 
        cap.release() 
         
        # Convert the image to base64 
        with open(filename, "rb") as image_file: 
            base64_data = base64.b64encode(image_file.read()).decode("utf-8") 
 
        return base64_data 
    except Exception as e: 
        print("Failed to capture image:", e) 
        return None 
 
def read_accelerometer_data(port, portGPS): 
    read_time = 0  # Variable to track the time elapsed while reading accelerometer data 
    reading_flag = True  # Flag to control the reading process 
 
    try: 
        # Open serial port for accelerometer 
        with serial.Serial(port, 9600, timeout=1) as ser_accelerometer: 
            # Open serial port for GPS 
            with serial.Serial(portGPS, 9600, timeout=1) as ser_gps: 
                start_time = time.time()  # Record the start time 
 
                while reading_flag: 
                    # Check if 20 seconds have elapsed 
                    elapsed_time = time.time() - start_time 
                    if elapsed_time >= 300: 
                        reading_flag = False 
                        break 
 
                    # Read data from Arduino - Accelerometer 
                    line_accelerometer = ser_accelerometer.readline().decode('utf-8').strip() 
                    print("Arduino output (Accelerometer):", line_accelerometer) 
 
                    # Split the line to extract condition and sensor data 
                    parts = line_accelerometer.split(";") 
                    if len(parts) >= 2:  # Ensure there are at least two parts 
                        condition = parts[0].strip() 
                        sensor_data = parts[1].strip().split(",")  # Split sensor data by comma 
 
                        if len(sensor_data) >= 3:  # Ensure there are at least three sensor readings 
                            # Create a dictionary with keys "sumbu X", "sumbu Y", and "sumbu Z" 
                            accelerometer_data = { 
                                "sumbu X": int(sensor_data[0].split(":")[1].strip()), 
                                "sumbu Y": int(sensor_data[1].split(":")[1].strip()), 
                                "sumbu Z": int(sensor_data[2].split(":")[1].strip()) 
                            } 
                            # Read GPS data 
                            latitude, longitude = read_gps_data(portGPS) 
                            # Capture image if condition is "Kerusakan Besar" 
                            image_path = None 
                            if condition.lower() == "kerusakan besar": 
                                image_path = capture_image(condition) 
                            # Save the accelerometer data to a JSON file based on condition 
                            save_to_json(accelerometer_data, condition, latitude, longitude, image_path) 
                            print("Data saved to JSON file.") 
 
                    # Add a delay of 500 milliseconds 
                    time.sleep(0.5) 
 
    except serial.SerialException as se: 
        print("Serial communication error:", se) 
    except Exception as e: 
print("Failed to read Arduino data:", e) 

def send_location_to_firestore_KN(latitude, longitude, path, document_id): 
    data = { 
        'latitude': latitude, 
        'longitude': longitude 
    } 
    doc_ref = db.collection(*path).document(document_id) 
    doc_ref.set(data) 

def send_data_to_firestore_KN(): 
    print("Sending data to Firestore for Kerusakan Null") 
    # Read JSON file containing the data 
    with open("kondisi_null_data.json", 'r') as json_file: 
        kondisi_null_data = json.load(json_file) 

    # Loop through each data entry 
    for i, data_entry in enumerate(kondisi_null_data, 1): 
        # Retrieve latitude, longitude from the entry 
        latitude = data_entry.get('latitude') 
        longitude = data_entry.get('longitude') 

        # Generate the path with an incremented index 
        path = ("Kerusakan Null",) 
        document_id = f"Kerusakan_N{i}" 

        # Send latitude, longitude to Firestore 
        send_location_to_firestore_KN(latitude, longitude, path, document_id) 

def send_location_to_firestore_KR(latitude, longitude, path, document_id): 
    data = { 
        'latitude': latitude, 
        'longitude': longitude  
    } 
    doc_ref = db.collection(*path).document(document_id) 
    doc_ref.set(data) 

def send_data_to_firestore_KR(): 
    print("Sending data to Firestore for Kerusakan Ringan") 
    # Read JSON file containing the data 
    with open("kerusakan_kecil_data.json", 'r') as json_file: 
        kondisi_null_data = json.load(json_file) 

    # Loop through each data entry 
    for i, data_entry in enumerate(kondisi_null_data, 1): 
        # Retrieve latitude, longitude from the entry 
        latitude = data_entry.get('latitude') 
        longitude = data_entry.get('longitude') 
        # Generate the path with an incremented index 
        path = ("Kerusakan Ringan",) 
        document_id = f"Kerusakan_R{i}" 

        # Send latitude, longitude to Firestore 
        send_location_to_firestore_KR(latitude, longitude, path, document_id) 

def send_location_to_firestore_KB(latitude, longitude, image_url, path, document_id): 
    data = { 
        'latitude': latitude, 
        'longitude': longitude, 
        'image_url': image_url 
    } 
    doc_ref = db.collection(*path).document(document_id) 
    doc_ref.set(data) 

def send_data_to_firestore_KB(): 
    print("Sending data to Firestore for Kerusakan Besar") 
    # Read JSON file containing the data 
    with open("kerusakan_besar_data.json", 'r') as json_file: 
        kondisi_null_data = json.load(json_file) 

    # Loop through each data entry 
    for i, data_entry in enumerate(kondisi_null_data, 1): 
        # Retrieve latitude, longitude, and image from the entry 
        latitude = data_entry.get('latitude') 
        longitude = data_entry.get('longitude') 
        image_base64 = data_entry.get('image_path') 

        # Convert base64 image data to bytes 
        image_data = base64_to_image_data(image_base64) 
        # Generate the path with an incremented index 
        path = ("Kerusakan Besar",) 
        document_id = f"Kerusakan_B{i}" 
        # Upload image to Firebase Storage and get public URL 
        image_url = upload_image_to_storage(image_data, *path, document_id) 
        # Send latitude, longitude, and image URL to Firestore 
        send_location_to_firestore_KB(latitude, longitude, image_url, path, document_id) 

def upload_image_to_storage(image_data, document_path, document_id): 
    bucket = storage.bucket() 
    image_path = f"{document_path}/{document_id}.jpg"  
    blob = bucket.blob(image_path) 
    blob.upload_from_string(image_data, content_type='image/jpeg') 
    return blob.public_url 

def base64_to_image_data(base64_string): 
    # Remove the base64 encoding prefix if it exists 
    if base64_string.startswith("data:image/jpeg;base64,"): 
        base64_string = base64_string.replace("data:image/jpeg;base64,", "") 
    # Convert base64 string to bytes 
    image_data = base64.b64decode(base64_string) 
    return image_data 

def main(): 
    print("Current Directory:", os.getcwd()) 
    port = '/dev/tty.usbserial-142440'   
    portGPS = '/dev/tty.usbmodem142301' 
    
    start_time = time.time()  # Record the start time 

    while True: 
        elapsed_time = time.time() - start_time  # Calculate elapsed time 
        # Read accelerometer data for 20 seconds 
        read_accelerometer_data(port, portGPS) 
        # Send data to Firestore 
        send_data_to_firestore_KN() 
        send_data_to_firestore_KR() 
        send_data_to_firestore_KB() 
        # Check if 20 seconds have elapsed 
        if elapsed_time >= 1: 
            start_time = time.time()  # Reset the start time 

    # Sleep for 1 second before checking again 
    time.sleep(1) 

if __name__ == '__main__': 
    main()