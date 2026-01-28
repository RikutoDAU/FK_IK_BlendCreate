import maya.cmds as cmds

from PySide6 import QtWidgets as qw ,QtCore as qc

'''
import sys
import os

failPath = __file__
folderPath = os.path.dirname(failPath)
sys.path.append(folderPath)

try:
    import FK_IK_MID_RigCreate_Logic as logic
except ImportError:
    cmds.error(logic + "isNotFound")
'''

import FK_IK_MID_RigCreate_Logic as logic
import importlib
importlib.reload(logic)

#GUI用クラス
class guiWindow(qw.QDialog):
    
    windowName = "FK,IK,BlendRigCreate"

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logicClass = logic.FK_IK_BlendRigCreate

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
            self.logicClass(self.inputFkCtlName.text(), self.inputIkCtlName.text(),self.inputSwitchCtlName.text()).doIt()

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
