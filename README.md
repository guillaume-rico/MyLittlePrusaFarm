# MyLittlePrusaFarm

Require :

    pip install windows-toasts
    pip install PyPrusaLink
    
    
# Exemple of use


Start print (-s) on every printer of group "gauche_fond" for the longger print that finish before 11 AM exluding gcode present in folder that contains "DUPLO"

    python C:\SLF\Perso\MyLittlePrusaFarm\MyLittlePrusaFarm.py -s -g gauche_fond --endhour 11 --notinclud DUPLO