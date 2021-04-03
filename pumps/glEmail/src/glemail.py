
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from smtplib import SMTP

from glEmail.src.util.configuration.configuration import Configuration


class GLEmail(object):

    def __init__(self):
        self.__smtp = Configuration.section("smtp")
        self.__msg = None

    def send(self, subject, to, body, attach):
        try:
            sender = SMTP(self.__smtp["host"], int(self.__smtp["port"]))
            sender.ehlo()
            sender.starttls()
            sender.login(self.__smtp["from"], self.__smtp["password"])
            self.__message(subject, to, body, attach)
            sender.sendmail(self.__smtp['from'], to, self.__msg.as_string())
        except Exception as e:
            return False
        return True

    def __message(self, subject, to, body, attach):
        self.__msg = MIMEMultipart()
        self.__msg["Subject"] = subject
        self.__msg["From"] = self.__smtp["from"]
        self.__msg["To"] = to
        self.__msg.attach(MIMEText(self.__html(body), "html"))
        #self.__msg.attach(self.__attach(attach))
        return

    def __html(self, body):
        html = "<html><head><title></title></head><body><h6 align=center></h6>\
            <h3 align=center>%s</h3><h6 align=center></h6></body>\
            </html>" % body
        return html

    def __attach(self, filename):
        fileattach = MIMEBase("application", "octet-stream")
        fileattach.set_payload(file(filename).read())
        encode_base64(fileattach)
        attachment = "attachment;filename={0}".format(filename.split('/')[-1])
        fileattach.add_header("Content-Disposition", attachment)
        return fileattach
