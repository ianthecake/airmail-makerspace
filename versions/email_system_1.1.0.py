import smtplib
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
#from ocr_text_detection import letter_name
#from ocr_text_detection import letter_department
import datetime
from PIL import Image
import pytesseract
import re
import cv2


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


def main():
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

    #s.send_message(msg)
    del msg
    s.quit()





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
        r"[A-Z][a-zA-Z-'’]+ [A-Z][a-zA-Z-'’]+"   # Each letter of surname and name capitalized
    ]

    # REGEX for Airbus-department codes
    #department_code_pattern = r'^[A-Z0-9-]{3,10}$'
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



### RUN MAIN
if __name__ == '__main__':
    main()