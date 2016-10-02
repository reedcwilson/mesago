#!/usr/bin/env python

import mesago
import unittest


class TestStringMethods(unittest.TestCase):

    def test_dictify(self):
        email = 'test@gmail.com'
        name = 'John'
        dictionary = mesago.dictify('email:%s,name:%s' % (email, name))
        self.assertEqual(dictionary['email'], email)
        self.assertEqual(dictionary['name'], name)

    def test_replace_tokens(self):
        text = "${token} works"
        tokens = {'token': 'nothing'}
        message = mesago.replace_tokens(text, tokens)
        self.assertEqual(message, "nothing works")

    def test_get_msg(self):
        to = 'email:test@gmail.com,name:John'
        subject = ['Test']
        body = '${name} is awesome'
        msg = mesago.get_msg(to, subject, body)
        text = msg.get_payload()[0].get_payload()
        self.assertEqual(text, "John is awesome")
        self.assertEqual(msg['Subject'], "Test")

if __name__ == '__main__':
    unittest.main()
