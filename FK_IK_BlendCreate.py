import maya.api.OpenMaya as om
import maya.cmds as cmds

from PySide6 import QtWidgets as qw ,QtCore as qc

# API2.0 を有効にする
def maya_useNewAPI():
    pass

#機能クラス
class FK_IK_BlendRigCreate(om.MPxCommand):

    def __init__(self, fkCtlName, ikCtlName, swicthCtlName):
        super().__init__()

        #元のジョイントに追加される名前
        self.plusNameList = ["FK","IK","Mid"]

        #格納用リスト
        self.chainList = []

        self.jointFK = []
        self.jointIK = []
        self.jointMID = []

        #指定されたコントローラーを割り当て
        self.fkCTL = fkCtlName
        self.ikCTL = ikCtlName

        self.switchCTL = swicthCtlName

    #選択中の2つのジョイントの親→子を返す。選択が1つならそのジョイントのみ。
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
    
    #選択された2つのジョイント間を親子階層順にリスト化して返す。
    def createChainList(self):

        start,end = self.getSelectJoint()
        if start == None or end == None:
            return
        
        current = start
        chain = []
        
        #ジョイントを親から子の順でリストに格納。
        while True:

            chain.append(current)

            if current == end:
                break
            
            #一階層下のジョイントを取得。
            child = cmds.listRelatives(current, children= True, type = 'joint')

            #ジョイントが複数に分岐した場合は中断。
            if child is None or len(child) != 1:
                cmds.error("子ジョイントが分岐しています")
                return

            current = child[0]
        
        self.chainList = chain
        print("指定ジョイント" , self.chainList)
        return

    #FK,IK,MID用にジョイントを複製する。引数で指定された1種のタイプのみ複製。
    def duplicateJoint(self,pulsName):

        newChainList = []

        #指定されたジョイントのリスト内の親→子の順に複製。
        for i in range(len(self.chainList)):
            copyJnt = cmds.duplicate(self.chainList[i], po=True)[0]

            #名前はFK,IK,MIDを見分けれるように変更。
            newName = cmds.rename(copyJnt, self.chainList[i] + "_" + pulsName)

            #親階層化する。
            if len(newChainList) > 0:
                cmds.parent(newName, newChainList[i - 1], relative=True)

            newChainList.append(newName)

        print("新しいジョイントリスト" , newChainList)
        return newChainList
    
    #IkHandleとそのコントローラーの作成。
    def ikHandleCtlCreate(self):

        ikCtl = self.ikCTL
        startJointIK = self.jointIK[0]
        endJointIK = self.jointIK[-1]

        #IkHandle作成。
        ikHandle = cmds.ikHandle(startJoint = startJointIK, endEffector = endJointIK , solver="ikRPsolver", name = self.jointIK[0] + "_IKhandle")[0]
        
        #指定されたコントローラーが存在しなけれな中断。
        if not cmds.objExists(ikCtl):
            cmds.error(ikCtl,"が存在しません")
    
        #指定されたコントローラーを複製して、group化に入れることでコントローラーの位置や回転の初期値を0にする。
        copyCtl = cmds.duplicate(ikCtl, name=endJointIK + "_CTL")[0]
        group = cmds.group(copyCtl, name=copyCtl + "_GRP")

        #コントローラーGroupの位置を合わせる。
        snapConst = cmds.pointConstraint(endJointIK, group, maintainOffset=False)[0]
        cmds.delete(snapConst)
        cmds.parent(ikHandle,copyCtl)

    #FKジョイントのコントローラーの作成。
    def fkCtlCreate(self):

        fkCtl = self.fkCTL

        #指定されたコントローラーが存在しなけれな中断。
        if not cmds.objExists(fkCtl):
            cmds.error(fkCtl,"が存在しません")

        #コントローラーの1つ前のループで作成されたコントローラーを変数に保存。
        beforeCnt = None        

        for i in self.jointFK:
            
            #指定されたコントローラーを複製して、group化に入れることでコントローラーの位置や回転の初期値を0にする。
            jointFkCnt = cmds.duplicate(fkCtl, name=i + "_CTL")[0]
            group = cmds.group(jointFkCnt, name=i + "_GRP")

            #コントローラーGroupの位置を合わせる。
            snapConst = cmds.parentConstraint(i , group, mo=False)[0]
            cmds.delete(snapConst)

            #現ループの親となる1つ前のループで作成されたコントローラーの子にする。
            if beforeCnt:
                cmds.parent(group, beforeCnt)

            # コントローラーの動きをジョイントへ与える。
            cmds.parentConstraint(jointFkCnt, i, mo=True)

            beforeCnt = jointFkCnt

    #複製されたFK,IKのジョイントの行列をブレンドさせてMIDに与える。
    def fkIkblend(self):
        
        #FKとIKのブレンド率を調整するコントローラー(switch)。
        switchCTL = self.switchCTL

        #指定されたコントローラーが存在しなけれな中断。
        if not cmds.objExists(switchCTL):
            cmds.error(switchCTL,"が存在しません")

        
        for i, jnt in enumerate(self.jointMID):
            
            #blendMatrixノードを用いてFK,IKの行列をMIDに与える。
            bmNode = cmds.createNode('blendMatrix', name=jnt + "_bm")

            #FK,IKの行列をブレンドさせてMIDに与える。
            cmds.connectAttr(self.jointFK[i] + ".matrix", bmNode + ".inputMatrix")
            cmds.connectAttr(self.jointIK[i] + ".matrix", bmNode + ".target[0].targetMatrix")
            cmds.connectAttr(bmNode + ".outputMatrix", self.jointMID[i] + ".offsetParentMatrix")

            #switchコントローラーに追加される属性の名前。
            attrName = jnt + "IKratio"

            #既にそのジョイントに対するブレンド率の属性が作られていたら削除する。同じジョイントで以前実行したことなどがある場合。
            if cmds.objExists(switchCTL + "." + attrName):
                cmds.deleteAttr(switchCTL + "." + attrName)

            #switchコントローラーにブレンド率の属性を追加。
            cmds.addAttr(switchCTL, longName=attrName, attributeType="double", min=0, max=1, keyable=True)

            #switchコントローラーで入力したブレンド率を反映させる。
            bmAttr = switchCTL + "." + attrName
            cmds.connectAttr(bmAttr, bmNode + ".target[0].weight")

            #MIDの移動、回転、ジョイント方向の値を0にする。MIDが複製された際の数値が入った状態のままだと、その数値が乗算された行列になってそう。
            cmds.setAttr(jnt+".translate",0,0,0)
            cmds.setAttr(jnt+".rotate",0,0,0)
            cmds.setAttr(jnt+".jointOrient",0,0,0)
        
        

    def doIt(self ,args):        

        #指定したジョイントの親子階層順のリストを作成。
        self.createChainList()

        #FK,IK,MIDごとにジョイントを複製。
        for i,plusNames in enumerate(self.plusNameList):

            if i == 0:
                self.jointFK = self.duplicateJoint(plusNames)

            elif i == 1:
                self.jointIK = self.duplicateJoint(plusNames)
            
            elif i == 2:
                self.jointMID = self.duplicateJoint(plusNames)
            
            else:
                break
        
        #コントローラーの作成。
        self.ikHandleCtlCreate()
        self.fkCtlCreate()

        #FKとIKをブレンドしてMIDに反映。
        self.fkIkblend()

        return

#GUI用クラス
class guiWindow(qw.QDialog):
    
    windowName = "FK,IK,BlendRigCreate"

    def __init__(self, parent=None):
        super().__init__(parent)
        
        

        self.logicClass = FK_IK_BlendRigCreate

        #ウィンドウの設定
        self.setWindowFlags(self.windowFlags() | qc.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(self.windowName)
        self.resize(400,400)
        
        self.layout = qw.QVBoxLayout(self)
        self.layout.setSpacing(10)

        #表示する説明文
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

        #ボタンを押した際の関数実行。()
        self.referenceFkButton.clicked.connect(lambda: self.importByExplorer(0))
        self.referenceIkButton.clicked.connect(lambda: self.importByExplorer(1))
        self.referenceSwitchButton.clicked.connect(lambda: self.importByExplorer(2))

        self.createButton.clicked.connect(self.clickedCreateButton)

    #エクスプローラーからコントローラーのインポート処理。現状はadobeのIllustrator.Aiファイル。
    def importByExplorer(self, num):
        
        #FKをインポートする用
        if num == 0:
            failFk = qw.QFileDialog.getOpenFileName(self, "FK:aiファイルを選択", "", "aiファイル(*.ai)")

            #コントローラーの名前指定テキストボックスは"参照済み"に。
            self.inputFkCtlName.setPlaceholderText("参照済み")
            pathNodeFk = cmds.file(failFk[0], i=True, type="Adobe(R) Illustrator(R)", returnNewNodes=True)
            
            #インポートした複製させるベースとなるコントローラーに名付け
            baseNameFk = cmds.rename(pathNodeFk[0],"Fk_Ctl_Base")
            self.inputFkCtlName.setText(baseNameFk)

        #IKをインポートする用
        elif num == 1:
            failIk = qw.QFileDialog.getOpenFileName(self, "IK:aiファイルを選択", "", "aiファイル(*.ai)")
            
            #コントローラーの名前指定テキストボックスは"参照済み"に。
            self.inputIkCtlName.setPlaceholderText("参照済み")
            pathNodeIk = cmds.file(failIk[0], i=True, type="Adobe(R) Illustrator(R)", returnNewNodes=True)

            #インポートした複製させるベースとなるコントローラーに名付け
            baseNameIk = cmds.rename(pathNodeIk[0],"Ik_Ctl_Base")
            self.inputIkCtlName.setText(baseNameIk)

        #switchコントローラーのインポート用        
        else:
            failSwitch = qw.QFileDialog.getOpenFileName(self, "Switch:aiファイルを選択", "", "aiファイル(*.ai)")

            #コントローラーの名前指定テキストボックスは"参照済み"に。
            self.inputSwitchCtlName.setPlaceholderText("参照済み")
            pathNodeSwitch = cmds.file(failSwitch[0], i=True, type="Adobe(R) Illustrator(R)", returnNewNodes=True)

            #インポートした複製させるベースとなるコントローラーに名付け
            nameSwitch = cmds.rename(pathNodeSwitch[0],"blendSwitch_Ctl")
            self.inputSwitchCtlName.setText(nameSwitch)
        
    #実行ボタンの処理。   
    def clickedCreateButton(self):
        
        cmds.undoInfo(openChunk=True)

        #入力またはインポートされたコントローラーを与えて実行
        try:
            self.logicClass(self.inputFkCtlName.text(), self.inputIkCtlName.text(),self.inputSwitchCtlName.text()).doIt(None)

        #エラー時は実行前の状態で中断。
        except Exception:
            cmds.undoInfo(closeChunk=True)
            cmds.undo()
            print("エラーが発生", Exception)

        finally:
            self.close()
            cmds.undoInfo(closeChunk=True)

            
openWindow = guiWindow()

openWindow.setObjectName(openWindow.windowName)
openWindow.show()

