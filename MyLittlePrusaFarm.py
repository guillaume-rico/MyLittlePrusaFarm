#!/usr/bin/python
# python C:\SLF\Perso\MyLittlePrusaFarm\MyLittlePrusaFarm.py
import configparser
import os
import glob 
import PrusaLinkPy

# On récupère le nom du dossier du script
scriptPath = os.path.dirname(os.path.realpath(__file__))

# On vérifie si un dossier _COMMON est présent 
dictGcodeCommon = {}
commonPath = scriptPath + "/groups"  + "/_COMMON"
if os.path.exists(commonPath) :
    print("Folder with common GCODE exists")
    listeTemp = os.scandir(commonPath)
    for folder in listeTemp :
        if folder.is_dir() :
            dictGcodeCommon[folder.name] = {}
            for file in os.scandir(folder) :
                if "gcode" in file.name :
                    dictGcodeCommon[folder.name][file.name] = file.path
        elif "gcode" in folder.name :
            dictGcodeCommon[folder.name] = folder.path
    print(dictGcodeCommon)
    
    
for folderGroup in os.scandir(scriptPath + '/groups') :
    if folderGroup.is_dir() and folderGroup.name != "_COMMON" :
        print("Working on group : " + folderGroup.name)
        # Pour chaque machine :
        # 1) On se connecte 
        # 2) On vérifie que les dossiers sont biens présents
        # 3) On télécharge les fichiers ci-besoin
        # 4) On supprime ceux qui ne sont plus valables
        for printer in os.scandir(folderGroup) :
            if printer.is_file() :
                print(" - Printer : " + printer.name)
                # Lecture des parametres de la becane 
                printerParam = {}
                printerParam["IP"] = ""
                printerParam["PORT"] = "80"
                printerParam["PKA"] = ""
                printerParam["IP_DISTANT"] = ""
                printerParam["PORT_DISTANT"] = ""
                with open(printer.path) as f:
                    content = f.readlines()
                    for line in content:
                        splitted = line.strip().split(' ')
                        if len(splitted) == 3 :
                            printerParam[splitted[0]] = splitted[2]
                if printerParam["IP_DISTANT"] != "" :
                    printerParam["IP"] = printerParam["IP_DISTANT"]
                if printerParam["PORT_DISTANT"] != "" :
                    printerParam["PORT"] = printerParam["PORT_DISTANT"]
                #print(str(printerParam))
                    
                if printerParam["IP"] != "" and printerParam["PKA"] != "" :
                
                    # Tentative de connexion 
                    prusaMini = PrusaLinkPy.PrusaLinkPy(printerParam["IP"], printerParam["PKA"] , port = printerParam["PORT"])
                    
                    connectionOK = True
                    try :
                        prusaMini.get_version()
                    except :
                        connectionOK = False
                        print("<!>  Error - Host doenot respond")
                
                    if connectionOK :
                        # On vient charger tous les COMMON
                        if len(dictGcodeCommon) != 0 :
                            for folder in dictGcodeCommon :
                                if isinstance(dictGcodeCommon[folder], dict) :
                                    print("  - Folder : " + folder)
                                    tempFolder = folder
                                    for file in dictGcodeCommon[folder] :
                                        print("   - File : " + file, end="")
                                        if prusaMini.exists_gcode(tempFolder + "/" + file) : 
                                            print(" -> File Already Exists")
                                        else :
                                            print(" -> Sending file", end="")
                                            ret = prusaMini.put_gcode(dictGcodeCommon[folder][file], tempFolder + "/" + file)
                                            print(" - Status : " + str(ret.status_code) + " text "  + str(ret.text))
                                else :
                                    print("  - File : " + folder, end="")
                                    if prusaMini.exists_gcode(folder) : 
                                        print(" -> File Already Exists")
                                    else :
                                        print(" -> Sending file", end="")
                                        ret = prusaMini.put_gcode(dictGcodeCommon[folder], folder)
                                        print(" - Status : " + str(ret.status_code) + " text "  + str(ret.text))
                                    
                                    
                        # On synchronise ensuite les dossiers présents dans GCODE
                        if os.path.exists(folderGroup.path + "/GCODE") :
                            for folderGcode in os.scandir(folderGroup.path + '/GCODE/') :
                                if folderGcode.is_dir() :
                                    tempFolder = folderGcode.name
                                    for file in os.scandir(folderGcode) :
                                        if "gcode" in file.name :
                                            print("   - File : " + file.name, end="")
                                            if prusaMini.exists_gcode(tempFolder + "/" + file.name) : 
                                                print(" -> File Already Exists")
                                            else :
                                                print(" -> Sending file", end="")
                                                ret = prusaMini.put_gcode(file.path, tempFolder + "/" + file.name)
                                                print(" - Status : " + str(ret.status_code) + " text "  + str(ret.text))
                                elif "gcode" in folderGcode.name :
                                    print("   - File : " + folderGcode.name, end="")
                                    if prusaMini.exists_gcode(folderGcode.name) : 
                                        print(" -> File Already Exists")
                                    else :
                                        print(" -> Sending file", end="")
                                        ret = prusaMini.put_gcode(folderGcode.path, folderGcode.name)
                                        print(" - Status : " + str(ret.status_code) + " text "  + str(ret.text))
                else :
                    print("  -> Warning : IP PKA not found : " + str(printerParam))

