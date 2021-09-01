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
    pass

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

#base class for each node in the tree
class node():
    nodeType = None
    def __init__(self):
        self.parent = None
        self.nodeStatus = NodeStatus.UNEXPLORED
        self.children = []

    def setParent(self,parent):
        self.parent = parent

    def activate(self,data):
        pass

    def activate(self,data,unit):
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

#base class for action type nodes
class actionNode(node):
    nodeType = NodeTypes.ACTION
    def activate(self, data, unit):
        pass

class node_Sequence(node):
    nodeType = NodeTypes.SEQUENCE
    def activate(self, data):
        for node in self.children:
            result = node.activate(data)
            if result != NodeStatus.SUCCEEDED:
                return result
        return NodeStatus.SUCCEEDED
    
    def activate(self, data,unit):
        for node in self.children:
            result = node.activate(data,unit)
            if result != NodeStatus.SUCCEEDED:
                return result
        return NodeStatus.SUCCEEDED

#return success if one returns success
class node_FallBack(node):
    
    def activate(self, data):
        for child in self.children:
            result = child.activate(data)
            if result == NodeStatus.SUCCEEDED:
                return NodeStatus.SUCCEEDED
            if result == NodeStatus.WAITING:
                return NodeStatus.WAITING
        return NodeStatus.FAILED

#fallback nodes for actions
class node_actionFallBack(actionNode):
    def activate(self, data, unit):
        for child in self.children:
            result = child.activate(data,unit)
            if result == NodeStatus.SUCCEEDED:
                return NodeStatus.SUCCEEDED
            if result == NodeStatus.WAITING:
                return NodeStatus.WAITING
        return NodeStatus.FAILED
    
class node_ActionSequence(node):
    nodeType = NodeTypes.SEQUENCE
    def __init__(self):
        super().__init__()
        self.sequenceCounter = 0

    def activate(self, data,unit):
        self.sequenceCounter = 0
        while self.sequenceCounter <= len(self.children):
            result = self.children[self.sequenceCounter].activate(data,unit)
            if (result == NodeStatus.SUCCEEDED):
                self.sequenceCounter += 1
            else:
                return result
        return NodeStatus.SUCCEEDED

#Is the game over
class node_isGameOver(node):
    def activate(self, data):
        if data["gameState"].turn >= 360:
            self.NodeStatus = NodeStatus.SUCCEEDED
            return NodeStatus.SUCCEEDED
        else:
            return NodeStatus.FAILED

#tick child for every unit
class node_AllUnitsDec(node):
    nodeType = NodeTypes.DECORATOR
    def activate(self, data):
        for unit in data["FriendlyUnits"]:
            self.children[0].activate(data,unit)
        return NodeStatus.SUCCEEDED

#returns either succeeded or waiting
class node_TerminateOrWait(node):
    nodeType = NodeTypes.DECORATOR
    def activate(self, data):
        result = self.children[0].activate(self,data)
        if result == NodeStatus.WAITING:
            return NodeStatus.WAITING
        else:
            return NodeStatus.SUCCEEDED
    
    def activate(self, data,unit):
        result = self.children[0].activate(self,data,unit)
        if result == NodeStatus.WAITING:
            return NodeStatus.WAITING
        else:
            return NodeStatus.SUCCEEDED

#a single coordinate literal
class node_coordinateLiteral(node):
    nodeType = NodeTypes.VALUE
    def __init__(self,coordinates):
        super().__init__()
        self.coordinate = coordinates
    def __init__(self,x,y):
        super().__init__()
        self.coordinate = Position(x,y)

    def activate(self, data):
        return self.coordinate
    
    
    def activate(self, data,unit):
        return self.coordinate

#move a unit to a specific target
class node_UnitGoTo(actionNode):
    def __init__(self,adjacent=False):
        super().__init__()
        self.adjacent = adjacent

    def activate(self, data,unit):
        #coordinateData
        target = self.children[0].activate(data,unit)
        if unit.pos == target or (unit.pos.is_adjacent(target) and self.adjacent):
            return NodeStatus.SUCCEEDED

        if unit.cooldown > 0:
            return NodeStatus.WAITING
        else:
            if target.x > unit.pos.x:
                data["ActionsArray"].append(unit.move('e'))
                return NodeStatus.WAITING
            elif target.x < unit.pos.x:
                data["ActionsArray"].append(unit.move('w'))
                return NodeStatus.WAITING

            if target.y > unit.pos.y:
                data["ActionsArray"].append(unit.move('s'))
                return NodeStatus.WAITING
            elif target.y < unit.pos.y:
                data["ActionsArray"].append(unit.move('n'))
                return NodeStatus.WAITING

            return NodeStatus.SUCCEEDED

#wait until unit's cargo is full
class node_mineUntilFull(actionNode):

    def adjacentResources(self,data,unit):
        posN = Position(unit.pos.x,unit.pos.y+1)
        posE = Position(unit.pos.x+1,unit.pos.y)
        posC = Position(unit.pos.x,unit.pos.y)
        posW = Position(unit.pos.x-1,unit.pos.y)
        posS = Position(unit.pos.x,unit.pos.y-1)
        result = data["gameState"].map.get_cell_by_pos(posN).has_resource()
        result = result or data["gameState"].map.get_cell_by_pos(posE).has_resource()
        result = result or data["gameState"].map.get_cell_by_pos(posC).has_resource()
        result = result or data["gameState"].map.get_cell_by_pos(posW).has_resource()
        result = result or data["gameState"].map.get_cell_by_pos(posS).has_resource()
        return result

    def activate(self, data, unit):
        if unit.get_cargo_space_left() <= 0:
            return NodeStatus.SUCCEEDED
        elif not self.adjacentResources(data,unit):
            return NodeStatus.FAILED
        else:
            return NodeStatus.WAITING
        
#returns coordinates of the closest resource
class node_getClosestResource(actionNode):
     def activate(self, data, unit):
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
            return None
#New Line