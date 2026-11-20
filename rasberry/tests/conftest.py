import os
import sys

# Les scripts du dossier rasberry/ s'importent entre eux par leur nom (ex. "from camera import ...")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
