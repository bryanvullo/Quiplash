import unittest
import requests
import json
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from azure.cosmos import CosmosClient

from pathlib import Path

class TestUpdatePlayer(unittest.TestCase):   
    LOCAL_DEV_URL = "http://localhost:7071/"
    PUBLIC_URL = "https://quiplash-2425-bv1g22.azurewebsites.net/"
    TEST_FUNCTION = "player/update"
    TEST_URL = PUBLIC_URL + TEST_FUNCTION
    
    pathToSettings = Path(__file__).parent.parent / 'local.settings.json'
    with open(pathToSettings) as settings_file:
        settings = json.load(settings_file)

    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    QuiplashDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    PlayerContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PlayerContainerName'])
    FunctionAppKey = settings['Values']['FunctionAppKey']

    player = {
        "username": "bryanvullo",
        "password": "password123"
    }
    update = {
        "username": "bryanvullo",
        "add_to_games_played": 1,
        "add_to_score": 100
    }

    def setUp(self):
        '''
        Register a player before testing
        '''
        REGISTER_URL = self.TEST_URL.replace("update", "register")
        requests.post(REGISTER_URL, json=(self.player),
                      headers={"x-functions-key": self.FunctionAppKey} )
        
    def tearDown(self):
        '''
        Delete the player after testing
        '''
        for doc in self.PlayerContainerProxy.read_all_items():
          self.PlayerContainerProxy.delete_item(item=doc, partition_key=doc['id'])

    def testValidUpdate(self):
        '''
        Test a valid update
        '''
        response = requests.put(self.TEST_URL, json=(self.update),
                                 headers={"x-functions-key": self.FunctionAppKey} )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], True)
        self.assertEqual(response.json()['msg'], "OK")

        result = json.loads(json.dumps(list(self.PlayerContainerProxy.read_all_items())[0]))
        self.assertEqual(result['username'], self.update['username'])
        self.assertEqual(result['games_played'], self.update['add_to_games_played'])
        self.assertEqual(result['total_score'], self.update['add_to_score'])
    
    if __name__ == '__main__':
        unittest.main()
