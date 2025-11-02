#!/usr/bin/env python3
import os
import sys
from tkinter import Tk
from app.ui.ui import App

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def run():
    root = Tk()
    # app = App(root)
    App(root)
    root.mainloop()


if __name__ == "__main__":
    run()
