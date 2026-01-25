import maya.api.OpenMaya as om
import maya.cmds as cmds

from PySide6 import QtWidgets, QtCore

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

        self.switchCTL = "switch1"

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

            jointFkCnt = cmds.duplicate(fkCtl, name=i + "_CTL")[0]

            group = cmds.group(jointFkCnt, name=i + "_GRP")

            snapConst = cmds.parentConstraint(i , group, mo=False)[0]
            cmds.delete(snapConst)

            if beforeCnt:
                cmds.parent(group, beforeCnt)

            cmds.parentConstraint(jointFkCnt, i, mo=True)

            beforeCnt = jointFkCnt

    def fkIkblend(self):

        switchCTL = self.switchCTL
        if not cmds.objExists(switchCTL):
            cmds.error(switchCTL,"が存在しません")

        for i, jnt in enumerate(self.jointMID):
            
            bmNode = cmds.createNode('blendMatrix', name=jnt + "_bm")

            cmds.connectAttr(self.jointFK[i] + ".matrix", bmNode + ".inputMatrix")
            cmds.connectAttr(self.jointIK[i] + ".matrix", bmNode + ".target[0].targetMatrix")
            cmds.connectAttr(bmNode + ".outputMatrix", self.jointMID[i] + ".offsetParentMatrix")

            attrName = jnt + "IKratio"

            cmds.addAttr(switchCTL, longName=attrName, attributeType="double", min=0, max=1, keyable=True)

            bmAttr = switchCTL + "." + attrName
            cmds.connectAttr(bmAttr, bmNode + ".target[0].weight")

            #MIDの移動、回転、ジョイント方向の値を0にする。MIDが複製された際の数値が入った状態のままだと、その数値が乗算された行列になってそう。
            cmds.setAttr(jnt+".translate",0,0,0)
            cmds.setAttr(jnt+".rotate",0,0,0)
            cmds.setAttr(jnt+".jointOrient",0,0,0)
        
        

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
        self.fkIkblend()



        return self.jointFK, self.jointIK, self.jointMID
    
class guiWindow(QtWidgets.QDialog):
    
    def __init__(self):
        super().__init__()
        
        self.logicClass = FK_IK_BlendRigCreate


        self.setWindowTitle("FK,IK,BlendRigCreate")
        self.resize(400,400)


        self.windowLayout = QtWidgets.QVBoxLayout(self)
        self.windowLayout.setSpacing(10)

        
        self.title = QtWidgets.QLabel("指定するジョイントを選択")
        self.createButton = QtWidgets.QPushButton("create FK,IK,MID")

        self.windowLayout.addWidget(self.title)
        self.windowLayout.addWidget(self.createButton)

        self.createButton.clicked.connect(self.clickedCreateButton)
        
    def clickedCreateButton(self):

        FK_IK_BlendRigCreate().doIt(None)
       

#FK_IK_BlendRigCreate().doIt(None)

openWindow = guiWindow()
openWindow.show()

