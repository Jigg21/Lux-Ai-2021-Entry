import enum
from tkinter.constants import UNITS
from typing import Sequence
from . import Nodes

#class that represents the entire tree
class behaviorTree():
    rootNode = None

    def __init__(self):
        self.rootNode = Nodes.node_FallBack()
        self.addNode(self.rootNode,Nodes.node_isGameOver())
    
    def traverse(self,data):
        self.rootNode.activate(data)
    
    def addNode(self,parent,child):
        parent.addChild(child)
        child.setParent(parent)



aiTree = behaviorTree()
gotoNode = Nodes.node_UnitGoTo(adjacent=True)
aiTree.addNode(aiTree.rootNode,gotoNode)
coordinateNode = Nodes.node_coordinateLiteral(0,0)
gotoNode.addChild(coordinateNode)
gotoNode.addDecorator(Nodes.node_AllUnitsDec)



