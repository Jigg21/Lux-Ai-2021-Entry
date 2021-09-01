import enum
from logging import debug
import logging
from tkinter.constants import UNITS
from typing import Sequence
from . import Nodes

#class that represents the entire tree
class behaviorTree():
    rootNode = None

    def __init__(self):
        self.rootNode = Nodes.node_FallBack()
        self.rootNode.addChild(Nodes.node_isGameOver())
    
    def traverse(self,data):
        self.rootNode.activate(data)
    




aiTree = behaviorTree()
SequenceNode = Nodes.node_Sequence()
allUnitsDec =  Nodes.node_AllUnitsDec()
aiTree.rootNode.addChild(allUnitsDec)
allUnitsDec.addChild(SequenceNode)


fallbackNode = Nodes.node_actionFallBack()
SequenceNode.addChild(fallbackNode)

fullCargoNode = Nodes.node_mineUntilFull()
fallbackNode.addChild(fullCargoNode)

gotoNode = Nodes.node_UnitGoTo()
fallbackNode.addChild(gotoNode)
coordinateNode = Nodes.node_getClosestResource()
gotoNode.addChild(coordinateNode)





gotoOriginNode = Nodes.node_UnitGoTo(adjacent=True)
gotoOriginNode.addChild(Nodes.node_coordinateLiteral(0,0))
SequenceNode.addChild(gotoOriginNode)


