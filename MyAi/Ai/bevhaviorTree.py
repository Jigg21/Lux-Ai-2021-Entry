import enum
from logging import debug
import logging
from tkinter.constants import UNITS
from . import Nodes

#class that represents the entire tree
class behaviorTree():
    rootNode = None

    def __init__(self):
        self.rootNode = Nodes.node_FallBack("root")
        self.rootNode.addChild(Nodes.node_isGameOver("gameCheck"))
    
    def traverse(self,data):
        logging.info("===================Turn {num}===================".format(num=data["gameState"].turn))
        self.rootNode.activate(data)
    




aiTree = behaviorTree()
allUnitsDec =  Nodes.node_AllUnitsDec("All Units Node")
SequenceNode = Nodes.node_Sequence("Resource Collection")

mineUntilFullSubTree = Nodes.node_FallBack("Mine Until Full")
gotoNode = Nodes.node_UnitGoTo("Go to nearest Resource",Nodes.AdjacentPerams.STRICT)
coordinateNode = Nodes.node_getClosestResource("Get Closest Resource")
fullCargoNode = Nodes.node_mineUntilFull("Gather Resources")


aiTree.rootNode.addChild(allUnitsDec)
allUnitsDec.addChild(SequenceNode)
SequenceNode.addChild(mineUntilFullSubTree)
mineUntilFullSubTree.addChild(fullCargoNode)
mineUntilFullSubTree.addChild(gotoNode)
gotoNode.addChild(coordinateNode)
SequenceNode.addChild(Nodes.subTree_dumpResources("Resource Drop Off"))


