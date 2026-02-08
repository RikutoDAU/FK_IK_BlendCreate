# FK_IK_BlendCreate

*指定したジョイントのFKとIK、とそれをブレンドするジョイントの計3つのジョイント+それらのコントローラーを生成するツール。<br>
*maya2025以降のversionに対応。(pySide6を使用している関係)<br>

*実装方法<br>
FK_IK_BlendCreate2_logic.pyファイルをMayaが標準で参照するスクリプトのディレクトリの元に置く。<br>
基本例)'C:\Users\%USERNAME%\Documents\maya\2025\ja_JP\scripts'<br>

*使用方法<br>
mayaでFK,IK,Blendジョイント分を生成したいジョイント間を親→子の順に選択。(CTRL + LeftClick)<br>
FK_IK_BlendCreate2_GUI.pyのスクリプトをMAYAのスクリプトエディタにコピペやシェルフに登録して呼び出す。<br>
<img width="456" height="445" alt="image" src="https://github.com/user-attachments/assets/a5c5b5ee-f298-4dab-8fe3-b51135af75e2" /><br>

画像のようなウィンドウが出るため、その説明通りに使用。<br>
