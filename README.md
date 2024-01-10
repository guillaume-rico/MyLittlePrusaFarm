# MyLittlePrusaFarm

Require :

    pip install windows-toasts
    pip install PyPrusaLink
    
# Configuration

Create a folder for each group of printer 
    
# Exemple of use


Start print (-s) on every printer of group (-g) "gauche_fond" for the longger print that finish before (--endhour) 11 AM exluding gcode present in folder (--notinclud) that contains "DUPLO"

    python C:\SLF\Perso\MyLittlePrusaFarm\MyLittlePrusaFarm.py -s -g gauche_fond --endhour 11 --notinclud DUPLO