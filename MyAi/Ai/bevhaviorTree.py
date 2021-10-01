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
aiTree.rootNode.addChild(allUnitsDec)
allUnitsDec.addChild(SequenceNode)

gather = Nodes.subTree_gatherResources("Gather Fuel")
SequenceNode.addChild(gather)
SequenceNode.addChild(Nodes.subTree_dumpResources("Resource Drop Off"))


