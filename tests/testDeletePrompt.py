import unittest
import requests
import json
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from azure.cosmos import CosmosClient

from pathlib import Path

class TestDeletePrompt(unittest.TestCase):   
    LOCAL_DEV_URL = "http://localhost:7071/"
    PUBLIC_URL = "https://quiplash-2425-bv1g22.azurewebsites.net/"
    TEST_FUNCTION = "prompt/delete"
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
    player2 = {
        "username": "bryanvullo2",
        "password": "password123"
    }
    prompt1 = {
        "username": "bryanvullo",
        "text": "What is the best food?"
    }
    prompt2 = {
        "username": "bryanvullo",
        "text": "What is the best drink?"
    }
    prompt3 = {
        "username": "bryanvullo2",
        "text": "What is the best color?"
    }


    @classmethod
    def setUpClass(cls):
        '''
        Register 2 players before testing
        '''
        REGISTER_URL = cls.TEST_URL.replace("prompt/delete", "player/register")
        requests.post(REGISTER_URL, json=(cls.player),
                      headers={"x-functions-key": cls.FunctionAppKey} )
        requests.post(REGISTER_URL, json=(cls.player2),
                        headers={"x-functions-key": cls.FunctionAppKey} )
        
    @classmethod
    def tearDownClass(cls):
        '''
        Delete the players after testing
        '''
        for doc in cls.PlayerContainerProxy.read_all_items():
          cls.PlayerContainerProxy.delete_item(item=doc, partition_key=doc['id'])

    def setUp(self):
        '''
        Add prompts before testing
        '''
        
        CREATE_URL = self.TEST_URL.replace("delete", "create")
        requests.post(CREATE_URL, json=(self.prompt1),
                      headers={"x-functions-key": self.FunctionAppKey} )
        requests.post(CREATE_URL, json=(self.prompt2),
                        headers={"x-functions-key": self.FunctionAppKey} )
        requests.post(CREATE_URL, json=(self.prompt3),
                        headers={"x-functions-key": self.FunctionAppKey} )
        
    def tearDown(self):
        '''
        Delete the prompts remaining after testing
        '''
        for doc in self.PromptContainerProxy.read_all_items():
          self.PromptContainerProxy.delete_item(item=doc, partition_key=doc['username'])

    def testDelete1Prompt(self):
        '''
        Test delete prompt user has only 1 prompt in the database
        '''

        self.assertEqual(len(list(self.PromptContainerProxy.read_all_items())), 3)

        body = {'player' : self.prompt3.get('username')}
        response = requests.post(self.TEST_URL, json=(body),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(response.json()['msg'], "1 prompts deleted")

        self.assertEqual(len(list(self.PromptContainerProxy.read_all_items())), 2)

    def testDelete2Prompts(self):
        '''
        Test delete prompt user has 2 prompts in the database
        '''

        self.assertEqual(len(list(self.PromptContainerProxy.read_all_items())), 3)

        body = {'player' : self.prompt1.get('username')}
        response = requests.post(self.TEST_URL, json=(body),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(response.json()['msg'], "2 prompts deleted")

        self.assertEqual(len(list(self.PromptContainerProxy.read_all_items())), 1)

    def testDeleteNoPrompts(self):
        '''
        Test delete prompt user has no prompts in the database
        '''

        self.assertEqual(len(list(self.PromptContainerProxy.read_all_items())), 3)

        body = {'player' : 'bryanvullo3'}
        response = requests.post(self.TEST_URL, json=(body),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(response.json()['msg'], "0 prompts deleted")

        self.assertEqual(len(list(self.PromptContainerProxy.read_all_items())), 3)


    if __name__ == '__main__':
        unittest.main()
