import azure.functions as func
import logging
import json
import os
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
import requests
from openai import AzureOpenAI

app = func.FunctionApp()

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

# OpenAI Service
OpenAIEndpoint = os.environ['OAIEndpoint']
OpenAIKey = os.environ['OAIKey']
OpenApiVersion = "2024-08-01-preview"
OpenAiClient = AzureOpenAI(azure_endpoint=OpenAIEndpoint, api_key=OpenAIKey, api_version=OpenApiVersion)
  
@app.route(route="player/register", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def registerPlayer(req: func.HttpRequest) -> func.HttpResponse:
    """
    registers player with username and password
    """
    logging.info('Python HTTP trigger function processed a request. Register Player')

    input = req.get_json()
    username = input.get('username')
    password = input.get('password')

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

    input = req.get_json()
    username = input.get('username')
    password = input.get('password')

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

    input = req.get_json()
    username = input.get('username')
    game_to_add = input.get('add_to_games_played')
    score_to_add = input.get('add_to_score')

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

    input = req.get_json()
    text = input.get('text')
    username = input.get('username')

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
    confidence = detectionResponse[0]['score']
    if lang not in SupportedLanguages or confidence < 0.2:
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

    logging.info(f"{OpenAIEndpoint}, {OpenAIKey}, {keyword}")

    # Use Azure OpenAI service to suggest prompt - prompt must include keyword and valid length
    suggestion = ""
    AIPrompt = f'''Can you suggest a prompt that includes the keyword '{keyword}'? 
        The prompt must be between 20 and 100 characters long. 
        Also, the prompt will used in a game of Quiplash. 
        Please only respond with a prompt, no other information.'''
    valid = False
    for i in range(4):
        if len(suggestion) >= 20 and len(suggestion) <= 100 and keyword in suggestion:
            valid = True
            break
        result = OpenAiClient.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": 
                    "Assistant is a large language model trained to generate Quiplash prompts."},
                {"role": "user", "content": AIPrompt}
            ]
        )
        suggestion = result.choices[0].message.content
    
    if not valid:
        return func.HttpResponse(
            body = json.dumps({"suggestion" : "Cannot generate suggestion" }),
            status_code=200
        )

    return func.HttpResponse(
            body = json.dumps({"suggestion" : suggestion}),
            status_code=200
        )

@app.route(route="prompt/delete", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def deletePrompt(req: func.HttpRequest) -> func.HttpResponse: 
    """
    deletes all prompts authored by player (username)
    assume player exists
    """
    logging.info('Python HTTP trigger function processed a request. Delete Prompt')

    input = req.get_json()
    username = input.get('player')
    count = 0

    # Get all prompts authored by player
    result = PromptContainerProxy.query_items(
        query='SELECT * FROM prompt WHERE prompt.username = @username',
        parameters=[dict(name='@username', value=username)],
        partition_key=username
    )
    
    # Delete all prompts authored by player, increment count
    for prompt in result:
        PromptContainerProxy.delete_item(item=prompt, partition_key=username)
        count += 1
 
    return func.HttpResponse(
            body = json.dumps({"result": True, "msg": f"{count} prompts deleted" }),
            status_code=200
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
    # [{prompt_id, text, username}]

    for player in players:
        # get all prompts authored by player in language
        result = PromptContainerProxy.query_items(
            query='SELECT * FROM prompt WHERE prompt.username = @username',
            parameters=[dict(name='@username', value=player)],
            partition_key=player
        )

        # get prompt text in specified language
        for doc in result:
            id = doc.get('id')
            texts = doc.get('texts')
            for text in texts:
                if text.get('language') == language:
                    # append to prompts
                    prompt = {"id": id, "text": text.get('text'), "username": player}
                    prompts.append(prompt)
                    break

    return func.HttpResponse(
            body = json.dumps(prompts),
            status_code=200
        )

@app.route(route="utils/podium", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def getPodium(req: func.HttpRequest) -> func.HttpResponse:
    """
    returns a dictionary of lists of players with the top 3 points per game ration (ppgr = total_score/games_played)
    if same ppgr, sort by increasing number of games, then increasing alphabetical order of username
    """
    logging.info('Python HTTP trigger function processed a request. Get Podium')

    # get all players
    players = PlayerContainerProxy.read_all_items()

    # calculate ppgr for all players
    # [(username, ppgr, games_played, total_score)]
    playerStats = []
    for player in players:
        username = player.get('username')
        games_played = player.get('games_played')
        total_score = player.get('total_score')
        if games_played == 0:
            ppgr = 0
        else:
            ppgr = total_score / games_played
        playerStats.append((username, ppgr, games_played, total_score))

    # sort players by ppgr, then games_played, then username
    sortedPlayers = sorted(playerStats, key=lambda x: (-x[1], x[2], x[0]))

    # calculate gold silver and bronze players
    gold = []
    silver = []
    bronze = []
    try:
        player = sortedPlayers.pop(0)
        goldPpgr = player[1]
        gold.append(player)
        while sortedPlayers[0][1] == goldPpgr:
            player = sortedPlayers.pop(0)
            gold.append(player)
    except IndexError:
        pass

    try:
        player = sortedPlayers.pop(0)
        silverPpgr = player[1]
        silver.append(player)
        while sortedPlayers[0][1] == silverPpgr:
            player = sortedPlayers.pop(0)
            silver.append(player)
    except IndexError:
        pass

    try:
        player = sortedPlayers.pop(0)
        bronzePpgr = player[1]
        bronze.append(player)
        while sortedPlayers[0][1] == bronzePpgr:
            player = sortedPlayers.pop(0)
            bronze.append(player)
    except IndexError:
        pass

    goldDict = [{"username":p[0], "games_played":p[2], "total_score":p[3]} for p in gold]
    silverDict = [{"username":p[0], "games_played":p[2], "total_score":p[3]} for p in silver]
    bronzeDict = [{"username":p[0], "games_played":p[2], "total_score":p[3]} for p in bronze]


    return func.HttpResponse(
            body = json.dumps({
                "gold": goldDict, 
                "silver": silverDict, 
                "bronze": bronzeDict
                }),
            status_code=200
        )