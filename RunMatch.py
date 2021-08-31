from MyAi.lux.annotate import text
import tkinter as tk
import os
import subprocess
import threading
from tkinter import Button, Label, filedialog
from tkinter.constants import BOTTOM, LEFT, RIGHT


class MatchRunner(tk.Frame):
    botAPath = ""
    botBPath = ""
    def __init__(self):
        print("Initializing")

        self.window = tk.Tk()
        self.window.title("Run Match")
        self.window.geometry("300x150")
        self.window.config(background = "white")

        
        self.mainFrame = tk.Frame(self.window)
        self.browseA = tk.Frame(self.mainFrame,bg="white")
        self.browseB = tk.Frame(self.mainFrame,bg="white")
        self.label_file_explorerA = Label(self.browseA,text="Bot A",
                                width= 10, height= 5, fg = "blue",bg="white")
        self.label_file_explorerB = Label(self.browseB,text="Bot B",
                                width= 10, height= 5, fg = "blue",bg="white")
        self.button_exploreA = Button(self.browseA,text="Browse",command=lambda:self.browseFiles(True))
        self.button_exploreB = Button(self.browseB,text="Browse",command=lambda:self.browseFiles(False))
        self.button_launch = Button(self.window,text="Launch Match!",command=self.launchMatch)
        self.button_abort = Button(self.window,text="Abort Match!",command=lambda:self.t1.join(timeout=1))
        
        self.mainFrame.pack(expand=True)
        self.browseA.pack(side=LEFT)
        self.browseB.pack(side=RIGHT)
        self.label_file_explorerA.pack()
        self.label_file_explorerB.pack()
        self.button_exploreA.pack()
        self.button_exploreB.pack()
        self.button_launch.pack(side=BOTTOM)
        self.button_abort.pack(side=BOTTOM)
        self.window.mainloop()

    def browseFiles(self,botA):
        if botA:
            filename = filedialog.askopenfilename(initialdir=os.path.abspath(__file__),
                                                title = "Select bot a",
                                                filetypes=(("Python Files","*.py"),("all files","*."))
            )
            self.botAPath = filename
            self.button_exploreA.config(text=filename[filename.find("Lux/")+4:])       
        else:
            filename = filedialog.askopenfilename(initialdir= os.path.abspath(__file__),
                                                title = "Select bot b",
                                                filetypes=(("Python Files","*.py"),("all files","*."))
            )
            self.botBPath = filename
            self.button_exploreB.config(text=filename[filename.find("Lux/")+4:])

    def launchMatch(self):
        try:
            if self.botBPath != "" and self.botAPath != "":
                self.t1 = threading.Thread(target=lambda: subprocess.run('lux-ai-2021 {patha} {pathb} --python=python3 --=replay.json'.format(patha=self.botAPath,pathb=self.botBPath),shell=True))
                self.t1.start()
                return None
        except:
            print("FAILED MATCH ABORTING")
            return None


if __name__ == "__main__":
    MatchRunner()