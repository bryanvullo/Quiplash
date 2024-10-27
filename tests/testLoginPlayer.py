import unittest
import requests
import json
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from azure.cosmos import CosmosClient

from pathlib import Path

class TestLoginPlayer(unittest.TestCase):   
    LOCAL_DEV_URL = "http://localhost:7071/"
    PUBLIC_URL = "<Your deployment URL here>/"
    TEST_FUNCTION = "player/login"
    TEST_URL = LOCAL_DEV_URL + TEST_FUNCTION
    
    pathToSettings = Path(__file__).parent.parent / 'local.settings.json'
    with open(pathToSettings) as settings_file:
        settings = json.load(settings_file)

    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    QuiplashDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    PlayerContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PlayerContainerName'])
    FunctionAppKey = settings['Values']['FunctionAppKey']

    validPlayer = {
        "username": "bryanvullo",
        "password": "password123"
    }

    @classmethod
    def setUpClass(cls):
        '''
        Register a player before testing
        '''
        REGISTER_URL = cls.TEST_URL.replace("login", "register")
        requests.post(REGISTER_URL, json=json.dumps(cls.validPlayer),
                      headers={"x-functions-key": cls.FunctionAppKey} )
        
    @classmethod
    def tearDownClass(cls):
        '''
        Delete the player after testing
        '''
        for doc in cls.PlayerContainerProxy.read_all_items():
          cls.PlayerContainerProxy.delete_item(item=doc, partition_key=doc['id'])
        
    def testValidLogin(self):
        '''
        Test a valid login
        '''
        response = requests.get(self.TEST_URL, json=json.dumps(self.validPlayer),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(response.json()['msg'], "OK")

    def testInexistentUsername(self):
        '''
        Test an inexistent username
        '''
        inexistentPlayer = self.validPlayer.copy()
        inexistentPlayer['username'] = "inexistent"

        response = requests.get(self.TEST_URL, json=json.dumps(inexistentPlayer),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['result'], False)
        self.assertEqual(response.json()['msg'], "Username or password incorrect")
    
    def testWrongPassword(self):
        '''
        Test a wrong password
        '''
        wrongPasswordPlayer = self.validPlayer.copy()
        wrongPasswordPlayer['password'] = "wrongpassword"

        response = requests.get(self.TEST_URL, json=json.dumps(wrongPasswordPlayer),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['result'], False)
        self.assertEqual(response.json()['msg'], "Username or password incorrect")
    
    if __name__ == '__main__':
        unittest.main()
