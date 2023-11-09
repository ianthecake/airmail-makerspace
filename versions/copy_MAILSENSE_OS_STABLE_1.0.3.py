import smtplib
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
from PIL import Image
import pytesseract
import re
import cv2
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QHeaderView, QSizePolicy, QScrollArea, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from gpiozero import LED, Button
from signal import pause
import threading
import os
import time
import datetime
import schedule

#from time import sleep, time
#from pynput import mouse



### EMAIL SYSTEM
email_address = 'airmail.notify@gmail.com'
password = 'nuuz freu rukr yzdp'


def get_contacts_by_name(filename, letter_name):
    contact_dict = {}
    with open(filename, mode='r', encoding='utf-8') as contactsFile:
        for line in contactsFile:
            # Split each line into parts (assuming each line is in the format: firstname surname email)
            parts = line.strip().split()

            if len(parts) >= 5:  # Check if the line contains at least three elements
                first_name = parts[0]
                surname = parts[1]
                email = parts[2]

                real_fn = parts[3]
                real_ln = parts[4]

                # Create a key (a tuple containing first name and surname) and assign the email as the value
                key = (first_name, surname, real_fn, real_ln)
                contact_dict[key] = email

    # Iterate through the dictionary to find a match for the given name
    email_to_name = None
    email_address = None
    # Initialize these variables to None
    get_firstname = None
    get_lastname = None
    get_real_fn = None
    get_real_ln = None

    for key, value in contact_dict.items():
        if f"{key[0]} {key[1]}" == letter_name:
            email_to_name = letter_name
            get_firstname = key[0]
            get_lastname = key[1]
            get_real_fn = key[2]
            get_real_ln = key[3]
            email_address = value
            break  # Exit the loop once a match is found

    return get_firstname, get_lastname, get_real_fn, get_real_ln, email_address


def readTemplate(filename):
    with open(filename, 'r', encoding='utf-8') as templateFile:
        templateFileNachricht = templateFile.read()
    return Template(templateFileNachricht)


def get_datetime():
    # Get the current date and time
    current_datetime = datetime.datetime.now()

    # Format it as a string in the desired format
    am_pm = str(current_datetime.strftime('%p'))
    print(am_pm)

    current_datetime_str = f'{current_datetime.strftime("%B %d, 20%y %I:%M")}'
    return f'{current_datetime_str} {am_pm}'


# FUNCTION: EMAIL_SYSTEM
def run_ocr_and_send_email(window):
    ## OCR
    letter_name = None
    letter_department = None

    cv2.imwrite("png/captured_image.png", window.last_image)
    filename = '/home/pi/Desktop/HandwritingDetection/Project/png/captured_image.png'
    img = Image.open(filename)
    text = pytesseract.image_to_string(img)

    # Unwanted words:
    unwanted_words = ['drive', 'street', 'way', 'avenue', 'straße', 'strasse', 'str.',
                      'willy-messerschmitt', 'willy-messerschmidt' 'willy',
                      'messerschmitt', 'messerschmidt', 'airbus', 'defence', 'space', 'münchen', 'zeichen', 'unser',
                      'ausbildung', 'and', 'to', 'zu', 'händen', 'ottobrunn', 'ottobrun', 'taufkirchen', 'abteilung',
                      'department']

    # List of all recognized names from the letter envelope (extract_names() function)
    names, departments = extract_names(text)

    # Filtering out names containing the unwanted words (street names etc)
    filtered_names = filter_names(names, unwanted_words)

    # Print the recognized and filtered name & department code
    for name in filtered_names:
        print(f'To: {name}')
        letter_name = name
        print(letter_name)

    for department in departments:
        print(f'Department: {department}')
        letter_department = department

    ## EMAIL
    firstname, surname, real_firstname, real_lastname, email = get_contacts_by_name('files_email/contacts.txt', letter_name)
    #contact_for_message = [firstname, surname, email]
    contact_for_message = [real_firstname, real_lastname, email]
    messageTemplate = readTemplate('files_email/message.txt')

    print(f'Firstname: {firstname}, Surname: {surname}, Email: {email}')

    try:
        s = smtplib.SMTP(host='smtp.gmail.com', port=587)
        s.starttls()
        s.login(email_address, password)

        msg = MIMEMultipart()
        full_name = f'{contact_for_message[0]} {contact_for_message[1]}'
        message = messageTemplate.substitute(CONTACT_NAME=full_name.title(), DATETIME_STRING=get_datetime().title())

        msg['From'] = email_address
        msg['To'] = email
        msg['Subject'] = "THERE'S A NEW LETTER IN YOUR MAILBOX!"
        msg.attach(MIMEText(message, 'plain'))
        print(msg)

        s.send_message(msg)
        del msg
        s.quit()

    except smtplib.SMTPRecipientsRefused as e:
        print("SMTPRecipientsRefused error:", e.recipients)
    except Exception as e:
        print("An error occurred:", str(e))


### OCR IMAGE CAPTURING


def get_camera_image():
    # Open a connection to the default camera (usually the built-in webcam)
    cap = cv2.VideoCapture(0)

    # Check if the camera opened successfully
    if not cap.isOpened():
        print("Error: Could not access the webcam.")
    else:
        # Read a single frame from the camera
        ret, frame = cap.read()

        if ret:
            # Save the captured frame as a JPEG image
            cv2.imwrite("png/captured_image.png", frame)
            print("Image captured and saved as 'captured_image.png'")
        else:
            print("Error: Could not capture an image.")

        # Release the camera when done
        cap.release()

    # Close any OpenCV windows that may have opened
    cv2.destroyAllWindows()


# Extract names from OCR text
def extract_names(text):
    # Define a list of regular expression patterns for names
    name_patterns = [
        r"[A-Z][a-zA-Z-'’]+ [A-Z][a-zA-Z-'’]+",  # First letter of surname and name capitalized
        r"[A-Z][a-zA-Z-'’]+ [A-Z][a-zA-Z-'’]+"  # Each letter of surname and name capitalized
    ]

    # REGEX for Airbus-department codes
    # department_code_pattern = r'^[A-Z0-9-]{3,10}$'
    departments_list = ['THGO-TL1', 'TDA']

    # Initialize a list to store all matching names
    names = []
    departments = []
    # Find matching names for each pattern in name_patterns
    for pattern in name_patterns:
        names.extend(re.findall(pattern, text))

    for department in departments_list:
        departments.extend(re.findall(department, text))

    # Remove duplicates (converting the list to a unique set and back to a list)
    unique_names = list(set(names))
    unique_departments = list(set(departments))

    return unique_names, unique_departments


# Function to filter out names containing unwanted words
def filter_names(names, unwanted_words):
    filtered_names = []
    for name in names:
        # Check if the name contains any unwanted words
        if not any(word in name.lower() for word in unwanted_words):
            filtered_names.append(name)
    return filtered_names





### PYQT
## Main Window Screen
class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Camera Feed and Email System Example")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.admin_button = QPushButton("Add Recipient manually")
        self.layout.addWidget(self.admin_button)

        self.email_button = QPushButton("Run Email System")
        self.layout.addWidget(self.email_button)

        self.settings_button = QPushButton('Settings')
        self.layout.addWidget((self.settings_button))

        self.label = QLabel(self)
        self.layout.addWidget(self.label)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.admin_button.clicked.connect(self.run_adminstrators)
        self.email_button.clicked.connect(self.run_ocr_and_send_email)
        self.settings_button.clicked.connect(self.run_settings)


        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera_feed)

        self.start_camera_feed()


    def start_camera_feed(self):
        if not self.cap:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
            self.timer.start(30)  # Update every 30 milliseconds
    
    def update_camera_feed(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Convert OpenCV BGR image to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to QImage
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

                # Store the last image
                self.last_image = rgb_frame  # Store the RGB frame

                # Display the QImage in the QLabel
                pixmap = QPixmap.fromImage(q_image)
                self.label.setPixmap(pixmap)
                self.label.setScaledContents(True)
                

    def run_ocr_and_send_email(self):
        # Call the function directly when the button is clicked
        run_ocr_and_send_email(self)

    def run_settings(self):
        self.settings_window = SettingsWindow()
        self.settings_window.show()

    def run_adminstrators(self):
        self.admin_window = AdministratorWindow()
        self.admin_window.show()

    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        super().closeEvent(event)



### SETTINGS WINDOW
class SettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Buttons
        self.b1 = QPushButton("Button 1")
        self.b2 = QPushButton("Button 2")
        self.b3 = QPushButton("Button 3")
        self.exit_button = QPushButton("Exit")

        # Labels to display button names
        self.label1 = QLabel()
        self.label2 = QLabel()
        self.label3 = QLabel()

        layout.addWidget(self.b1)
        layout.addWidget(self.b2)
        layout.addWidget(self.b3)
        layout.addWidget(self.exit_button)
        layout.addWidget(self.label1)
        layout.addWidget(self.label2)
        layout.addWidget(self.label3)

        self.b1.clicked.connect(self.update_label1)
        self.b2.clicked.connect(self.update_label2)
        self.b3.clicked.connect(self.update_label3)
        self.exit_button.clicked.connect(self.close)

    def update_label1(self):
        self.label1.setText("Button 1 clicked")

    def update_label2(self):
        self.label2.setText("Button 2 clicked")

    def update_label3(self):
        self.label3.setText("Button 3 clicked")



### ADMINSTRATORS WINDOW
class AdministratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Administrator Window")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Wrap the QTableWidget in a QScrollArea
        scroll_area = QScrollArea()
        table_widget = QTableWidget(12, 3)  # 12 rows and 3 columns
        scroll_area.setWidget(table_widget)

        # Populate the table with data
        for row in range(12):
            for col in range(3):
                item = QTableWidgetItem(f"Row {row+1}, Col {col+1}")
                table_widget.setItem(row, col, item)

        # Set horizontal header to stretch to the available space
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(scroll_area)

        # Create the Exit button with a label
        exit_button = QPushButton("Exit")
        layout.addWidget(exit_button)

        # Connect the button's click event to the close method
        exit_button.clicked.connect(self.close)


'''class AdminstratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Administrator Window")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create a QListWidget to display the list of contacts
        self.contact_list_widget = QListWidget()

        # Set the size policy and the maximum number of visible items
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.contact_list_widget.setSizePolicy(size_policy)
        self.contact_list_widget.setMaximumHeight(200)  # Adjust this to your preferred height

        layout.addWidget(self.contact_list_widget)

        # Add some contacts to the list (you can replace this with your actual contact data)

        contacts = ["Contact 1", "Contact 2", "Contact 3", "Contact 4", "Contact 5", "Contact 6"]
        admins_dict = {}

        with open('files_email/contacts.txt', mode='r', encoding='utf-8') as contactsFile:
            for line in contactsFile:
                # Split each line into parts (assuming each line is in the format: firstname surname email)
                parts = line.strip().split()

                if len(parts) >= 5:  # Check if the line contains at least three elements
                    admin_firstname = parts[3]
                    admin_lastname = parts[4]
                    admin_email = parts[2]

                    # Create a key (a tuple containing first name and surname) and assign the email as the value
                    admin_tuple = (admin_firstname, admin_lastname)
                    admins_dict[admin_tuple] = admin_email

        self.contact_list_widget.addItems(contacts)

        # Create the Exit button with a label
        self.exit_button = QPushButton("Exit")
        layout.addWidget(self.exit_button)

        # Connect the button's click event to the close method
        self.exit_button.clicked.connect(self.close)'''


class OpticalLightGate:
    def __init__(self):
        
        self.letter_counter = 0
        self.phototransistor = Button(23)  # Connect to IR phototransistor (GPIO23)

        #self.led.on()  # Turn on the IR LED initially

        self.phototransistor.when_pressed = self.on_object_detected
        self.phototransistor.when_released = self.on_object_removed

    def on_object_detected(self):
        
        self.letter_counter += 1
        print("Mail inserted!")
        print(f'There are {self.letter_counter} letters inside.')
        

    def on_object_removed(self):
        print("All mail removed! Mailbox empty.")
        
    
    def run(self):
        # Keep the script running
        pause()
        
    
    ## Email sending process through the ls    
        
    email_address = 'airmail.notify@gmail.com'
    password = 'nuuz freu rukr yzdp'
    
    
    def send_email_light_sensor(self):
        print('Email timing system running')
        

        
        '''
        
        try:
            atetime_ls = get_datetime()
            
            s = smtplib.SMTP(host='smtp.gmail.com', port=587)
            s.starttls()
            s.login(email_address, password)
            
            msg = MIMEMultipart()
            message_template = Template(open('files_email/mailbox_message.txt').read())
            message = message_template.substitute(NUM_LETTERS_LIGHT_GATE=self.letter_counter, DATETIME_STRING=datetime_ls.title())

            msg['From'] = email_address
            msg['To'] = 'fabian.bauriedl@icloud.com'
            msg['Subject'] = "THERE ARE NEW LETTERS IN YOUR MAILBOX!"
            msg.attach(MIMEText(message, 'plain'))
            
            s.send_message(msg)
            s.quit()

            print("Email sent successfully!")

        except smtplib.SMTPRecipientsRefused as e:
            print("SMTPRecipientsRefused error:", e.recipients)
        except Exception as e:
            print("An error occurred:", str(e))'''
            










#class DisplaySleep:
    
    
    
    
    '''def __init__(self):
        pass
    
    def on_move(self, x, y):
        print(time())
        global last_move
        last_move = time()
    
    def start_listener(self):
        print('Before')
        with mouse.Listener(on_move=self.on_move) as listener:
            listener.join()
        listener = mouse.Listener(on_move=on_move)
        listener.start()
        print('After')
        '''
        
def test():
    print('test')


def email_checking_loop():
    while True:
        schedule.run_pending()
        time.sleep(1)  # Add a delay to avoid busy-waiting


#### RUN PROGRAM ####
def main():
    # Create an instance of the OpticalLightGate class
    light_gate = OpticalLightGate()
    
    # light gate thread and displaysleep thread
    light_gate_thread = threading.Thread(target=light_gate.run)
    light_gate_thread.daemon = True  # Set as a daemon thread
    light_gate_thread.start()
    check_email_and_send = light_gate.send_email_light_sensor
    
    #check_email_and_send
    schedule.every().day.at("20:21").do(email_checking_loop)
    email_checking_thread = threading.Thread(target=email_checking_loop)
    email_checking_thread.daemon = True  # Set the thread as a daemon so it won't block program exit
    email_checking_thread.start()
    
    
    
    
    # Create a PyQt application and window
    app = QApplication(sys.argv)
    window = MyWindow()
    window.showFullScreen()
    
    
    
    
    
    sys.exit(app.exec())

    
 
    


if __name__ == "__main__":
    main()
