import unittest
import requests
import json
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from azure.cosmos import CosmosClient

from pathlib import Path

class TestCreatePrompt(unittest.TestCase):   
    LOCAL_DEV_URL = "http://localhost:7071/"
    PUBLIC_URL = "https://quiplash-2425-bv1g22.azurewebsites.net/"
    TEST_FUNCTION = "prompt/create"
    TEST_URL = PUBLIC_URL + TEST_FUNCTION
    
    pathToSettings = Path(__file__).parent.parent / 'local.settings.json'
    with open(pathToSettings) as settings_file:
        settings = json.load(settings_file)

    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    QuiplashDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    PlayerContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PlayerContainerName'])
    PromptContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PromptContainerName'])
    FunctionAppKey = settings['Values']['FunctionAppKey']

    player = {
        "username": "bryanvullo",
        "password": "password123"
    }
    promptEnglish = {
        # valid
        "username": "bryanvullo",
        "text": "What is the best food?"
    }
    promptLong = {
        # too long
        "username": "bryanvullo",
        "text": "What is the best food? What is the best food? " + 
            "What is the best food? What is the best food? What is the best food?"
    }
    promptShort = {
        # too short
        "username": "bryanvullo",
        "text": "What?"
    }
    promptItalian = {
        # unsupported language
        "username": "bryanvullo",
        "text": "Qual è il miglior cibo?"
    }
    promptNotPlayer = {
        # player does not exist
        "username": "notplayer",
        "text": "What is the best food?"
    }
    promptHindi = {
        # supported language
        "username": "bryanvullo",
        "text": "सबसे अच्छा खाना क्या है?"
    }
    promptIrish = {
        # supported language
        "username": "bryanvullo",
        "text": "Cad é an bia is fearr?"
    }
    promptSpanish = {
        # supported language
        "username": "bryanvullo",
        "text": "¿Cuál es la mejor comida?" #correct characters???
    }
    promptChinese = {
        # supported language
        "username": "bryanvullo",
        "text": "最好的食物是什么？最好的食物是什么？最好的食物是什么？"
    }
    promptPolish = {
        # supported language
        "username": "bryanvullo",
        "text": "Jakie jest najlepsze jedzenie?"
    }

    def setUp(self):
        '''
        Register a player before testing
        '''
        REGISTER_URL = self.TEST_URL.replace("prompt/create", "player/register")
        requests.post(REGISTER_URL, json=json.dumps(self.player),
                      headers={"x-functions-key": self.FunctionAppKey} )
        
    def tearDown(self):
        '''
        Delete the player after testing
        '''
        for doc in self.PlayerContainerProxy.read_all_items():
          self.PlayerContainerProxy.delete_item(item=doc, partition_key=doc['id'])
        for doc in self.PromptContainerProxy.read_all_items():
          self.PromptContainerProxy.delete_item(item=doc, partition_key=doc['username'])

    def testValidEnglishPrompt(self):
        '''
        Test a valid prompt in English
        '''
        response = requests.post(self.TEST_URL, json=json.dumps(self.promptEnglish),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(response.json()['msg'], "OK")

        results = json.loads(json.dumps(list(self.PromptContainerProxy.read_all_items())))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['username'], self.promptEnglish['username'])
        self.assertEqual(len(results[0]['texts']), 6)
    
    def testValidHindiPrompt(self):
        '''
        Test a valid prompt in Hindi
        '''
        response = requests.post(self.TEST_URL, json=json.dumps(self.promptHindi),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(response.json()['msg'], "OK")

        results = json.loads(json.dumps(list(self.PromptContainerProxy.read_all_items())))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['username'], self.promptHindi['username'])
        self.assertEqual(len(results[0]['texts']), 6)

    def testValidIrishPrompt(self):
        '''
        Test a valid prompt in Irish
        '''
        response = requests.post(self.TEST_URL, json=json.dumps(self.promptIrish),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(response.json()['msg'], "OK")

        results = json.loads(json.dumps(list(self.PromptContainerProxy.read_all_items())))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['username'], self.promptIrish['username'])
        self.assertEqual(len(results[0]['texts']), 6)
    
    def testValidSpanishPrompt(self):
        '''
        Test a valid prompt in Spanish
        '''
        response = requests.post(self.TEST_URL, json=json.dumps(self.promptSpanish),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(response.json()['msg'], "OK")

        results = json.loads(json.dumps(list(self.PromptContainerProxy.read_all_items())))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['username'], self.promptSpanish['username'])
        self.assertEqual(len(results[0]['texts']), 6)
    
    def testValidChinesePrompt(self):
        '''
        Test a valid prompt in Chinese
        '''
        response = requests.post(self.TEST_URL, json=json.dumps(self.promptChinese),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(response.json()['msg'], "OK")

        results = json.loads(json.dumps(list(self.PromptContainerProxy.read_all_items())))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['username'], self.promptChinese['username'])
        self.assertEqual(len(results[0]['texts']), 6)
    
    def testValidPolishPrompt(self):
        '''
        Test a valid prompt in Polish
        '''
        response = requests.post(self.TEST_URL, json=json.dumps(self.promptPolish),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(response.json()['msg'], "OK")

        results = json.loads(json.dumps(list(self.PromptContainerProxy.read_all_items())))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['username'], self.promptPolish['username'])
        self.assertEqual(len(results[0]['texts']), 6)
    
    def testLongPrompt(self):
        '''
        Test a prompt that is too long
        '''
        response = requests.post(self.TEST_URL, json=json.dumps(self.promptLong),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['result'], False)
        self.assertEqual(response.json()['msg'], "Prompt less than 20 characters or more than 100 characters")
    
    def testShortPrompt(self):
        '''
        Test a prompt that is too short
        '''
        response = requests.post(self.TEST_URL, json=json.dumps(self.promptShort),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['result'], False)
        self.assertEqual(response.json()['msg'], "Prompt less than 20 characters or more than 100 characters")
    
    def testUnsupportedLanguagePrompt(self):
        '''
        Test a prompt in an unsupported language
        '''
        response = requests.post(self.TEST_URL, json=json.dumps(self.promptItalian),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['result'], False)
        self.assertEqual(response.json()['msg'], "Unsupported language")
    
    def testPlayerDoesNotExistPrompt(self):
        '''
        Test a prompt for a player that does not exist
        '''
        response = requests.post(self.TEST_URL, json=json.dumps(self.promptNotPlayer),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['result'], False)
        self.assertEqual(response.json()['msg'], "Player does not exist")
   
    if __name__ == '__main__':
        unittest.main()
