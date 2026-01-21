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
        self.plusNameList = ["FK","IK","Mid"]   #名前は仮置き中

        self.jointFK = []
        self.jointIK = []
        self.jointMID = []

        self.ikCTL = "ik_Ctl_Base"  #名前は仮置き中
        self.fkCTL = "fk_Ctl_Base"

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
    
    def ikHandleCtlCreate(self):

        ikCtl = self.ikCTL
        startJointIK = self.jointIK[0]
        endJointIK = self.jointIK[-1]

        ikHandle = cmds.ikHandle(startJoint = startJointIK, endEffector = endJointIK , solver="ikRPsolver", name = self.jointIK[0] + "_IKhandle")[0]
        
        if not cmds.objExists(ikCtl):
            cmds.error(ikCtl,"が存在しません")
    
        copyCtl = cmds.duplicate(ikCtl, name=endJointIK + "_CTL")[0]

        snapConst = cmds.pointConstraint(endJointIK, copyCtl, maintainOffset=False)[0]
        cmds.delete(snapConst)
        cmds.parent(ikHandle,copyCtl)

    def fkCtlCreate(self):

        #newfkCntChain = []
        fkCtl = self.fkCTL
        beforeCnt = None

        for i in self.jointFK:

            jointFkCnt = cmds.duplicate(fkCtl, name=i+ "_CTL")[0]

            group = cmds.group(jointFkCnt, name=i + "_GRP")

            snapConst = cmds.parentConstraint(i , group, mo=False)[0]
            cmds.delete(snapConst)

            if beforeCnt:
                cmds.parent(group, beforeCnt)

            cmds.parentConstraint(jointFkCnt, i, mo=True)

            beforeCnt = jointFkCnt

    def doIt(self ,args):        

        self.createChainList()

        for i,plusNames in enumerate(self.plusNameList):

            if i == 0:
                self.jointFK = self.duplicateJoint(plusNames)

            elif i == 1:
                self.jointIK = self.duplicateJoint(plusNames)
            
            elif i == 2:
                self.jointMID = self.duplicateJoint(plusNames)
            
            else:
                break

        self.ikHandleCtlCreate()
        self.fkCtlCreate()



        return self.jointFK, self.jointIK, self.jointMID

FK_IK_BlendRigCreate().doIt(None)



