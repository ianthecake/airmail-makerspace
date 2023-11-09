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
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer, Qt

### EMAIL SYSTEM
email_adress = 'airmail.notify@gmail.com'
password = 'nuuz freu rukr yzdp'


def get_contacts_by_name(filename, letter_name):
    contact_dict = {}
    with open(filename, mode='r', encoding='utf-8') as contactsFile:
        for line in contactsFile:
            # Split each line into parts (assuming each line is in the format: firstname surname email)
            parts = line.strip().split()

            if len(parts) >= 3:  # Check if the line contains at least three elements
                first_name = parts[0]
                surname = parts[1]
                email = parts[2]

                # Create a key (a tuple containing first name and surname) and assign the email as the value
                key = (first_name, surname)
                contact_dict[key] = email

    # Iterate through the dictionary to find a match for the given name
    email_to_name = None
    email_address = None
    # Initialize these variables to None
    get_firstname = None
    get_lastname = None

    for key, value in contact_dict.items():
        if f"{key[0]} {key[1]}" == letter_name:
            email_to_name = letter_name
            get_firstname = key[0]
            get_lastname = key[1]
            email_address = value
            break  # Exit the loop once a match is found

    return get_firstname, get_lastname, email_address


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
def run_ocr_and_send_email():
    ## OCR
    letter_name = None
    letter_department = None

    get_camera_image()
    filename = '/Users/ian/Desktop/HandwritingDetection/Project/jpegs/captured_image.jpg'
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
    firstname, surname, email = get_contacts_by_name('files_email/contacts.txt', letter_name)
    contact_for_message = [firstname, surname, email]
    messageTemplate = readTemplate('files_email/message.txt')

    print(f'Firstname: {firstname}, Surname: {surname}, Email: {email}')

    try:
        s = smtplib.SMTP(host='smtp.gmail.com', port=587)
        s.starttls()
        s.login(email_adress, password)

        msg = MIMEMultipart()
        full_name = f'{contact_for_message[0]} {contact_for_message[1]}'
        message = messageTemplate.substitute(CONTACT_NAME=full_name.title(), DATETIME_STRING=get_datetime().title())

        msg['From'] = email_adress
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
            cv2.imwrite("jpegs/captured_image.jpg", frame)
            print("Image captured and saved as 'captured_image.jpg'")
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


# OCR work:


# Return names and departments for email usage


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

        #self.camera_button = QPushButton("Start Camera Feed")
        #self.layout.addWidget(self.camera_button)

        self.email_button = QPushButton("Run Email System")
        self.layout.addWidget(self.email_button)

        self.settings_button = QPushButton('Settings')
        self.layout.addWidget((self.settings_button))

        self.label = QLabel(self)
        self.layout.addWidget(self.label)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #self.camera_button.clicked.connect(self.start_camera_feed)
        self.email_button.clicked.connect(self.run_ocr_and_send_email)
        self.settings_button.clicked.connect(self.run_settings)


        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera_feed)

        self.start_camera_feed()


    def start_camera_feed(self):
        if not self.cap:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.timer.start(30)  # Update every 30 milliseconds

    def update_camera_feed(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Convert OpenCV BGR image to QImage
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

                # Display the QImage in the QLabel
                pixmap = QPixmap.fromImage(q_image)
                self.label.setPixmap(pixmap)
                self.label.setScaledContents(True)

    def run_ocr_and_send_email(self):
        # Call the function directly when the button is clicked
        run_ocr_and_send_email()

    def run_settings(self):
        self.settings_window = SettingsWindow()
        self.settings_window.show()

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




#### RUN PROGRAM ####

def main():
    ## PYQT
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()