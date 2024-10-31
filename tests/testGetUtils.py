import unittest
import requests
import json
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from azure.cosmos import CosmosClient

from pathlib import Path

class TestGetUtils(unittest.TestCase):   
    LOCAL_DEV_URL = "http://localhost:7071/"
    PUBLIC_URL = "https://quiplash-2425-bv1g22.azurewebsites.net/"
    TEST_FUNCTION = "utils/get"
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
    player3 = {
        "username": "bryanvullo3",
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
    prompt4 = {
        "username": "bryanvullo2",
        "text": "What is the best animal?"
    }
    prompt5 = {
        "username": "bryanvullo3",
        "text": "What is the best movie?"
    }

    @classmethod
    def setUpClass(cls):
        '''
        Register players before testing
        Add prompts before testing
        '''
        REGISTER_URL = cls.TEST_URL.replace("utils/get", "player/register")
        requests.post(REGISTER_URL, json=json.dumps(cls.player),
                      headers={"x-functions-key": cls.FunctionAppKey} )
        requests.post(REGISTER_URL, json=json.dumps(cls.player2),
                        headers={"x-functions-key": cls.FunctionAppKey} )
        requests.post(REGISTER_URL, json=json.dumps(cls.player3),
                        headers={"x-functions-key": cls.FunctionAppKey} )
        
        CREATE_URL = cls.TEST_URL.replace("utils/get", "prompt/create")
        requests.post(CREATE_URL, json=json.dumps(cls.prompt1),
                      headers={"x-functions-key": cls.FunctionAppKey} )
        requests.post(CREATE_URL, json=json.dumps(cls.prompt2),
                        headers={"x-functions-key": cls.FunctionAppKey} )
        requests.post(CREATE_URL, json=json.dumps(cls.prompt3),
                        headers={"x-functions-key": cls.FunctionAppKey} )
        requests.post(CREATE_URL, json=json.dumps(cls.prompt4),
                        headers={"x-functions-key": cls.FunctionAppKey} )
        requests.post(CREATE_URL, json=json.dumps(cls.prompt5),
                        headers={"x-functions-key": cls.FunctionAppKey} )
        
    @classmethod
    def tearDownClass(cls):
        '''
        Delete the players after testing
        Delete the prompts remaining after testing
        '''
        for doc in cls.PlayerContainerProxy.read_all_items():
            cls.PlayerContainerProxy.delete_item(item=doc, partition_key=doc['id'])

        for doc in cls.PromptContainerProxy.read_all_items():
            cls.PromptContainerProxy.delete_item(item=doc, partition_key=doc['username'])

    def testGetPromptFrom1and3InEnglish(self):
        '''
        Test getting prompts from 2 different players
        '''
        body = {
            "players" : ["bryanvullo", "bryanvullo3"],
            "language" : "en"
        }
        response = requests.get(self.TEST_URL, json=json.dumps(body),
                                headers={"x-functions-key": self.FunctionAppKey})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

        testPrompts = ["What is the best food?","What is the best drink?","What is the best movie?"]
        testPromptsSet = set(testPrompts)
        testUsernames = ["bryanvullo", "bryanvullo3"]
        testUsernamesSet = set(testUsernames)

        responsePromptsSet = set()
        responseUsernamesSet = set()
        for prompt in response.json():
            responsePromptsSet.add(prompt.get('text'))
            responseUsernamesSet.add(prompt.get('username'))
        
        self.assertEqual(testPromptsSet, responsePromptsSet)
        self.assertEqual(testUsernamesSet, responseUsernamesSet)

    def testGetPromptFrom3InSpanish(self):
        '''
        Test getting prompts from player3 to check in Spanish
        '''
        body = {
            "players" : ["bryanvullo3"],
            "language" : "es"
        }
        response = requests.get(self.TEST_URL, json=json.dumps(body),
                                headers={"x-functions-key": self.FunctionAppKey})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        testPrompts = ["¿Cuál es la mejor película?"]
        testPromptsSet = set(testPrompts)
        testUsernames = ["bryanvullo3"]
        testUsernamesSet = set(testUsernames)

        responsePromptsSet = set()
        responseUsernamesSet = set()
        for prompt in response.json():
            responsePromptsSet.add(prompt.get('text'))
            responseUsernamesSet.add(prompt.get('username'))
        
        self.assertEqual(testPromptsSet, responsePromptsSet)
        self.assertEqual(testUsernamesSet, responseUsernamesSet)

        

    if __name__ == '__main__':
        unittest.main()
