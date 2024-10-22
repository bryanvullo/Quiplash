import azure.functions as func
import logging
import json

app = func.FunctionApp()

# TODO - add uniqueness in player username
# TODO - player "id" partition key
# TODO - prompt "username" partition key
# TODO - update local.settings.json with Azure Text Translation and OpenAI keys and function keys
# TODO - return appropriate status codes

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

    input = req.get_json()
    username = input.get('username')
    password = input.get('password')

    if len(username) < 5 or len(password) > 15:
        return func.HttpResponse(
            body = json.dumps({"result": False, "msg": "Username less than 8 characters or more than 15 characters" })
        )
    if len(password) < 8 or len(password) > 15:
        return func.HttpResponse(
            body = json.dumps({"result": False, "msg": "Password less than 8 characters or more than 15 characters" })
        )
    
    # TODO: check if username already exists

    # else
    # TODO create player in DB, set GP ans TS to 0
    return func.HttpResponse(
        body = json.dumps({"result": True, "msg": "OK" })
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

    # TODO: check if username and password match in DB
    # return func.HttpResponse(
    #         body = json.dumps({"result": False, "msg": "Username or password incorrect" })
    #     )
    
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

    # TODO: check if username exists in DB
    # return func.HttpResponse(
    #         body = json.dumps({"result": False, "msg": "Player does not exist" })
    #     )

    # TODO: update player in DB
    return func.HttpResponse(
        body = json.dumps({"result": True, "msg": "OK" })
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

    # TODO: check if username exists in DB
    # return func.HttpResponse(
    #         body = json.dumps({"result": False, "msg": "Player does not exist" })
    #    )

    # TODO: check if prompt text is valid (length 20 - 100)
    # TODO: ???ask about if prompt larger than 100 characters in translation???
    # return func.HttpResponse(
    #         body = json.dumps({"result": False, "msg": "Prompt less than 20 characters or more than 100 characters" })
    #     )

    # TODO: check if language is supported (Azure Text Translation service)
    # return func.HttpResponse(
    #         body = json.dumps({"result": False, "msg": "Unsupported language" })
    #     )

    # TODO: generate translated prompts in: (languages TBD)
    # TODO: store prompts in DB
    return func.HttpResponse(
            body = json.dumps({"result": True, "msg": "OK" })
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