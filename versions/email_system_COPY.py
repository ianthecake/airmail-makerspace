import smtplib
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ocr_text_detection import letter_name
from ocr_text_detection import letter_department

email_adress = 'airmail.notify@gmail.com'
password = 'nuuz freu rukr yzdp'


def check_contact(letter_name):
    with open('../files_email/contacts.txt', 'r') as file:
        file_contents = file.read()

        EMAIL_TO = None

        if letter_name in file_contents:
            EMAIL_TO = letter_name
            print(f'Name {letter_name} found in contacts.txt and returned as {EMAIL_TO}')
            return EMAIL_TO
        else:
            EMAIL_TO = 'Ausbildungsabteilung München'
            print(f'Name {letter_name} was NOT found in contacts.txt and is returned as {EMAIL_TO}')
            return EMAIL_TO


def getContacts(filename, email_to):
    firstnames = []
    surnames = []
    emails = []
    '''with open(filename, mode='r', encoding='utf-8') as contactsFile:
        for a_contact in contactsFile:
            firstnames.append(a_contact.split()[0])
            surnames.append(a_contact.split()[1])
            emails.append(a_contact.split()[2])'''


    return firstnames, surnames, emails


def readTemplate(filename):
    with open(filename, 'r', encoding='utf-8') as templateFile:
        templateFileNachricht = templateFile.read()
    return Template(templateFileNachricht)


def main():
    firstnames, surnames, emails = getContacts('../files_email/contacts.txt', check_contact(letter_name))
    messageTemplate = readTemplate('../files_email/message.txt')

    s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    s.starttls()
    s.login(email_adress, password)


    for firstname, surname, email in zip(firstnames, surnames, emails):
        msg = MIMEMultipart()
        full_name = f'{firstname} {surname}'
        message = messageTemplate.substitute(CONTACT_NAME=full_name.title())

        print(message)

        msg['From'] = email_adress
        msg['To'] = email
        msg['Subject'] = "THERE'S A NEW LETTER IN YOUR MAILBOX!"

        msg.attach(MIMEText(message, 'plain'))

        s.send_message(msg)
        del msg

    s.quit()

#print(getContacts('files_email/contacts.txt'))
if __name__ == '__main__':
    main()