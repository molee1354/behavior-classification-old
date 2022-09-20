import smtplib, ssl

from datetime import datetime

def sendmail(receiver):
    sender = 'testacc98458@gmail.com'
    # receiver = 'molee1354@gmail.com'
    receiver = receiver

    now = datetime.now()
    dt = datetime.strftime(now,"%m%d %H%M")

    message = """\
    [{} Upload Notification]

    Successfully uploaded files.

    """.format(dt)

    port = 465
    password = 'Agusrn09!'

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context = context) as server:
        server.login('testacc98458@gmail.com', password)
        server.sendmail(
            sender,
            receiver,
            message
        )

# ? just keeping it as a module
if __name__ == '__main__':
    receiver = 'molee1354@gmail.com'
    sendmail(receiver)

# TODO: add user input for receiver and make a main() function to make this sendable.        