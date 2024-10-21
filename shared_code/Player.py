import json

class Player:
    def __init__(self, id, username, password, games_played, total_score):
        self.id = id
        self.username = username
        self.password = password
        self.games_played = games_played
        self.total_score = total_score

    def __str__(self):
        return f"Player: {self.id}, {self.username}, {self.password}, {self.games_played}, {self.total_score}"
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "games_played": self.games_played,
            "total_score": self.total_score
        }
    
    def to_json(self):
        # TODO: check if valid to schema

        return json.dumps(self.to_dict())
    
    # TODO: check if fields are valid to schema