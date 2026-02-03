import maya.cmds as cmds
import traceback

#機能クラス
class FK_IK_BlendRigCreate():

    def __init__(self, fkCtlName, ikCtlName, swicthCtlName):

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

        #kコントローラー指定がなかった場合用、作成されたデフォルトコントローラーリスト
        self.defaultCtlList = []

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

            #元のジョイントとの親子階層を解除
            currentParent = cmds.listRelatives(newName, parent=True)
            if currentParent:
                cmds.parent(newName, world=True)

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

        #コントローラーの指定がない場合はデフォルト用を割り当て
        if not ikCtl:
            ikCtl = self.createCurveCtl(formType="Square")
            #ikCtl = self.squareCtlBase
        
        #指定されたコントローラーが存在しなければ中断。
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

        #コントローラーの指定がない場合はデフォルト用を割り当て
        if not fkCtl:
            fkCtl = self.createCurveCtl(formType="Diamond")
            #fkCtl = self.diamondCtlBase

        #指定されたコントローラーが存在しなければ中断。
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

    def createSquareCurve(self):
        points = [(-1, 0, 1), (1, 0, 1), (1, 0, -1), (-1, 0, -1), (-1, 0, 1)]
        self.squareCtlBase = cmds.curve(n="SquareCtlBase", d=1, p=points)

        #角度調整
        cmds.rotate(0,90,0,self.squareCtlBase , relative = True)
        cmds.makeIdentity(self.squareCtlBase, apply = True, rotate= True)

    def createDiamondCurve(self):
        points = [(0, 1, 0), (-1, 0, 0), (0, -1, 0), (1, 0, 0), (0, 1, 0)]
        self.diamondCtlBase = cmds.curve(n="DiamondCtlBase", d=1, p=points)
        
        #角度調整
        cmds.rotate(0,90,0,self.diamondCtlBase , relative = True)
        cmds.makeIdentity(self.diamondCtlBase, apply = True, rotate= True)

    def createCurveCtl(self, formType):
        match formType:
            case "Square":
                self.createSquareCurve()
                self.defaultCtlList.append(self.squareCtlBase)
                return self.squareCtlBase
            
            case "Diamond":
                self.createDiamondCurve()
                self.defaultCtlList.append(self.diamondCtlBase)
                return self.diamondCtlBase
            
            case _:
                print("形状が選ばれていないか、存在していない")
                
            
        

    def doIt(self):        

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

        if self.defaultCtlList:
            cmds.delete(self.defaultCtlList)

        return
