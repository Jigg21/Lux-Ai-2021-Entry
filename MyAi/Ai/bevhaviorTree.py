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
    



#instantiate behavior tree
aiTree = behaviorTree()

#for each unit
allUnitsDec =  Nodes.node_AllUnitsDec("All Units Node")
#collect resources
expandCity = Nodes.subTree_expandCity("Expand City Subtree")
aiTree.rootNode.addChild(allUnitsDec)
allUnitsDec.addChild(expandCity)



