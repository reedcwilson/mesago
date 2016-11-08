#!/usr/bin/env python

import sys
import os
import re
import getpass
import smtplib
import email
import getopt
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders


def get_section(lines, token):
    indices = [i for i, x in enumerate(lines) if x.strip() == token]
    if len(indices) != 2:
        err = "Invalid file format: "
        err += "%s list must have a single open and close tag pair" % token
        print err
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


def dictify(lines):
    tags = [tag.strip() for tag in lines]
    dictionary = {}
    for tag in tags:
        parts = tag.split(':')
        dictionary[parts[0]] = parts[1]
    return dictionary


def get_attachment(path):
    attachment = open(path, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header(
            'Content-Disposition',
            "attachment; filename= %s" % os.path.basename(path))
    return part


def get_param_groups(lines):
    params = []
    i = 0
    start = -1
    while i < len(lines):
        l = lines[i].strip()
        if l == '$message':
            if start == -1:
                start = i
            else:
                params.append(dictify(lines[start+1:i]))
                start = -1
        i += 1
    return params


def get_msg(params, subject_raw, body_raw):
    # get message parts
    tos = params['emails'].split(';')
    subject_raw = ''.join([line.strip() for line in subject_raw])
    subject = replace_tokens(subject_raw, params)
    body = replace_tokens(body_raw, params)
    attaches = {k: v for (k, v) in params.iteritems() if '[attachment]' in k}
    attachments = []
    for k, v in attaches.iteritems():
        attachments.append(get_attachment(v.strip()))
    # add parts of message to msg object
    msg = MIMEMultipart()
    msg['To'] = email.Utils.COMMASPACE.join(tos)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    for attachment in attachments:
        msg.attach(attachment)
    return msg


def get_params(filename):
    # get parameters
    param_lines = []
    with open(filename, 'r') as f:
        param_lines = f.readlines()
    return get_param_groups(param_lines)


def get_template(filename):
    with open(filename, 'r') as f:
        return f.readlines()


def assert_valid_file(filename):
    if not os.path.isfile(filename):
        print "the provided path is not a file: %s" % filename
        sys.exit(1)


def print_usage(exit):
    print ("mesago.py "
           "[-m (print message only)] "
           "-t <templatefile> "
           "-p <paramsfile>"
           )
    sys.exit(2)


def get_args(argv):
    inputfile, outputfile = (None,)*2
    messageonly = False
    try:
        opts, remainder = getopt.getopt(argv[1:], "hmt:p:")
    except getopt.GetoptError:
        print_usage(2)
    for opt, arg in opts:
        if opt == '-h':
            print_usage(0)
        elif opt in ("-t"):
            inputfile = arg
        elif opt in ("-p"):
            outputfile = arg
        elif opt in ("-m"):
            messageonly = True
    return inputfile, outputfile, messageonly


def print_message(msg):
    print '%s##########' % msg


def main(template_filename, params_filename, message_only):
    assert_valid_file(template_filename)
    assert_valid_file(params_filename)
    # get parts of template
    template_lines = get_template(template_filename)
    me = ''.join(get_section(template_lines, '$from')).strip()
    subject = get_section(template_lines, '$subject')
    body_raw = ''.join(get_section(template_lines, '$body'))
    if not message_only:
        password = getpass.getpass('Password: ')
    # get param groups
    param_groups = get_params(params_filename)
    # send off all of the messages
    for params in param_groups:
        msg = get_msg(params, subject, body_raw)
        if not message_only:
            send(msg, me, password)
        else:
            print_message(replace_tokens(body_raw, params))


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


token_func_map = {'file': read_file, 'attachment': lambda x: ""}


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print_usage(-1)
    templatefile, paramsfile, messageonly = get_args(sys.argv)
    main(templatefile, paramsfile, messageonly)
