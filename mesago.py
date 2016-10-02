#!/usr/bin/env python

import sys
import os
import re
import getpass
import smtplib
import email
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


def get_section(lines, token):
    indices = [i for i, x in enumerate(lines) if x.strip() == token]
    if len(indices) != 2:
        str = "Invalid file format: "
        str += "%s list must have a single open and close tag pair" % token
        print str
        sys.exit(1)
    return lines[indices[0]+1:indices[1]]


def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()


def replace_tokens(text, tokens):
    new_str = text
    for token, value in tokens.iteritems():
        match = re.match('(\[(\w+)\])', token)
        if match:
            groups = match.groups()
            full_token = groups[0]
            token_type = groups[1]
            if token_type not in token_func_map:
                print "Invalid special token: [%s]" % token_type
                sys.exit(1)
            value = token_func_map[token_type](value)
            token = token.replace(full_token, '')
        new_str = new_str.replace('${%s}' % token, value)
    return new_str


def dictify(line):
    tags = [tag for tag in line.split(',')]
    dictionary = {}
    for tag in tags:
        parts = tag.split(':')
        dictionary[parts[0]] = parts[1]
    return dictionary


def get_msg(to, subject, body_raw):
    tokens = dictify(to)
    tos = tokens['email'].split(';')
    body = replace_tokens(body_raw, tokens)
    # add parts of message to msg object
    msg = MIMEMultipart()
    msg['To'] = email.Utils.COMMASPACE.join(tos)
    msg['Subject'] = ''.join([line.strip() for line in subject])
    msg.attach(MIMEText(body, 'plain'))
    return msg


def main(message_file):
    if not os.path.isfile(message_file):
        print "the provided path is not a file"
        sys.exit(1)
    lines = []
    with open(message_file, 'r') as f:
        lines = [line for line in f.readlines()]
    # get parts of message
    me = ''.join(get_section(lines, '$from')).strip()
    to_lines = get_section(lines, '$to')
    subject = get_section(lines, '$subject')
    body_raw = ''.join(get_section(lines, '$body'))
    password = getpass.getpass('Password: ')
    for to in to_lines:
        msg = get_msg(to.strip(), subject, body_raw)
        send(msg, me, password)


def send(msg, from_addr, password):
    msg['From'] = from_addr
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    try:
        server.login(from_addr, password)
    except smtplib.SMTPAuthenticationError:
        print 'Username and password not accepted: %s' % from_addr
        sys.exit(1)
    text = msg.as_string()
    server.sendmail(from_addr, msg['To'].split(', '), text)
    server.quit()


token_func_map = {'file': read_file}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "You must provide a message file"
        sys.exit(1)
    main(sys.argv[1])
