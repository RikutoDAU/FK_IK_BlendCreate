import maya.api.OpenMaya as om
import maya.cmds as cmds

from PySide6 import QtWidgets as qw ,QtCore as qc

# API2.0 を有効にする
def maya_useNewAPI():
    pass

class FK_IK_BlendRigCreate(om.MPxCommand):

    def __init__(self, fkCtlName, ikCtlName, swicthCtlName):
        super().__init__()

        self.chainList = []
        self.plusNameList = ["FK","IK","Mid"]

        self.jointFK = []
        self.jointIK = []
        self.jointMID = []

        self.fkCTL = fkCtlName
        self.ikCTL = ikCtlName

        self.switchCTL = swicthCtlName

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

        group = cmds.group(copyCtl, name=copyCtl + "_GRP")


        snapConst = cmds.pointConstraint(endJointIK, group, maintainOffset=False)[0]
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

            if cmds.objExists(switchCTL + "." + attrName):
                cmds.deleteAttr(switchCTL + "." + attrName)

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

        return #self.jointFK, self.jointIK, self.jointMID
    
class guiWindow(qw.QDialog):
    
    windowName = "FK,IK,BlendRigCreate"

    def __init__(self, parent=None):
        super().__init__(parent)
        
        

        self.logicClass = FK_IK_BlendRigCreate

        self.setWindowFlags(self.windowFlags() | qc.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(self.windowName)
        self.resize(400,400)


        self.layout = qw.QVBoxLayout(self)
        self.layout.setSpacing(10)

        explainText = (
            "指定するジョイント間を親→子の順で2つ選択(CTRL + L_Click)\n"
            "illustratorから追加するコントローラーのサイズはインポート後にcreateする前に調整してください。"
            )
        self.explain = qw.QLabel(explainText)

        #使用FKコントローラーの指定(名前)
        self.inputFkCtlName = qw.QLineEdit()
        self.inputFkCtlName.setPlaceholderText("指定するFKコントローラーの名前を入力 又はドラッグ")
        self.layout.addWidget(self.inputFkCtlName)

        #使用IKコントローラーの指定(名前)
        self.inputIkCtlName = qw.QLineEdit()
        self.inputIkCtlName.setPlaceholderText("指定するIKコントローラーの名前を入力 又はドラッグ")
        self.layout.addWidget(self.inputIkCtlName)

        #FKとIKのブレンド率調整用のコントローラーの指定
        self.inputSwitchCtlName = qw.QLineEdit()
        self.inputSwitchCtlName.setPlaceholderText("指定するブレンド率のコントローラーの名前を入力 又はドラッグ")
        self.layout.addWidget(self.inputSwitchCtlName)

        #コントローラーをエクスプローラーから参照ボタン
        self.referenceFkButton = qw.QPushButton("FK用コントローラーをaiファイルからインポートして参照")
        self.referenceIkButton = qw.QPushButton("IK用コントローラーをaiファイルからインポートして参照")
        self.referenceSwitchButton = qw.QPushButton("ブレンド率の調整用コントローラーをaiファイルからインポートして参照")

        #実行ボタン
        self.createButton = qw.QPushButton("create FK,IK,MID")

        #ウィンドウに表示
        self.layout.addWidget(self.explain)
        self.layout.addWidget(self.referenceFkButton)
        self.layout.addWidget(self.referenceIkButton)
        self.layout.addWidget(self.referenceSwitchButton)
        self.layout.addWidget(self.createButton)

        self.referenceFkButton.clicked.connect(lambda: self.importByExplorer(0))
        self.referenceIkButton.clicked.connect(lambda: self.importByExplorer(1))
        self.referenceSwitchButton.clicked.connect(lambda: self.importByExplorer(2))

        self.createButton.clicked.connect(self.clickedCreateButton)

        
    def importByExplorer(self, num):
        
        if num == 0:
            failFk = qw.QFileDialog.getOpenFileName(self, "FK:aiファイルを選択", "", "aiファイル(*.ai)")
            self.inputFkCtlName.setPlaceholderText("参照済み")
            pathNodeFk = cmds.file(failFk[0], i=True, type="Adobe(R) Illustrator(R)", returnNewNodes=True)
            
            baseNameFk = cmds.rename(pathNodeFk[0],"Fk_Ctl_Base")
            self.inputFkCtlName.setText(baseNameFk)

        elif num == 1:
            failIk = qw.QFileDialog.getOpenFileName(self, "IK:aiファイルを選択", "", "aiファイル(*.ai)")
            self.inputIkCtlName.setPlaceholderText("参照済み")
            pathNodeIk = cmds.file(failIk[0], i=True, type="Adobe(R) Illustrator(R)", returnNewNodes=True)

            baseNameIk = cmds.rename(pathNodeIk[0],"Ik_Ctl_Base")
            self.inputIkCtlName.setText(baseNameIk)
        
        else:
            failSwitch = qw.QFileDialog.getOpenFileName(self, "Switch:aiファイルを選択", "", "aiファイル(*.ai)")
            self.inputSwitchCtlName.setPlaceholderText("参照済み")
            pathNodeSwitch = cmds.file(failSwitch[0], i=True, type="Adobe(R) Illustrator(R)", returnNewNodes=True)

            nameSwitch = cmds.rename(pathNodeSwitch[0],"blendSwitch_Ctl")
            self.inputSwitchCtlName.setText(nameSwitch)
        
        
    def clickedCreateButton(self):
        
        cmds.undoInfo(openChunk=True)

        try:
            self.logicClass(self.inputFkCtlName.text(), self.inputIkCtlName.text(),self.inputSwitchCtlName.text()).doIt(None)

        
        except Exception:
            cmds.undoInfo(closeChunk=True)
            cmds.undo()
            print("エラーが発生", Exception)

        finally:
            self.close()
            cmds.undoInfo(closeChunk=True)
            

        
       

#FK_IK_BlendRigCreate().doIt(None)

openWindow = guiWindow()

openWindow.setObjectName(openWindow.windowName)
openWindow.show()

