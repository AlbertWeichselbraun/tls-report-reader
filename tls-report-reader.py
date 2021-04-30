#!/usr/bin/env python

import email

from imaplib import IMAP4_SSL, IMAP4
from getpass import getpass
from gzip import decompress
from json import loads

EMAIL_ACCOUNT = "albert.weichselbraun@gmail.com"
APP_PASSWORD = "lgyfsmewiavzuilt"

TO = "albert.weichselbraun+tls@gmail.com"

try:
    with IMAP4_SSL("imap.gmail.com") as imap:
        imap.login(EMAIL_ACCOUNT, APP_PASSWORD)
        imap.select("INBOX")
        rv, messages = imap.search(None, '(TO "{}")'.format(TO))
        for msg in messages[0].split(b" "):
            rv, data = imap.fetch(msg, '(RFC822)')

            for response in data:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])

                    if not msg.is_multipart():
                        print("Message is not multipart!")
                        exit(-1)

                    for part in msg.walk():
                        content_disposition = str(part.get("Content-Disposition"))
                        if content_disposition.startswith('attachment'):
                            content = part.get_payload(decode=True)
                            content = decompress(content)
                            j = loads(content)

                            reporter = j['contact-info']
                            date_range = j['date-range']
                            for policy in j['policies']:
                                print(reporter, '({}-{})'.format(date_range['start-datetime'], date_range['end-datetime']), '>', policy['policy']['policy-domain'], policy['summary'])

            # exit(-1)

except IMAP4.error as e:
    print("Login failed.", e)
    exit(-1)
