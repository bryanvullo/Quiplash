import azure.functions as func
import logging
import json
import os
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
import requests

app = func.FunctionApp()

# TODO - update local.settings.json with OpenAI keys and function keys

# TODO: prompt limit in translation doent not apply
# TODO: ask if there are boundaries to score_to_add and game_to_add
# TODO: return error?? line 144 len(list(result)) > 1
# TODO: do we use the native language characters or the English characters for the languages?

MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
QuiplashDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
PlayerContainerProxy = QuiplashDBProxy.get_container_client(os.environ['PlayerContainerName'])
PromptContainerProxy = QuiplashDBProxy.get_container_client(os.environ['PromptContainerName'])

# Translation Serive
TranslationEndpoint = os.environ['TranslationEndpoint']
TranslationKey = os.environ['TranslationKey']
TranslationRegion = os.environ['TranslationRegion']
# English, Irish, Spanish, Hindi, Chinese Simplified and Polish
SupportedLanguages = ["en", "ga", "es", "hi", "zh-Hans", "pl"]

@app.route(route="myFirstFunction", auth_level=func.AuthLevel.ANONYMOUS)
def myFirstFunction(req: func.HttpRequest) -> func.HttpResponse:
    
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "Please enter a name",
             status_code=200
        )
    
@app.route(route="player/register", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def registerPlayer(req: func.HttpRequest) -> func.HttpResponse:
    """
    registers player with username and password
    """
    logging.info('Python HTTP trigger function processed a request. Register Player')

    input = json.loads( req.get_json() )
    username = input['username']
    password = input['password']

    # check if username and password are valid
    if len(username) < 5 or len(username) > 15:
        return func.HttpResponse(
            body = json.dumps({"result": False, "msg": "Username less than 5 characters or more than 15 characters" }),
            status_code=400
        )
    if len(password) < 8 or len(password) > 15:
        return func.HttpResponse(
            body = json.dumps({"result": False, "msg": "Password less than 8 characters or more than 15 characters" }),
            status_code=400
        )
    
    # check if username already exists
    result = PlayerContainerProxy.query_items(
        query='SELECT * FROM player WHERE player.username = @username',
        parameters=[dict(name='@username', value=username)],
        enable_cross_partition_query=True
    )
    if len(list(result)) > 0:
        return func.HttpResponse(
            body = json.dumps({"result": False, "msg": "Username already exists" }),
            status_code=400
        )

    # create player in DB, set GP ans TS to 0
    playerDict = {
        "username" : username,
        "password" : password,
        "games_played" : 0,
        "total_score" : 0
    }
    PlayerContainerProxy.create_item(body=playerDict, enable_automatic_id_generation=True)
    return func.HttpResponse(
        body = json.dumps({"result": True, "msg": "OK" }),
        status_code=200
    )

@app.route(route="player/login", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def loginPlayer(req: func.HttpRequest) -> func.HttpResponse:
    """
    logs in player with username and password
    """
    logging.info('Python HTTP trigger function processed a request. Login Player')

    input = json.loads( req.get_json() )
    username = input['username']
    password = input['password']

    # check if username and password match in DB
    result = PlayerContainerProxy.query_items(
        query='SELECT * FROM player WHERE player.username = @username AND player.password = @password',
        parameters=[dict(name='@username', value=username), dict(name='@password', value=password)],
        enable_cross_partition_query=True
    )

    if len(list(result)) == 0:
        return func.HttpResponse(
            body = json.dumps({"result": False, "msg": "Username or password incorrect" }),
            status_code=401
        )
    
    return func.HttpResponse(
        body = json.dumps({"result": True, "msg": "OK" })
    )

@app.route(route="player/update", auth_level=func.AuthLevel.FUNCTION, methods=["PUT"])
def updatePlayer(req: func.HttpRequest) -> func.HttpResponse:
    """
    updates player's games_played and total_score
    """
    logging.info('Python HTTP trigger function processed a request. Update Player')

    input = json.loads( req.get_json() )
    username = input['username']
    game_to_add = input['add_to_games_played']
    score_to_add = input['add_to_score']

    # check if username exists in DB
    result = PlayerContainerProxy.query_items(
        query='SELECT * FROM player WHERE player.username = @username',
        parameters=[dict(name='@username', value=username)],
        enable_cross_partition_query=True
    )
    result = list(result)
    if len(result) == 0:
        return func.HttpResponse(
            body = json.dumps({"result": False, "msg": "Player does not exist" }),
            status_code=400
        )
    elif len(result) > 1:
        # TODO: return error??
        pass
    logging.info('Update Player: Player exists')
    
    # get player's games_played and total_score
    player = json.loads(json.dumps(result[0]))
    player_id = player['id']
    player['games_played'] += game_to_add
    player['total_score'] += score_to_add

    # update player in DB
    PlayerContainerProxy.replace_item(
        item=player_id,
        body=player
    )

    logging.info('Update Player: Player updated')

    return func.HttpResponse(
        body = json.dumps({"result": True, "msg": "OK" }),
        status_code=200
    )

@app.route(route="prompt/create", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def createPrompt(req: func.HttpRequest) -> func.HttpResponse:
    """
    Creates prompt for player (username) and adds it and its translations to the DB
    """
    logging.info('Python HTTP trigger function processed a request. Create Prompt')

    input = json.loads(req.get_json())
    text = input['text']
    username = input['username']

    # check if username exists in DB
    result = PlayerContainerProxy.query_items(
        query='SELECT * FROM player WHERE player.username = @username',
        parameters=[dict(name='@username', value=username)],
        enable_cross_partition_query=True
    )
    result = list(result)
    if len(result) == 0:
        return func.HttpResponse(
            body = json.dumps({"result": False, "msg": "Player does not exist" }),
            status_code=400
        )
    elif len(result) > 1:
        # TODO: return error??
        pass
    logging.info('Prompt Create: Player exists')

    # check if prompt text is valid (length 20 - 100)
    if len(text) < 20 or len(text) > 100:
        return func.HttpResponse(
                body = json.dumps({"result": False, "msg": "Prompt less than 20 characters or more than 100 characters" }),
                status_code=400
            )
    logging.info('Prompt Create: Prompt text is of valid length')

    # check if language is supported (Azure Text Translation service)
    detectURL = TranslationEndpoint + "detect"
    params = {"api-version": "3.0"}
    headers = {
        "Ocp-Apim-Subscription-Key": TranslationKey,
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Region": TranslationRegion
    }
    body = [{"text": text}]
    detectionRequest = requests.post(detectURL, params=params, headers=headers, json=body)
    detectionResponse = detectionRequest.json()
    lang = detectionResponse[0]['language']
    if lang not in SupportedLanguages:
        return func.HttpResponse(
                body = json.dumps({"result": False, "msg": "Unsupported language" }),
                status_code=400
            )
    logging.info(f'Prompt Create: Language is supported {lang}')
    
    # translate prompt to all supported languages
    languagesToTranslate = SupportedLanguages.copy()
    languagesToTranslate.remove(lang)
    translateURL = TranslationEndpoint + "translate"
    params = {
        "api-version": "3.0",
        "from": lang,
        "to": languagesToTranslate
    }
    headers = {
        "Ocp-Apim-Subscription-Key": TranslationKey,
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Region": TranslationRegion
    }
    body = [{"text": text}]
    translationRequest = requests.post(translateURL, params=params, headers=headers, json=body)
    translationResponse = translationRequest.json()
    translations = translationResponse[0]['translations']
    logging.info('Prompt Create: Prompt translated, inserting into DB')

    # prepare document to insert into DB
    texts = [{"language": lang, "text": text}]
    for translation in translations:
        translationDict = {"language": translation['to'], "text": translation['text']}
        texts.append(translationDict)
    promptDict = {"username": username, "texts": texts}

    # insert prompt and translations into DB
    PromptContainerProxy.create_item(body=promptDict, enable_automatic_id_generation=True)
    return func.HttpResponse(
        body = json.dumps({"result": True, "msg": "OK" }),
        status_code=200
    )

@app.route(route="prompt/suggest", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def suggestPrompt(req: func.HttpRequest) -> func.HttpResponse:
    """
    Uses Azure OpenAI service to suggest prompt that includes keyword
    """
    logging.info('Python HTTP trigger function processed a request. Suggest Prompt')

    input = req.get_json()
    keyword = input.get('keyword')

    # TODO: use Azure OpenAI service to suggest prompt - prompt must include keyword
    suggestion = "SUGGESTED PROMPT"
    # TODO: check if suggestion is valid (length 20 - 100)
    return func.HttpResponse(
            body = json.dumps({"suggestion" : suggestion})
        )

@app.route(route="prompt/delete", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def deletePrompt(req: func.HttpRequest) -> func.HttpResponse: 
    """
    deletes all prompts authored by player (username)
    assume player exists
    """
    logging.info('Python HTTP trigger function processed a request. Delete Prompt')

    input = req.get_json()
    username = input.get('username')

    count = 0
    # TODO: get all prompts authored by player and count

    # TODO: delete all prompts authored by player 
    return func.HttpResponse(
            body = json.dumps({"result": True, "msg": f"{count} prompts deleted" })
        )

@app.route(route="utils/get", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def getUtils(req: func.HttpRequest) -> func.HttpResponse:
    """
    returns a list of all prompts' text in a given language created by players in the list
    if player does not exist, skip. if player doesn't have any prompts, skip.
    assumes valid language
    """
    logging.info('Python HTTP trigger function processed a request. Get Utils')

    input = req.get_json()
    players = input.get('players')
    language = input.get('language')

    prompts = []
    # [{id, text, username}]

    for player in players:
        # TODO: get all prompts authored by player in language
        # TODO: append to prompts
        pass

    return func.HttpResponse(
            body = json.dumps({prompts})
        )

@app.route(route="utils/podium", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def getPodium(req: func.HttpRequest) -> func.HttpResponse:
    """
    returns a distionary of lists of players with the top 3 points per game ration (ppgr = total_score/games_played)
    if same ppgr, sort by increasing number of games, then increasing alphabetical order of username
    """
    logging.info('Python HTTP trigger function processed a request. Get Podium')

    # TODO: get all players

    # TODO: calculate ppgr for all players

    # TODO: sort players by ppgr

    # TODO: calculate gold silver and bronze players
    gold = []
    silver = []
    bronze = []

    return func.HttpResponse(
            body = json.dumps({
                "gold": gold, 
                "silver": silver, 
                "bronze": bronze
                })
        )