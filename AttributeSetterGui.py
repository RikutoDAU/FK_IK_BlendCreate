import maya.cmds as cmds

from PySide6 import QtWidgets as qw ,QtCore as qc
#from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QPushButton

import importlib


class attrSetterGui():

    def __init__(self):
        
        #ウィンドウの設定
        self.setWindowFlags(self.windowFlags() | qc.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(self.windowName)
        self.resize(400,400)
        
        self.layout = qw.QVBoxLayout(self)
        self.layout.setSpacing(10)

        #表示する説明文
        explainText = (
            "\n"
            )
        self.explain = qw.QLabel(explainText)

        self.lockList[
            self.lockTrsXCb,self.lockTrsYCb,self.lockTrsZCb,

        ]

        self.lockTrsXCb = qw.QCheckBox("X位置のロック")
        self.lockTrsYCb = qw.QCheckBox("Y位置のロック")
        self.lockTrsZCb = qw.QCheckBox("Z位置のロック")


        self.lockTrsXCb.setChecked(True)
        self.lockTrsYCb.setChecked(True)
        self.lockTrsZCb.setChecked(True)

        self.lockRotXCb = qw.QCheckBox("X回転のロック")
        self.lockRotYCb = qw.QCheckBox("Y回転のロック")
        self.lockRotZCb = qw.QCheckBox("Z回転のロック")

        self.lockRotXCb.setChecked(True)
        self.lockRotYCb.setChecked(True)
        self.lockRotZCb.setChecked(True)

        
