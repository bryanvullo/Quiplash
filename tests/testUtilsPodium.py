import unittest
import requests
import json
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from azure.cosmos import CosmosClient

from pathlib import Path

class TestGetUtils(unittest.TestCase):   
    LOCAL_DEV_URL = "http://localhost:7071/"
    PUBLIC_URL = "https://quiplash-2425-bv1g22.azurewebsites.net/"
    TEST_FUNCTION = "utils/podium"
    TEST_URL = LOCAL_DEV_URL + TEST_FUNCTION
    
    pathToSettings = Path(__file__).parent.parent / 'local.settings.json'
    with open(pathToSettings) as settings_file:
        settings = json.load(settings_file)

    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    QuiplashDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    PlayerContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PlayerContainerName'])
    PromptContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PromptContainerName'])
    FunctionAppKey = settings['Values']['FunctionAppKey']

    player = {
        "username": "alpha-user",
        "password": "password123"
    }
    player2 = {
        "username": "bravo-user",
        "password": "password123"
    }
    player3 = {
        "username": "charlie-user",
        "password": "password123"
    }
    player4 = {
        "username": "delta-user",
        "password": "password123"
    }
    player5 = {
        "username": "echo-user",
        "password": "password123"
    }
    player6 = {
        "username": "foxtrot-user",
        "password": "password123"
    }
    player7 = {
        "username": "golf-user",
        "password": "password123"
    }
    players = [player, player2, player3, player4, player5, player6, player7]

    update = {
        "username": "alpha-user",
        "add_to_games_played": 10,
        "add_to_score": 40
    }
    update2 = {
        "username": "bravo-user",
        "add_to_games_played": 20,
        "add_to_score": 80
    }
    update3 = {
        "username": "charlie-user",
        "add_to_games_played": 10,
        "add_to_score": 40
    }
    update4 = {
        "username": "delta-user",
        "add_to_games_played": 10,
        "add_to_score": 80
    }
    update5 = {
        "username": "echo-user",
        "add_to_games_played": 50,
        "add_to_score": 100
    }
    update6 = {
        "username": "foxtrot-user",
        "add_to_games_played": 10,
        "add_to_score": 10
    }
    update7 = {
        "username": "golf-user",
        "add_to_games_played": 10,
        "add_to_score": 10
    }
    updates = [update, update2, update3, update4, update5, update6, update7]

    @classmethod
    def setUpClass(cls):
        '''
        Register players before testing
        Update players before testing
        '''
        REGISTER_URL = cls.TEST_URL.replace("utils/podium", "player/register")
        for player in cls.players:
            requests.post(REGISTER_URL, json=json.dumps(player),
                          headers={"x-functions-key": cls.FunctionAppKey} )
        
        UPDATE_URL = cls.TEST_URL.replace("utils/podium", "player/update")
        for update in cls.updates:
            requests.put(UPDATE_URL, json=json.dumps(update),
                          headers={"x-functions-key": cls.FunctionAppKey} )
        
    @classmethod
    def tearDownClass(cls):
        '''
        Delete the players after testing
        '''
        for doc in cls.PlayerContainerProxy.read_all_items():
            cls.PlayerContainerProxy.delete_item(item=doc, partition_key=doc['id'])

    def testUtilsPodium(self):
        '''
        Test the podium utility function
        '''
        response = requests.get(self.TEST_URL, headers={"x-functions-key": self.FunctionAppKey} )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

        gold = response.json()['gold']
        silver = response.json()['silver']
        bronze = response.json()['bronze']

        self.assertEqual(len(gold), 1)
        self.assertEqual(gold[0].get('username'), 'delta-user')

        self.assertEqual(len(silver), 3)
        self.assertEqual(silver[0].get('username'), 'alpha-user')
        self.assertEqual(silver[1].get('username'), 'charlie-user')
        self.assertEqual(silver[2].get('username'), 'bravo-user')

        self.assertEqual(len(bronze), 1)
        self.assertEqual(bronze[0].get('username'), 'echo-user')


    if __name__ == '__main__':
        unittest.main()