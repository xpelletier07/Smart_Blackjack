1. Installer python 3.10, vérifier qu'il fonctionne avec py -3.10 --version ou python3.10 --version (Pour MacOs de marde)
2. Placer le terminal dans /media_pipe
3. Créer le venv : py -3.10 -m venv venv_mediapipe ou python3.10 -m venv venv_mediapipe
4. L'activer : .\venv_mediapipe_310\Scripts\Activate.ps1 ou source /venv_mediapipe/bin/activate 
5. Installer le nécessaire : py -3.10 -m pip install --upgrade pip ou python3.10 -m pip install --upgrade pip
6. pip install -r requirements.txt
7. Ne pas oublier d'installer pyserial : pip install pyserial
8. Exécuter : python detection_action.py