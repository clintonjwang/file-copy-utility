import easygui
import os

path = easygui.diropenbox(msg='Choose directory to search')
print(os.listdir(path))