import smtplib
import os
import sys
import email
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from html.parser import HTMLParser

if not sys.version_info[:2][0] == (3):
    e = 'Python 3.x required'
    raise ImportError(e)


class MLStripper(HTMLParser):

    def __init__(self):
        # initialize the base class
        HTMLParser.__init__(self)

    def read(self, data):
        # clear the current output before re-use
        self._lines = []
        # re-set the parser's state before re-use
        self.reset()
        self.feed(data)
        return ''.join(self._lines)

    def handle_data(self, d):
        self._lines.append(d)


def strip_tags(html):
    s = MLStripper()
    return s.read(html)


def send_msg(user, pwd, recipients, subject, htmlmsgtext, attachments=None, verbose=False):

    try:
        # Make text version from HTML - First convert tags that produce a line
        # break to carriage returns
        msgtext = htmlmsgtext.replace(
            '</br>', "\r").replace('<br />', "\r").replace('</p>', "\r")
        # Then strip all the other tags out
        msgtext = strip_tags(msgtext)

        # necessary mimey stuff
        msg = MIMEMultipart()
        msg.preamble = 'This is a multi-part message in MIME format.\n'
        msg.epilogue = ''

        body = MIMEMultipart('alternative')
        body.attach(MIMEText(msgtext))
        body.attach(MIMEText(htmlmsgtext, 'html'))
        msg.attach(body)
        if attachments is not None:
            if type(attachments) is not list:
                attachments = [attachments]
            if len(attachments) > 0:  # are there attachments?
                for filename in attachments:
                    f = filename
                    part = MIMEBase('application', "octet-stream")
                    part.set_payload(open(f, "rb").read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
                    msg.attach(part)

        msg.add_header('From', user)
        msg.add_header('To', ", ".join(recipients))
        msg.add_header('Subject', subject)
#         msg.add_header('Reply-To', replyto)

        # The actual email sendy bits
        host = 'smtp.gmail.com:587'
        server = smtplib.SMTP(host)
        server.set_debuglevel(False)  # set to True for verbose output
        try:
            # gmail expect tls
            server.starttls()
            server.login(user, pwd)
            server.sendmail(user, recipients, msg.as_string())
            if verbose:
                print('Email sent to {}'.format(recipients))
            server.quit()  # bye bye
        except:
            # if tls is set for non-tls servers you would have raised an
            # exception, so....
            server.login(user, pwd)
            server.sendmail(user, recipients, msg.as_string())
            if verbose:
                print('Email sent to {}'.format(recipients))
            server.quit()  # sbye bye
    except:
        print('Email NOT sent to {} successfully. ERR: {} {} {} '.format(str(recipients),
                                                                         str(sys.exc_info()[
                                                                             0]),
                                                                         str(sys.exc_info()[
                                                                             1]),
                                                                         str(sys.exc_info()[2])))
        raise
        #just in case
