import unittest
import requests
import json
from pathlib import Path

class TestCreatePrompt(unittest.TestCase):   
    LOCAL_DEV_URL = "http://localhost:7071/"
    PUBLIC_URL = "https://quiplash-2425-bv1g22.azurewebsites.net/"
    TEST_FUNCTION = "prompt/suggest"
    TEST_URL = LOCAL_DEV_URL + TEST_FUNCTION
    
    pathToSettings = Path(__file__).parent.parent / 'local.settings.json'
    with open(pathToSettings) as settings_file:
        settings = json.load(settings_file)

    FunctionAppKey = settings['Values']['FunctionAppKey']

    def testSugguestPrompt(self):
        '''
        Test the suggest prompt function
        '''

        response = requests.post(self.TEST_URL, json=json.dumps({"keyword": "food"}),
                                 headers={'x-functions-key': self.FunctionAppKey})
        
        print(response.text)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)

        prompt = response.json()['suggestion']

        with open('./../suggestion.txt', 'w') as f:
            f.write(prompt)
            f.close()
        
        self.assertTrue(len(prompt) > 20)
        self.assertTrue(len(prompt) < 100)
        self.assertTrue("food" in prompt)

    if __name__ == '__main__':
        unittest.main()
