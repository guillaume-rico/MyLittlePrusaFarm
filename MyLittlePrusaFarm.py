#!/usr/bin/python
# python C:\SLF\Perso\MyLittlePrusaFarm\MyLittlePrusaFarm.py

import argparse
import os
import glob 
import sys 

sys.path.insert(1, 'C:/SLF/Perso/brio/pyPrusaLink/PrusaLinkPy')

import PrusaLinkPy

# On récupère le nom du dossier du script
scriptPath = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--clean', action='store_true')
parser.add_argument('-t', '--test', action='store_true')
parser.add_argument('-g', '--groups', nargs='+', default=[])
args = parser.parse_args()
clean = args.clean
test = args.test
groupListToDo = args.groups

def flatten(dictionary, folder ="") :
    items = []
    for key, value in dictionary.items():
        if isinstance(value, dict):
            for elem in flatten(value,folder + key + "/") :
                items.append(elem)
        else:
            items.append((folder + key,value))
    return items

def flattenFolder(dictionary, folder ="") :
    items = []
    for key, value in dictionary.items():
        if isinstance(value, dict):
            items.append(folder + key)
            for elem in flattenFolder(value,folder + key + "/") :
                items.append(elem)
    return items

# On vérifie si un dossier _COMMON est présent 
dictGcodeCommon = {}
commonPath = scriptPath + "/groups"  + "/_COMMON"

for folderGroup in os.scandir(scriptPath + '/groups') :
    if folderGroup.is_dir() and \
       folderGroup.name != "_COMMON" and \
       folderGroup.name != "example" and \
       (groupListToDo == [] or folderGroup.name in groupListToDo) :
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
                        print("<!>  Error - Host does not respond")
                
                    listFileToSend = []
                    listFolderToSend = []
                    
                    if connectionOK :
                        # On vient télécharger tous les fichiers de COMMON et GCODE
                        listDirToSynch = [commonPath, folderGroup.path + "/GCODE"]
                        for dirToSynch in listDirToSynch :
                            dirToSynch = dirToSynch.replace("\\","/")
                            if os.path.exists(dirToSynch) :
                                for (root,dirs,files) in os.walk(dirToSynch,topdown=True):
                                    for file in files :
                                        if "gcode" in file : 
                                            completPath = root.replace("\\","/") + "/" + file
                                            printerPath = completPath.replace(dirToSynch + "/","")
                                            listFolderToSend.append(root.replace("\\","/").replace(dirToSynch + "/",""))
                                            #print("Copy from : " + completPath + " to " + printerPath, end="")
                                            print("  * File " + printerPath, end="")
                                            listFileToSend.append(printerPath)
                                            if prusaMini.exists_gcode(printerPath) : 
                                                print(" -> File Already Exists")
                                            else :
                                                print(" -> Sending file", end="")
                                                errorDuringSending = False
                                                try :
                                                    if not test :
                                                        ret = prusaMini.put_gcode(completPath, printerPath)
                                                except :
                                                    print(" -> Error durring sending")
                                                    errorDuringSending = True
                                                    break
                                                if not errorDuringSending : 
                                                    if ret.status_code == 201 :
                                                        print(" -> Done")
                                                    elif ret.status_code == 401 :
                                                        print(" -> Error : Unauthorized - Check IP & Port & PKA") 
                                                    elif ret.status_code == 409 :
                                                        print(" -> Error : File already exists") 
                                                    else :
                                                        print(" -> Error : " + str(ret.status_code) + " text "  + str(ret.text))
                        # On Supprime les fichiers qui n'ont plus rien a faire
                        listFolderToSend = list(set(listFolderToSend))
                        #print(listFolderToSend)
                        if clean :
                            # filename filedir
                            fileDict = prusaMini.get_recursive_v1_files()
                            #print(fileDict)
                            # Delete Files
                            for fileName, filePrinterPath in flatten(fileDict) :
                                if fileName not in listFileToSend :
                                    print("  * Delete File : " + filePrinterPath, end="")
                                    ret = prusaMini.delete_gcode(filePrinterPath)
                                    if ret.status_code == 204 :
                                        print(" -> Done")
                                    else :
                                        print(" -> Error : " + str(ret.status_code) + " text "  + str(ret.text))
                            # Delete Folders
                            for folderPrinterPath in flattenFolder(fileDict) :
                                if folderPrinterPath not in listFolderToSend :
                                    print("  * Delete Folder : /" + folderPrinterPath, end="")
                                    ret = prusaMini.delete_gcode("/" + folderPrinterPath)
                                    if ret.status_code == 204 :
                                        print(" -> Done")
                                    else :
                                        print(" -> Error : " + str(ret.status_code) + " text "  + str(ret.text))
                                
                else :
                    print("  -> Warning : IP PKA not found : " + str(printerParam))

