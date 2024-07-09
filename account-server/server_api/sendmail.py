import smtplib
from getpass import getpass
from email.mime.text import MIMEText


def send_gameland_email(receiver, subject, body):
    send_email("gameland.noreply@gmail.com", token, receiver, subject, body)
    
def send_email(user, pwd, receiver, subject, body):

    sender = user

    content = body

    msg = MIMEText(content)
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = subject

    smtp_server_name = 'smtp.gmail.com'
    port = '465' # for secure messages
    #port = '587' # for normal messages

    if port == '465':
        server = smtplib.SMTP_SSL('{}:{}'.format(smtp_server_name, port))
    else:
        server = smtplib.SMTP('{}:{}'.format(smtp_server_name, port))
        server.starttls() # this is for secure reason

    server.login(sender, pwd)
    server.send_message(msg)
    server.quit()
        
        
token = "lolgameland36"
        
if __name__ == "__main__":
    send_email("gameland.noreply@gmail.com", token, "gameland.noreply@gmail.com", "Hola", "Como estas?")
    
    