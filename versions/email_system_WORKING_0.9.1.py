import smtplib
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ocr_text_detection import letter_name
from ocr_text_detection import letter_department




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


def main():
    firstname, surname, email = get_contacts_by_name('../files_email/contacts.txt', letter_name)
    contact_for_message = [firstname, surname, email]
    messageTemplate = readTemplate('../files_email/message.txt')

    print(f'Firstname: {firstname}, Surname: {surname}, Email: {email}')

    s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    s.starttls()
    s.login(email_adress, password)


    #for f, s, e in contact_for_message:
    msg = MIMEMultipart()
    full_name = f'{contact_for_message[0]} {contact_for_message[1]}'
    message = messageTemplate.substitute(CONTACT_NAME=full_name.title())

    print(message)

    msg['From'] = email_adress
    msg['To'] = email
    msg['Subject'] = "THERE'S A NEW LETTER IN YOUR MAILBOX!"

    msg.attach(MIMEText(message, 'plain'))

    s.send_message(msg)
    del msg

    s.quit()

if __name__ == '__main__':
    main()