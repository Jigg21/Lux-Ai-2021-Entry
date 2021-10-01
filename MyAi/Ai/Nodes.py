from os import supports_bytes_environ
from tkinter.constants import NORMAL
from lux import annotate
import enum
from tkinter import NoDefaultRoot
from typing import Sequence
import logging
from lux.game_map import Position
from lux.constants import Constants
import math

logging.basicConfig(filename='debug.log', encoding='utf-8', level=logging.DEBUG,filemode="w")
logging.info("Begining Log")

class NodeHeirarchyError(Exception):
    def __init__(self, *args: object):
        super().__init__(*args)
        self.message = "Tree heirarchy rules broken! Decorator nodes should only have one child!"

class SubtreeChildAssignmentError:
    def __init__(self):
        self.message = "Attempted to add child node to subtree."

class MissingUnitInformationError:
    def __init__(self):
        self.message = "A node which needed unit information did not get it"

#what kind of node is this
class NodeTypes(enum.Enum):
    #returns some value or condition
    VALUE = 1
    #each of it's children will be done in order 
    SEQUENCE = 2
    #some specific action that the ai can take, requires specifying unit
    ACTION = 3
    #returns success
    FALLBACK = 4
    #Have one child only
    DECORATOR = 5

#has the node been explored, if so what was the result?
class NodeStatus(enum.Enum):
    #completed it's task or check
    SUCCEEDED = 1
    #failed it's task or check
    FAILED = 2
    #task is in progress, wait for result
    WAITING = 3
    
    UNEXPLORED = 4

#how should adjacency be handled
class AdjacentPerams(enum.Enum):
    #must be the exact square
    EXACT = 1
    #excludes diagonals
    STRICT = 2
    #normal adjacency
    NORMAL = 3

#base class for each node in the tree
class node():
    nodeType = None
    def __init__(self,name):
        self.name = name
        self.parent = None
        self.nodeStatus = NodeStatus.UNEXPLORED
        self.children = []

    def setParent(self,parent):
        self.parent = parent

    def activate(self,data):
        logging.debug(self.name)
        pass

    def addChild(self,child):
        if self.nodeType == NodeTypes.DECORATOR and len(self.children) == 1:
            raise NodeHeirarchyError
        self.children.append(child)
        child.parent = self

    #insert a decorator node between two nodes
    def addDecorator(self,decorator):
        decorator = decorator()
        decorator.setParent = self.parent
        self.parent.children.remove(self)
        self.parent.addChild(decorator)
        decorator.addChild(self)

#Ticks each child in order
class node_Sequence(node):
    nodeType = NodeTypes.SEQUENCE
    def activate(self, data):
        super().activate(data)
        for node in self.children:
            result = node.activate(data)
            if result != NodeStatus.SUCCEEDED:
                return result
        return NodeStatus.SUCCEEDED

#return success if at least one child returns success
class node_FallBack(node):
    
    def activate(self, data):
        super().activate(data)
        for child in self.children:
            result = child.activate(data)
            if result == NodeStatus.SUCCEEDED:
                return NodeStatus.SUCCEEDED
            if result == NodeStatus.WAITING:
                return NodeStatus.WAITING
        return NodeStatus.FAILED
    
#Is the game over
class node_isGameOver(node):
    def activate(self, data):
        super().activate(data)
        if data["gameState"].turn >= 360:
            self.NodeStatus = NodeStatus.SUCCEEDED
            return NodeStatus.SUCCEEDED
        else:
            return NodeStatus.FAILED

#tick child for every unit
class node_AllUnitsDec(node):
    nodeType = NodeTypes.DECORATOR
    def activate(self, data):
        super().activate(data)
        for unit in data["FriendlyUnits"]:
            data["CurrentUnit"] = unit
            self.children[0].activate(data)
        return NodeStatus.SUCCEEDED

#returns either succeeded or waiting
class node_TerminateOrWait(node):
    nodeType = NodeTypes.DECORATOR
    def activate(self, data):
        super().activate(data)
        result = self.children[0].activate(self,data)
        if result == NodeStatus.WAITING:
            return NodeStatus.WAITING
        else:
            return NodeStatus.SUCCEEDED
    
#pass a coordinate literal
class node_coordinateLiteral(node):
    nodeType = NodeTypes.VALUE
    def __init__(self,name,coordinates):
        super().__init__(name)
        self.coordinate = coordinates

    def __init__(self,name,x,y):
        super().__init__(name)
        self.coordinate = Position(x,y)

    def activate(self, data):
        super().activate(data)
        return self.coordinate

#move a unit to coordinates from child node
class node_UnitGoTo(node):
    #adjacent: if the agent can stop when adjacent to location
    def __init__(self,name,adjacent=AdjacentPerams.EXACT):
        super().__init__(name)
        self.adjacent = adjacent

    def activate(self, data):
        super().activate(data)
        unit = data["CurrentUnit"]
        #position object representing target location
        target = self.children[0].activate(data)
        data["ActionsArray"].append(annotate.circle(target.x,target.y))
        #return success when the unit reaches position
        if unit.pos == target and self.adjacent == AdjacentPerams.EXACT:
            logging.debug("Arrived")
            return NodeStatus.SUCCEEDED
        if  unit.pos.is_adjacent(target) and self.adjacent == AdjacentPerams.NORMAL:
            logging.debug("Arrived")
            return NodeStatus.SUCCEEDED
        if isStrictlyAdjacent(target,unit.pos) and self.adjacent == AdjacentPerams.STRICT:
            logging.debug("Arrived")
            return NodeStatus.SUCCEEDED

        

        #if the unit can act
        if unit.can_act():
            #go to it
            logging.debug("Moving")
            data["ActionsArray"].append(unit.move(unit.pos.direction_to(target)))

        return NodeStatus.WAITING

#wait until unit's cargo is full
class node_mineUntilFull(node):

    def adjacentResources(self,data,unit):
        posN = Position(clamp(0,data["gameState"].map.width,unit.pos.x),clamp(0,data["gameState"].map.height,unit.pos.y-1))
        posE = Position(clamp(0,data["gameState"].map.width,unit.pos.x+1),clamp(0,data["gameState"].map.height,unit.pos.y))
        posC = Position(unit.pos.x,unit.pos.y)
        posW = Position(clamp(0,data["gameState"].map.width,unit.pos.x-1),clamp(0,data["gameState"].map.height,unit.pos.y))
        posS = Position(clamp(0,data["gameState"].map.width,unit.pos.x),clamp(0,data["gameState"].map.height,unit.pos.y+1))

        result = data["gameState"].map.get_cell_by_pos(posN).has_resource()
        result = result or data["gameState"].map.get_cell_by_pos(posE).has_resource()
        result = result or data["gameState"].map.get_cell_by_pos(posC).has_resource()
        result = result or data["gameState"].map.get_cell_by_pos(posW).has_resource()
        result = result or data["gameState"].map.get_cell_by_pos(posS).has_resource()
        return result

    def activate(self, data):
        super().activate(data)
        unit = data["CurrentUnit"]
        if unit.get_cargo_space_left() <= 0:
            logging.debug("Full Cargo")
            return NodeStatus.SUCCEEDED
        elif not self.adjacentResources(data,unit):
            logging.debug("No Resources Left")
            return NodeStatus.FAILED
        else:
            logging.debug("Getting Resources")
            return NodeStatus.WAITING
        
#returns coordinates of the closest resource
class node_getClosestResource(node):
     def activate(self, data):
        super().activate(data)
        unit = data["CurrentUnit"]
        closest_dist = math.inf
        closest_resource_tile = None
        for resource_tile in data["ResourceTiles"]:
            if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not data["Player"].researched_coal(): continue
            if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not data["Player"].researched_uranium(): continue
            dist = resource_tile.pos.distance_to(unit.pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_resource_tile = resource_tile
        if closest_resource_tile is not None:
            return closest_resource_tile.pos
        else:
            logging.warn("CAN'T FIND RESOURCES")
            return None

class node_getBestResource(node):
    def countAdjacentResources(self,data,unit):
        posN = Position(clamp(0,data["gameState"].map.width,unit.pos.x),clamp(0,data["gameState"].map.height,unit.pos.y-1))
        posE = Position(clamp(0,data["gameState"].map.width,unit.pos.x+1),clamp(0,data["gameState"].map.height,unit.pos.y))
        posC = Position(unit.pos.x,unit.pos.y)
        posW = Position(clamp(0,data["gameState"].map.width,unit.pos.x-1),clamp(0,data["gameState"].map.height,unit.pos.y))
        posS = Position(clamp(0,data["gameState"].map.width,unit.pos.x),clamp(0,data["gameState"].map.height,unit.pos.y+1))

        result = data["gameState"].map.get_cell_by_pos(posN).has_resource()
        result = result or data["gameState"].map.get_cell_by_pos(posE).has_resource()
        result = result or data["gameState"].map.get_cell_by_pos(posC).has_resource()
        result = result or data["gameState"].map.get_cell_by_pos(posW).has_resource()
        result = result or data["gameState"].map.get_cell_by_pos(posS).has_resource()
        return result

    def activate(self, data):
        super().activate(data)
        unit = data["CurrentUnit"]


#get coordinates of the closest city
class node_getClosestCity(node):
    def activate(self, data):
        super().activate(data)
        unit = data["CurrentUnit"]
        if len(data["Player"].cities) > 0:
            closest_dist = math.inf
            closest_city_tile = None
            for k, city in data["Player"].cities.items():
                for city_tile in city.citytiles:
                    dist = city_tile.pos.distance_to(unit.pos)
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_city_tile = city_tile
            return  closest_city_tile.pos

#is a unit's cargo empty?
class node_emptyCargo(node):
    nodeType = NodeTypes.VALUE
    def adjacentCities(self,data,unit):
        posN = Position(unit.pos.x,unit.pos.y+1)
        posE = Position(unit.pos.x+1,unit.pos.y)
        posC = Position(unit.pos.x,unit.pos.y)
        posW = Position(unit.pos.x-1,unit.pos.y)
        posS = Position(unit.pos.x,unit.pos.y-1)
        result = data["gameState"].map.get_cell_by_pos(posN).citytile != None
        result = result or data["gameState"].map.get_cell_by_pos(posE).citytile != None
        result = result or data["gameState"].map.get_cell_by_pos(posC).citytile != None
        result = result or data["gameState"].map.get_cell_by_pos(posW).citytile != None
        result = result or data["gameState"].map.get_cell_by_pos(posS).citytile != None
        return result

    def activate(self, data):
        super().activate(data)
        unit = data["CurrentUnit"]
        if unit.cargo.wood + unit.cargo.coal + unit.cargo.uranium <= 0:
            logging.debug("All Cargo Dropped")
            return NodeStatus.SUCCEEDED
        elif data["gameState"].map.get_cell_by_pos(unit.pos).citytile == None:
            logging.debug("Not on a city!")
            return NodeStatus.FAILED
        else:
            return NodeStatus.WAITING

class node_placeCity(node):
    def activate(self, data):
        super().activate(data)
        unit = data["CurrentUnit"]
        #if the unit can build a city tile do it
        if unit.can_build():
            data["ActionsArray"].append(unit.build_city())
            
            return NodeStatus.SUCCEEDED
        else:
            return NodeStatus.WAITING

#base class for the subtree classes
class subTree(node):
    def __init__(self,name):
        super().__init__(name)
    
    def activate(self, data):         
        return self.rootNode.activate(data)
    
    def addChild(self, child):
        raise SubtreeChildAssignmentError
    
#subtree that orders unit to return to the nearest city until cargo is empty
class subTree_dumpResources(subTree):
    def __init__(self,name):
        super().__init__(name)
        
        self.rootNode = node_FallBack("Fallback")
        gotoNode = node_UnitGoTo("Go to",AdjacentPerams.EXACT)
        coordinateNode = node_getClosestCity("Closest City")
        emptyCargoNode = node_emptyCargo("Empty Cargo")

        self.rootNode.addChild(emptyCargoNode)
        self.rootNode.addChild(gotoNode)
        gotoNode.addChild(coordinateNode)

#subtree that orders a unit to gather resources until their inventories are full       
class subTree_gatherResources(subTree):
    def __init__(self,name):
        super().__init__(name)
        self.rootNode = node_FallBack("Mine Until Full")
        gotoNode = node_UnitGoTo("Go to nearest Resource",AdjacentPerams.NORMAL)
        coordinateNode = node_getClosestResource("Get Closest Resource")
        fullCargoNode = node_mineUntilFull("Gather Resources")
        self.rootNode.addChild(fullCargoNode)
        self.rootNode.addChild(gotoNode)
        gotoNode.addChild(coordinateNode)

        
    
    def activate(self, data):
        super().activate(data)            
        return self.rootNode.activate(data)

    def addChild(self, child):
        raise SubtreeChildAssignmentError

class subTree_expandCity(subTree):
    def __init__(self,name):
        super().__init__(name)
        self.rootNode = node_Sequence("Expand City")
        gatherResources = subTree_gatherResources("Gather Resources")
        gotoNode = node_UnitGoTo("Go to nearest City",adjacent=NORMAL)
        cityCoordinates = node_getClosestCity("Find Closest City")
        placeCity = node_placeCity("Place City Tile")

        self.rootNode.addChild(gatherResources)
        self.rootNode.addChild(gotoNode)
        gotoNode.addChild(cityCoordinates)
        self.rootNode.addChild(placeCity)


def isStrictlyAdjacent(pos1,pos2):
    if pos2.equals(Position(pos1.x+1,pos1.y)):
        return True
    if pos2.equals(Position(pos1.x-1,pos1.y)):
        return True
    if pos2.equals(Position(pos1.x,pos1.y+1)):
        return True
    if pos2.equals(Position(pos1.x,pos1.y-1)):
        return True
    return False

#Clamp a value to range (min,max)
def clamp(min,max,value):
    if value < min:
        return min
    if value > max:
        return max
    return value
