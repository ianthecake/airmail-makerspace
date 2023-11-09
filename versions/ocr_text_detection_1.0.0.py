from PIL import Image
import pytesseract
import re
import cv2

letter_name = None
letter_department = None


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

# Return names and departments for email usage