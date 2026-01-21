import maya.api.OpenMaya as om
import maya.cmds as cmds

# API2.0 を有効にする
def maya_useNewAPI():
    pass

#selection = om.MGlobal.getActiveSelectionList()

class FK_IK_BlendRigCreate(om.MPxCommand):

    def __init__(self):
        super().__init__()
        self.chainList = []
        self.plusNameList = ["FK","IK","Mid"]

    def getSelectJoint(self):
        isSelection = cmds.ls(selection=True, type='joint')

        if len(isSelection) == 1:
            startJoint = isSelection[0]
            endJoint = startJoint
        
        elif len(isSelection) == 2:
            startJoint = isSelection[0]
            endJoint = isSelection[1]

        else:
            cmds.error("ジョイントが選択されていないか、3つ以上選択されています")
            return None
        return startJoint,endJoint
            
    def createChainList(self):

        start,end = self.getSelectJoint()
        if start == None or end == None:
            return
        
        current = start
        chain = []
        
        #ジョイントを親から子の順でリストに格納
        while True:

            chain.append(current)

            if current == end:
                break
            
            child = cmds.listRelatives(current, children= True, type = 'joint')

            if child is None or len(child) != 1:
                cmds.error("子ジョイントが分岐しています")
                return

            current = child[0]
            chainList = chain
        
        self.chainList = chain
        print("指定ジョイント" , self.chainList)
        return chain

    def duplicateJoint(self,pulsName):

        newChainList = []

        for i in range(len(self.chainList)):
            copyJnt = cmds.duplicate(self.chainList[i], po=True)[0]

            newName = cmds.rename(copyJnt, self.chainList[i] + "_" + pulsName)

            if len(newChainList) > 0:
                cmds.parent(newName, newChainList[i - 1], relative=True)

            newChainList.append(newName)

        print("新しいジョイントリスト" , newChainList)
        return newChainList

    def doIt(self ,args):        

        self.createChainList()

        for i,plusNames in enumerate(self.plusNameList):

            if i == 0:
                jointFK = self.duplicateJoint(plusNames)

            elif i == 1:
                jointIK = self.duplicateJoint(plusNames)
            
            elif i == 2:
                jointMID = self.duplicateJoint(plusNames)
            
            else:
                break
        
        print()
        return jointFK,jointIK,jointMID

FK_IK_BlendRigCreate().doIt(None)



