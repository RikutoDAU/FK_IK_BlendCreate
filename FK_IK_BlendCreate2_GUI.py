import maya.cmds as cmds

from PySide6 import QtWidgets as qw ,QtCore as qc
import importlib

import sys
import os
'''
failPath = __file__
folderPath = os.path.dirname(failPath)
sys.path.append(folderPath)

try:
    import FK_IK_MID_RigCreate_Logic as logic
    importlib.reload(logic)
except ImportError:
    cmds.error("FK_IK_MID_RigCreate_Logic が見つかりません。")
'''

import FK_IK_MID_RigCreate_Logic as logic
import importlib
importlib.reload(logic)

#GUI用クラス
class guiWindow(qw.QDialog):
    
    windowName = "FK,IK,BlendRigCreate"

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logicClass = logic.FK_IK_BlendRigCreate()

        #ウィンドウの設定
        self.setWindowFlags(self.windowFlags() | qc.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(self.windowName)
        self.resize(400,400)
        
        self.layout = qw.QVBoxLayout(self)
        self.layout.setSpacing(10)

        #表示する説明文
        explainText = (
            "指定するジョイント間を親→子の順で2つ選択(CTRL + L_Click)\n"
            "illustratorから追加するコントローラーのサイズはインポート後にcreateする前に調整してください。\n"
            "コントローラーの指定がない場合は自動でDefault用で生成されます"
            )
        self.explain = qw.QLabel(explainText)

        self.inputFkCtlDict = {}

        self.selectChainList = self.logicClass.createChainList()

        if self.selectChainList == 0:
            cmds.error("ジョイントが選択されていません。")

        for i , jnt in enumerate(self.selectChainList):

            line = qw.QHBoxLayout()
            
            label = qw.QLabel(jnt)

            #inputLine = qw.QLineEdit()

            #使用FKコントローラーの指定(名前)
            inputFkCtlName = qw.QLineEdit()
            inputFkCtlName.setPlaceholderText("指定するFKコントローラーの名前を入力 又はドラッグ")

            #self.layout.addWidget(self.inputFkCtlName)
            self.layout.addLayout(line)

            line.addWidget(label)
            line.addWidget(inputFkCtlName)

            
            referenceFkButton = qw.QPushButton(jnt + ":のFK用コントローラーをaiファイルからインポートして参照")            
            referenceFkButton.clicked.connect(lambda checked = False, input = inputFkCtlName: self.importByExplorer(0, input))
            self.layout.addWidget(referenceFkButton)
            
            self.inputFkCtlDict[jnt]  = inputFkCtlName

        #使用IKコントローラーの指定(名前)
        self.inputIkCtlName = qw.QLineEdit()
        self.inputIkCtlName.setPlaceholderText("指定するIKコントローラーの名前を入力 又はドラッグ")
        self.layout.addWidget(self.inputIkCtlName)


        #FKとIKのブレンド率調整用のコントローラーの指定
        self.inputSwitchCtlName = qw.QLineEdit()
        self.inputSwitchCtlName.setPlaceholderText("指定するブレンド率のコントローラーの名前を入力 又はドラッグ")
        self.layout.addWidget(self.inputSwitchCtlName)

        #コントローラーをエクスプローラーから参照ボタン
        #self.referenceFkButton = qw.QPushButton("FK用コントローラーをaiファイルからインポートして参照")
        self.referenceIkButton = qw.QPushButton("IK用コントローラーをaiファイルからインポートして参照")
        self.referenceSwitchButton = qw.QPushButton("ブレンド率の調整用コントローラーをaiファイルからインポートして参照")

        #実行ボタン
        self.createButton = qw.QPushButton("create FK,IK,MID")

        #ウィンドウに表示
        self.layout.addWidget(self.explain)
        #self.layout.addWidget(self.referenceFkButton)
        self.layout.addWidget(self.referenceIkButton)
        self.layout.addWidget(self.referenceSwitchButton)
        self.layout.addWidget(self.createButton)

        #ボタンを押した際の関数実行。()
        #self.referenceFkButton.clicked.connect(lambda: self.importByExplorer(0))
        self.referenceIkButton.clicked.connect(lambda: self.importByExplorer(1, self.inputIkCtlName))
        self.referenceSwitchButton.clicked.connect(lambda: self.importByExplorer(2, self.inputSwitchCtlName))

        self.createButton.clicked.connect(self.clickedCreateButton)

    #エクスプローラーからコントローラーのインポート処理。現状はadobeのIllustrator.Aiファイル。
    def importByExplorer(self, num, ctlName):
        
        #FKをインポートする用
        if num == 0:
            failFk = qw.QFileDialog.getOpenFileName(self, "FK:aiファイルを選択", "", "aiファイル(*.ai)")

            #コントローラーの名前指定テキストボックスは"参照済み"に。
            ctlName.setPlaceholderText("参照済み")
            pathNodeFk = cmds.file(failFk[0], i=True, type="Adobe(R) Illustrator(R)", returnNewNodes=True)
            
            #インポートした複製させるベースとなるコントローラーに名付け
            baseNameFk = cmds.rename(pathNodeFk[0],"Fk_Ctl_Base")
            #self.inputFkCtlName.setText(baseNameFk)

            ctlName.setText(baseNameFk)

        #IKをインポートする用
        elif num == 1:
            failIk = qw.QFileDialog.getOpenFileName(self, "IK:aiファイルを選択", "", "aiファイル(*.ai)")
            
            #コントローラーの名前指定テキストボックスは"参照済み"に。
            ctlName.setPlaceholderText("参照済み")
            pathNodeIk = cmds.file(failIk[0], i=True, type="Adobe(R) Illustrator(R)", returnNewNodes=True)

            #インポートした複製させるベースとなるコントローラーに名付け
            baseNameIk = cmds.rename(pathNodeIk[0],"Ik_Ctl_Base")
            ctlName.setText(baseNameIk)

        #switchコントローラーのインポート用        
        else:
            failSwitch = qw.QFileDialog.getOpenFileName(self, "Switch:aiファイルを選択", "", "aiファイル(*.ai)")

            #コントローラーの名前指定テキストボックスは"参照済み"に。
            ctlName.setPlaceholderText("参照済み")
            pathNodeSwitch = cmds.file(failSwitch[0], i=True, type="Adobe(R) Illustrator(R)", returnNewNodes=True)

            #インポートした複製させるベースとなるコントローラーに名付け
            nameSwitch = cmds.rename(pathNodeSwitch[0],"blendSwitch_Ctl")
            ctlName.setText(nameSwitch)
        
    #実行ボタンの処理。   
    def clickedCreateButton(self):
        
        cmds.undoInfo(openChunk=True)

        fkCtl = []
        for i in self.inputFkCtlDict.values():
            text = i.text()
            fkCtl.append(text)
        
        ikCtl = self.inputIkCtlName.text()
        switchCtl = self.inputSwitchCtlName.text()

        chainList = self.selectChainList

        #入力またはインポートされたコントローラーを与えて実行
        try:
            self.logicClass.doByGui(fkCtl, ikCtl,switchCtl, chainList)

        #エラー時は実行前の状態で中断。
        except Exception as e:
            cmds.undoInfo(closeChunk=True)
            cmds.undo()
            print("エラーが発生", {e})

        finally:
            self.close()
            cmds.undoInfo(closeChunk=True)

            
openWindow = guiWindow()

openWindow.setObjectName(openWindow.windowName)
openWindow.show()
