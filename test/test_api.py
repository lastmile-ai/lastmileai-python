
import unittest
import os

import sys
sys.path.append('../src')

from lastmileai import LastMile


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.lastmile = LastMile(api_key=os.environ.get('LASTMILEAI_API_KEY'))

    def test_health(self):
        res = self.lastmile.api_health()
        self.assertEqual(res.get('status'), 'OK')
        pass
    
    def test_create_trial(self):
        res = self.lastmile.create_trial('test_trial')
        self.assertEqual(res.get('name'), 'test_trial')
        pass
    
    def test_completion(self):
        res = self.lastmile.create_openai_completion({'prompt': 'Hello world', 'model': 'text-davinci-003'})
        self.assertNotEqual(res.get('completionResponse'), None)
        pass

    def tearDown(self):
        
        res = self.lastmile.create_openai_chat_completion({'model': "gpt-3.5-turbo",
    'messages': [
      { 'role': "user", 'content': "Your prompt here" },
    ],})
        self.assertNotEqual(res.get('completionResponse'), None)
        pass

if __name__ == '__main__':
    unittest.main()
