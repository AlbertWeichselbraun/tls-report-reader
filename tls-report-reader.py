#!/usr/bin/env python

import argparse
import email

from imaplib import IMAP4_SSL, IMAP4
from getpass import getpass
from gzip import decompress
from json import loads
from datetime import date, timedelta
from collections import defaultdict

DEFAULT_CONFIG_FILE = 'tls-report-reader.json'

def parse_args():
    ''' parse command line arguments '''
    parser = argparse.ArgumentParser(description='Analyze TLS reports.')
    parser.add_argument('--days', metavar='N', type=int, default=1,
                        help='Number of days to summarize')
    parser.add_argument('--stats', action='store_true',
                        help='Print statistics, even if no errors have been reported.')
    parser.add_argument('-c', '--config', default=DEFAULT_CONFIG_FILE)

    return parser.parse_args()


def read_config(config_file):
    '''
    Returns:
        The configuration provided in the config file.
    '''
    with open(config_file) as f:
        return loads(f.read())


def compute_stats(imap_server, imap_user, imap_pass, imap_filter, since):
    '''
    Returns:
        The number of failures and a dictionary with per reporter and
        domain statistics.
    '''
    stats = defaultdict(dict)
    failures = 0
    try:
        with IMAP4_SSL(imap_server) as imap:
            imap.login(imap_user, imap_pass)
            imap.select("INBOX")
            rv, messages = imap.search(None, '({} SINCE {})'.format(
                imap_filter, since.strftime("%d-%b-%Y")))
            for msg in messages[0].split(b" "):
                rv, data = imap.fetch(msg, '(RFC822)')

                for response in data:
                    if isinstance(response, tuple):
                        msg = email.message_from_bytes(response[1])

                        if not msg.is_multipart():
                            print("Message is not multipart!")
                            exit(-1)

                        for part in msg.walk():
                            content_disposition = str(
                                part.get("Content-Disposition"))
                            if content_disposition.startswith('attachment'):
                                content = part.get_payload(decode=True)
                                content = decompress(content)
                                j = loads(content)

                                reporter = j['contact-info']
                                date_range = j['date-range']
                                for policy in j['policies']:
                                    domain = policy['policy']['policy-domain']
                                    if not domain in stats[reporter]:
                                        stats[reporter][domain] = {}
                                    stats[reporter][domain]['successful'] = stats[reporter][domain].get('successful', 0) + policy['summary']['total-successful-session-count']
                                    stats[reporter][domain]['failure'] = stats[reporter][domain].get('failure', 0) + policy['summary']['total-failure-session-count']
                                    failures += policy['summary']['total-failure-session-count']

    except IMAP4.error as e:
        print("Login failed.", e)
        exit(-1)

    return failures, stats


def format_statisics(stats, since):
    r = ['# Mail statistics: {} to {}:\n'.format(since.isoformat(),
                                                date.today().isoformat())]

    for no, reporter in enumerate(stats, 1):
        r.append('{}. {}'.format(no, reporter))
        for domain in stats[reporter]:
            r.append('   - {}: successful: {}, failure: {}'.format(domain, stats[reporter][domain]['successful'], stats[reporter][domain]['failure']))
    return '\n'.join(r)


if __name__ == '__main__':
    args = parse_args()
    config = read_config(args.config)

    since = date.today() - timedelta(days=args.days)
    failures, stats = compute_stats(imap_server=config['imap_server'],
                                    imap_user=config['imap_user'],
                                    imap_pass=config['imap_pass'],
                                    imap_filter=config['imap_filter'],
                                    since=since)

    if failures > 0 or args.stats:
        print(format_statisics(stats, since=since))
