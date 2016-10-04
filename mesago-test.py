#!/usr/bin/env python

import mesago
import unittest


class TestStringMethods(unittest.TestCase):

    def test_dictify(self):
        email = 'test@gmail.com'
        name = 'John'
        dictionary = mesago.dictify(['email:%s\n' % email,'name:%s\n' % name])
        self.assertEqual(dictionary['email'], email)
        self.assertEqual(dictionary['name'], name)

    def test_replace_tokens(self):
        text = "${token} works"
        tokens = {'token': 'nothing'}
        message = mesago.replace_tokens(text, tokens)
        self.assertEqual(message, "nothing works")

    def test_get_msg(self):
        params = {'email':'test@gmail.com','name':'John'}
        subject = ['Test']
        body = '${name} is awesome'
        msg = mesago.get_msg(params, subject, body)
        text = msg.get_payload()[0].get_payload()
        self.assertEqual(text, "John is awesome")
        self.assertEqual(msg['Subject'], "Test")

    def test_get_params_single(self):
        lines = [
                "$message\n",
                "emails:to@a.com\n",
                "name:person\n",
                "$message\n",
                ]
        params = mesago.get_param_groups(lines)
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]['emails'], 'to@a.com')

    def test_get_params_multiple(self):
        lines = [
                "$message\n",
                "emails:to@a.com\n",
                "name:person\n",
                "$message\n",
                "\n",
                "$message\n",
                "emails:to@b.com\n",
                "name:thing\n",
                "$message\n",
                ]
        params = mesago.get_param_groups(lines)
        self.assertEqual(len(params), 2)

if __name__ == '__main__':
    unittest.main()
