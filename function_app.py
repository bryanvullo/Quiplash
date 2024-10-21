import azure.functions as func
import logging

app = func.FunctionApp()

# TODO - add uniqueness in player username
# TODO - player "id" partition key
# TODO - prompt "username" partition key

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
    
@app.route(route="player/register", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def registerPlayer(req: func.HttpRequest) -> func.HttpResponse:
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
