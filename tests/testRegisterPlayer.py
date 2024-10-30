import unittest
import requests
import json
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from azure.cosmos import CosmosClient

from pathlib import Path

class TestRegisterPlayer(unittest.TestCase):   
    LOCAL_DEV_URL = "http://localhost:7071/player/register"
    PUBLIC_URL = "https://quiplash-2425-bv1g22.azurewebsites.net/player/register"
    TEST_URL = LOCAL_DEV_URL
    
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

    # boundary test cases
    shortUsernamePlayer = {
        # username less than 5 characters
        "username": "4chr",
        "password": "password123"
    }
    shortUsernameBoundaryPlayer = {
        # username IS 5 characters
        "username": "bryan",
        "password": "password123"
    }
    longUsernamePlayer = {
        # username more than 15 characters
        "username": "bryanvullo123456",
        "password": "password123"
    }
    longUsernameBoundaryPlayer = {
        # username IS 15 characters
        "username": "bryanvullo12345",
        "password": "password123"
    }
    shortPasswordPlayer = {
        "username": "bryanvullo",
        # password less than 8 characters
        "password": "pass123"
    }
    shortPasswordBoundaryPlayer = {
        "username": "bryanvullo",
        # password IS 8 characters
        "password": "password"
    }
    longPasswordPlayer = {
        "username": "bryanvullo",
        # password more than 15 characters
        "password": "password12345678"
    }
    longPasswordBoundaryPlayer = {
        "username": "bryanvullo",
        # password IS 15 characters
        "password": "password1234567"
    }

    def tearDown(self):
        for doc in self.PlayerContainerProxy.read_all_items():
          self.PlayerContainerProxy.delete_item(item=doc,partition_key=doc['id'])

    def test_register_valid_player(self):
        response = requests.post(self.TEST_URL, json=json.dumps(self.validPlayer), 
                                 headers={"x-functions-key": self.FunctionAppKey})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], True)
        self.assertEqual(response.json()["msg"], "OK")

    def test_register_short_username_player(self):
        response = requests.post(self.TEST_URL, json=json.dumps(self.shortUsernamePlayer))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["result"], False)
        self.assertEqual(response.json()["msg"], "Username less than 5 characters or more than 15 characters")
    
    def test_register_short_username_boundary_player(self):
        response = requests.post(self.TEST_URL, json=json.dumps(self.shortUsernameBoundaryPlayer))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], True)
        self.assertEqual(response.json()["msg"], "OK")

    def test_register_long_username_player(self):
        response = requests.post(self.TEST_URL, json=json.dumps(self.longUsernamePlayer))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["result"], False)
        self.assertEqual(response.json()["msg"], "Username less than 5 characters or more than 15 characters")

    def test_register_long_username_boundary_player(self):
        response = requests.post(self.TEST_URL, json=json.dumps(self.longUsernameBoundaryPlayer))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], True)
        self.assertEqual(response.json()["msg"], "OK")
    
    def test_register_short_password_player(self):
        response = requests.post(self.TEST_URL, json=json.dumps(self.shortPasswordPlayer))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["result"], False)
        self.assertEqual(response.json()["msg"], "Password less than 8 characters or more than 15 characters")
    
    def test_register_short_password_boundary_player(self):
        response = requests.post(self.TEST_URL, json=json.dumps(self.shortPasswordBoundaryPlayer))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], True)
        self.assertEqual(response.json()["msg"], "OK")
    
    def test_register_long_password_player(self):
        response = requests.post(self.TEST_URL, json=json.dumps(self.longPasswordPlayer))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["result"], False)
        self.assertEqual(response.json()["msg"], "Password less than 8 characters or more than 15 characters")
    
    def test_register_long_password_boundary_player(self):
        response = requests.post(self.TEST_URL, json=json.dumps(self.longPasswordBoundaryPlayer))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], True)
        self.assertEqual(response.json()["msg"], "OK")
    
    def test_register_existing_player(self):
        responseGood = requests.post(self.TEST_URL, json=json.dumps(self.validPlayer))
        responseBad = requests.post(self.TEST_URL, json=json.dumps(self.validPlayer))

        self.assertEqual(responseGood.status_code, 200)
        self.assertEqual(responseGood.json()["result"], True)
        self.assertEqual(responseGood.json()["msg"], "OK")

        self.assertEqual(responseBad.status_code, 400)
        self.assertEqual(responseBad.json()["result"], False)
        self.assertEqual(responseBad.json()["msg"], "Username already exists")

    def test_register_db_not_empty(self):
        response = requests.post(self.TEST_URL, json=json.dumps(self.validPlayer))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], True)
        self.assertEqual(response.json()["msg"], "OK")

        response = requests.post(self.TEST_URL, json=json.dumps(self.shortUsernameBoundaryPlayer))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], True)
        self.assertEqual(response.json()["msg"], "OK")

    if __name__ == '__main__':
        unittest.main()
