from lux import game
import math, sys
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from Ai import bevhaviorTree as bt
DIRECTIONS = Constants.DIRECTIONS
game_state = None


def agent(observation, configuration):
    global game_state
    
    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])
    
    actions = []

    ### AI Code goes down here! ### 
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height
    #Create a dictionary of game info the ai needs
    gameInfo = dict()
    gameInfo["Turn"] = game_state.turn
    gameInfo["FriendlyUnits"] = player.units
    gameInfo["ActionsArray"] = actions
    gameInfo["Player"] = player
    resource_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)
    gameInfo["ResourceTiles"]
    # we iterate over all our units and do something with them
    bt.aiTree.traverse(gameInfo)
    # you can add debug annotations using the functions in the annotate object
    
    
    return actions
