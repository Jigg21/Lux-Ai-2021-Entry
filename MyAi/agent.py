import logging
from lux import game
import math, sys
import time
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES,Position
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from Ai import bevhaviorTree as bt
DIRECTIONS = Constants.DIRECTIONS
game_state = None


def agent(observation, configuration):
    global game_state
    startTime = time.time()

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
    gameInfo["gameState"] = game_state
    gameInfo["FriendlyUnits"] = player.units
    gameInfo["ActionsArray"] = actions
    gameInfo["Player"] = player
    resource_tiles: list[Cell] = []
    tileYields = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            tileYields.append(((x,y),countAdjacentResources(x,y)))
            if cell.has_resource():
                resource_tiles.append(cell)
    gameInfo["ResourceTiles"] = resource_tiles
    gameInfo["ResourceYields"] = tileYields
    #traverse the behavior tree
    bt.aiTree.traverse(gameInfo)
    
    logging.info("Executed in {time} seconds".format(time=(time.time()-startTime)))
    return actions

def countAdjacentResources(pos):
    result  = 0
    adjacentPositions = [
            Position(clamp(0, game_state.map.width,pos.x),clamp(0,game_state.map.height,pos.y-1)),
            Position(clamp(0,game_state.map.width,pos.x+1),clamp(0,game_state.map.height,pos.y)),
            Position(pos.x,pos.y),
            Position(clamp(0,game_state.map.width,pos.x-1),clamp(0,game_state.map.height,pos.y)),
            Position(clamp(0,game_state.map.width,pos.x),clamp(0,game_state.map.height,pos.y+1))
    ]

    for pos in adjacentPositions:
        if game_state.map.get_cell_by_pos(pos):
            result +=1
    return result

def countAdjacentResources(x,y):
    result  = 0
    pos = Position(x,y)
    adjacentPositions = [
            Position(clamp(0, game_state.map.width,pos.x),clamp(0,game_state.map.height,pos.y-1)),
            Position(clamp(0,game_state.map.width,pos.x+1),clamp(0,game_state.map.height,pos.y)),
            Position(pos.x,pos.y),
            Position(clamp(0,game_state.map.width,pos.x-1),clamp(0,game_state.map.height,pos.y)),
            Position(clamp(0,game_state.map.width,pos.x),clamp(0,game_state.map.height,pos.y+1))
    ]

    for pos in adjacentPositions:
        if game_state.map.get_cell_by_pos(pos):
            result +=1
    return result

#Clamp a value to range (min,max)
def clamp(min,max,value):
    max -=1
    if value < min:
        return min
    if value > max:
        return max
    return value
