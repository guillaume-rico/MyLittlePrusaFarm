#!/usr/bin/python
# python C:\SLF\Perso\MyLittlePrusaFarm\MyLittlePrusaFarm.py

import argparse
import os
import glob 
import sys 
import concurrent.futures
from multiprocessing import Manager
import random, time, datetime

# For debugging lib sys.path.insert(1, 'C:/SLF/Perso/brio/pyPrusaLink/PrusaLinkPy')

import PrusaLinkPy

# On récupère le nom du dossier du script
scriptPath = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('-u', '--update', action='store_true', help="update Gcode on printers")
parser.add_argument('-t', '--test', action='store_true', help="test mode")
parser.add_argument('-c', '--check', action='store_true', help="check status of printers")
parser.add_argument('-n', '--notification', action='store_true', help="display windows notification")
parser.add_argument('-s', '--start', action='store_true', help="start Gcode on printers")

# Args for start 
parser.add_argument('--endhour', type=int, help='Next change hour')
parser.add_argument('--notinclud', type=str, help='String in folder to exlcude')

parser.add_argument('-g', '--groups', nargs='+', default=[], help="groups")
args = parser.parse_args()

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

def loadINI(printerName, fileName) :
    retDict = {}
    retDict["IP"] = ""
    retDict["PORT"] = "80"
    retDict["PKA"] = ""
    retDict["IP_DISTANT"] = ""
    retDict["PORT_DISTANT"] = ""
    retDict["iniFileLoaded"] = False
    
    if fileName.is_file() :
        with open(fileName.path) as f:
            content = f.readlines()
            for line in content:
                splitted = line.strip().split(' ')
                if len(splitted) == 3 :
                    retDict[splitted[0]] = splitted[2]
    if retDict["IP_DISTANT"] != "" :
        retDict["IP"] = retDict["IP_DISTANT"]
    if retDict["PORT_DISTANT"] != "" :
        retDict["PORT"] = retDict["PORT_DISTANT"]
        
    if retDict["IP"] != "" and retDict["PKA"] != "" :
        retDict["iniFileLoaded"] = True
        
    if not retDict["iniFileLoaded"] and ".ini" in fileName.path :
        displaySyncStatus(printerName,  "  -> Warning : IP or PKA not found in ini file : " + str(retDict))
        addError(printerName , "Error -  IP or PKA not found in ini file : " + str(fileName.path) + " " + str(retDict))
        
    return retDict
    
errorDict = {}
def addError (printerL, text) :
    if printerL not in errorDict :
        errorDict[printerL] = []
    errorDict[printerL].append(text)

syncStatusByPrinterDict = {}
isInDisplaySyncStatus = False
def displaySyncStatus (printerB, status, appendToStr = False) :
    # Clear Screen 
    # Update Dict 
    global isInDisplaySyncStatus
    
    while isInDisplaySyncStatus :
        time.sleep(random.uniform(0.01, 0.05))
        
    if printerB not in syncStatusByPrinterDict :
        syncStatusByPrinterDict[printerB] = ""
        
    if appendToStr :
        syncStatusByPrinterDict[printerB] = syncStatusByPrinterDict[printerB] + status 
    else :
        syncStatusByPrinterDict[printerB] = status 

    if not isInDisplaySyncStatus :
        isInDisplaySyncStatus = True
        
        # Display on Screen :
        UP = "\x1B[" + str(len(syncStatusByPrinterDict) + 2) + "A"
        UP2 = "\x1B[2A"
        CLR = "\x1B[0K"
        
        # Clear screen
        for elem in syncStatusByPrinterDict  :
            print(f"{UP2}{CLR}")
        print(f"{UP2}{CLR}")
        print(f"{UP2}{CLR}")
            
        print(f"{UP}Status :{CLR}")
        for printerB in syncStatusByPrinterDict :
            # print(printerB + " : " + syncStatusByPrinterDict[printerB])
            if "Finish" in syncStatusByPrinterDict[printerB] :
                # In green !
                print('\x1b[6;30;42m' + printerB + '\x1b[0m' + f" : " + syncStatusByPrinterDict[printerB] + f"{CLR}")
            else :
                print(printerB + f" : " + syncStatusByPrinterDict[printerB] + f"{CLR}")
            

        isInDisplaySyncStatus = False
    

def synchroPrinter (printerDef, folderGroupLocal) :

    # Lecture des parametres de la becane 
    printerParam = loadINI(printerDef.name, printerDef)
        
    if printerParam["iniFileLoaded"] :
    
        # Tentative de connexion 
        prusaMini = PrusaLinkPy.PrusaLinkPy(printerParam["IP"], printerParam["PKA"] , port = printerParam["PORT"])
        
        connectionOK = True
        try :
            prusaMini.get_version()
        except :
            connectionOK = False
            displaySyncStatus(printerDef.name, "<!>  Error - Host does not respond")
            addError(printerDef.name , "Error - Host does not respond")
    
        listFileToSend = []
        listFolderToSend = []
        
        if connectionOK :
            # On vient télécharger tous les fichiers de COMMON et GCODE
            listDirToSynch = [commonPath, folderGroupLocal.path + "/GCODE"]
            for dirToSynch in listDirToSynch :
                dirToSynch = dirToSynch.replace("\\","/")
                if os.path.exists(dirToSynch) :
                    for (root,dirs,files) in os.walk(dirToSynch,topdown=True):
                        for file in files :
                            if "gcode" in file or "bbf" in file : 
                                completPath = root.replace("\\","/") + "/" + file
                                printerPath = completPath.replace(dirToSynch + "/","")
                                listFolderToSend.append(root.replace("\\","/").replace(dirToSynch + "/",""))
                                
                                displaySyncStatus(printerDef.name, "  * File " + printerPath)
                                
                                listFileToSend.append(printerPath)
                                if prusaMini.exists_gcode(printerPath) : 
                                    displaySyncStatus(printerDef.name, " -> File Already Exists", True)
                                else :
                                    displaySyncStatus(printerDef.name, " -> Sending file ...", True)
                                    
                                    errorDuringSending = False
                                    try :
                                        if not args.test :
                                            ret = prusaMini.put_gcode(completPath, printerPath)
                                    except Exception as e:
                                        displaySyncStatus(printerDef.name, " -> Error durring sending", True)
                                        addError(printerDef.name , "Error - during sending file : " + printerPath + f" error : {e}")
                                        errorDuringSending = True
                                        break
                                    if not errorDuringSending : 
                                        if ret.status_code == 201 :
                                            displaySyncStatus(printerDef.name, " -> " + '\x1b[6;30;42m' + "OK" + '\x1b[0m', True)
                                        elif ret.status_code == 401 :
                                            displaySyncStatus(printerDef.name, " -> Error : Unauthorized - Check IP & Port & PKA", True)
                                            addError(printerDef.name , "Error - Error : Unauthorized - Check IP & Port & PKA - sending file : " + printerPath)
                                        elif ret.status_code == 409 :
                                            displaySyncStatus(printerDef.name," -> Error : File already exists", True)
                                        else :
                                            displaySyncStatus(printerDef.name, " -> Error : " + str(ret.status_code) + " text "  + str(ret.text).replace('\n', ''), True)
                                            addError(printerDef.name , "Error - during sending file : " + printerPath + " Error code : " + str(ret.status_code) + " - Error text "  + str(ret.text).replace('\n', ''))
            # On Supprime les fichiers qui n'ont plus rien a faire
            listFolderToSend = list(set(listFolderToSend))
            #print(listFolderToSend)
            if True :
                # filename filedir
                fileDict = prusaMini.get_recursive_files()
                #print(fileDict)
                # Delete Files
                for fileName, filePrinterPath in flatten(fileDict) :
                    if fileName not in listFileToSend :
                        displaySyncStatus(printerDef.name,"  * Delete File : " + filePrinterPath)
                        ret = prusaMini.delete_gcode(filePrinterPath)
                        if ret.status_code == 204 :
                            displaySyncStatus(printerDef.name," -> Done" , True)
                        else :
                            displaySyncStatus(printerDef.name," -> Error : " + str(ret.status_code) + " text "  + str(ret.text).replace('\n', '') , True)
                            addError(printerDef.name , "Error - during deleting file : " + filePrinterPath + " Error code : " + str(ret.status_code) + " - Error text "  + str(ret.text).replace('\n', ''))
                # Delete Folders
                for folderPrinterPath in flattenFolder(fileDict) :
                    if folderPrinterPath not in listFolderToSend :
                        displaySyncStatus(printerDef.name,"  * Delete Folder : /" + folderPrinterPath)
                        ret = prusaMini.delete_gcode("/" + folderPrinterPath)
                        if ret.status_code == 204 :
                            displaySyncStatus(printerDef.name," -> Done", True)
                        else :
                            displaySyncStatus(printerDef.name," -> Error : " + str(ret.status_code) + " text "  + str(ret.text).replace('\n', ''), True)
                            addError(printerDef.name , "Error - during deleting folder : " + folderPrinterPath + " Error code : " + str(ret.status_code) + " - Error text "  + str(ret.text).replace('\n', ''))
        displaySyncStatus(printerDef.name, "Finish !")

#Nettoyage de la console :
os.system('cls' if os.name=='nt' else 'clear')

# Mise à jour des clés USB :
if args.update :

    # On vérifie si un dossier _COMMON est présent 
    dictGcodeCommon = {}
    commonPath = scriptPath + "/groups"  + "/_COMMON"

    # On gnéère la liste des threads à executer : un thread par machine
    listPrinterToSync = []
    for folderGroup in os.scandir(scriptPath + '/groups') :
        if folderGroup.is_dir() and \
           folderGroup.name != "_COMMON" and \
           folderGroup.name != "example" and \
           (args.groups == [] or folderGroup.name in args.groups) :
            # Pour chaque machine :
            # 1) On se connecte 
            # 2) On vérifie que les dossiers sont biens présents
            # 3) On télécharge les fichiers ci-besoin
            # 4) On supprime ceux qui ne sont plus valables
            for printer in os.scandir(folderGroup) :
                
                # Ajout à la liste des Threads a executer
                listPrinterToSync.append((printer,folderGroup))
    
    # On execute l'ensemble des threads 
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(listPrinterToSync)) as executor:
        futures = []
        for PrinterToSync, folderGroup in listPrinterToSync:
            futures.append(executor.submit(synchroPrinter, printerDef=PrinterToSync, folderGroupLocal=folderGroup))
        # On attend la fin
        for future in concurrent.futures.as_completed(futures) :
            try:
                result = future.result()
            except Exception as e:
                print(f"Error in thread : {e}")


if args.check or args.start :
    printerCheckDict = {}
    for folderGroup in os.scandir(scriptPath + '/groups') :
        if folderGroup.is_dir() and \
           folderGroup.name != "_COMMON" and \
           folderGroup.name != "example" and \
           (args.groups == [] or folderGroup.name in args.groups) :
            print("Working on group : " + folderGroup.name)
            # Pour chaque machine :
            # 1) On se connecte 
            # 2) On vérifie que les dossiers sont biens présents
            # 3) On télécharge les fichiers ci-besoin
            # 4) On supprime ceux qui ne sont plus valables
            for printer in os.scandir(folderGroup) :
            
                printerParam = loadINI(printer.name, printer)
                    
                if printerParam["iniFileLoaded"] :
                    
                    prusaMini = PrusaLinkPy.PrusaLinkPy(printerParam["IP"], printerParam["PKA"] , port = printerParam["PORT"])
                    
                    connectionOK = True
                    try :
                        ret = prusaMini.get_printer()
                    except :
                        connectionOK = False
                        print("<!>  Error - Host does not respond")
                        addError(printer.name , "Error - Host does not respond")
                    
                    if connectionOK :
                        connectionOK = True
                        try :
                            ret2 = prusaMini.get_status()
                        except :
                            connectionOK = False
                            print("<!>  Error - Host does not respond")
                            addError(printer.name , "Error - Host does not respond")    
                            
                        if connectionOK :
                            printerCheckDict[printer.name] = {}
                            printerCheckDict[printer.name]["pointer"] = prusaMini
                            printerCheckDict[printer.name]["get_printer"] = ret.json()
                            printerCheckDict[printer.name]["get_status"] = ret2.json()
                            print("  * Printing ? " + str(printerCheckDict[printer.name]["get_printer"]['state']['flags']['printing']) + " - error ? " + str(printerCheckDict[printer.name]["get_printer"]['state']['flags']['error']))
                            
    if args.notification :
        # Prepare notification
        printerFinishList = []
        printerAlmostFinishList = []
        printerChangeFilamentList = []
        for printer in printerCheckDict :
            if printerCheckDict[printer]["get_status"]["printer"]["state"] == "FINISHED" :
                printerFinishList.append(printer)
            elif printerCheckDict[printer]["get_status"]["job"]["progress"] >= 99 :
                printerAlmostFinishList.append(printer)
            elif printerCheckDict[printer]["get_status"]["printer"]["state"] == "ATTENTION" :
                printerChangeFilamentList.append(printer)
                
        textToDisplay = ""
        if printerFinishList != [] :
            textToDisplay = textToDisplay + "Finish : " + str(len(printerFinishList)) + " printer(s) : " + " ".join(printerFinishList) + " ! \n"
        if printerAlmostFinishList != [] :
            textToDisplay = textToDisplay + "Almost Finish : " + str(len(printerAlmostFinishList)) + " printer(s) : " + " ".join(printerAlmostFinishList) + " ! \n"
        if printerChangeFilamentList != [] :
            textToDisplay = textToDisplay + "Change Filament : " + str(len(printerChangeFilamentList)) + " printer(s) : " + " ".join(printerChangeFilamentList) + " ! \n"
                
        if textToDisplay != "" :
            from windows_toasts import Toast, WindowsToaster
            toaster = WindowsToaster('MyLittlePrusaFarm')
            newToast = Toast()
            newToast.text_fields = [textToDisplay]
            newToast.on_activated = lambda _: print('Toast clicked!')
            toaster.show_toast(newToast)
            
    if args.start :
        endHour = args.endhour
        foldertoskip = args.notinclud
        # Combien de temps avant 22h 
        actual = datetime.datetime.now()
        
        if actual.hour < endHour :
            nbMinAvalable = (endHour - 1 - actual.hour) * 60 + 60 - actual.minute
        else :
            nbMinAvalable = (24      - 1 - actual.hour) * 60 + 60 - actual.minute
            nbMinAvalable = nbMinAvalable + endHour * 60
        print("Temps avant prochaine execution : " + str(round(nbMinAvalable / 60,0)) + "h " + str(round(nbMinAvalable % 60,0)) + "m")
        
        #On cherche les machines de libre        
        for printer in printerCheckDict :
            if printerCheckDict[printer]["get_status"]["printer"]["state"] == "IDLE" :
                dictFileToRun = {}
                # On cherche le plus grand programme a lancer
                gcodeDict = printerCheckDict[printer]["pointer"].get_recursive_files()
                for dkey in gcodeDict :
                    if (foldertoskip is not None and foldertoskip not in dkey) or foldertoskip is None : 
                        for fname in gcodeDict[dkey] :
                            valid = True
                            try : 
                                duree = datetime.datetime.strptime(fname.split(".")[0], "%Hh%Mm")
                            except :
                                valid = False
                                
                            if valid :
                                if duree.hour * 60 + duree.minute <= nbMinAvalable : 
                                    dictFileToRun[duree.hour * 60 + duree.minute] = gcodeDict[dkey][fname]
                                
                # Maintenant on cherche le pus long disponible et on le lance
                if dictFileToRun != {} :
                    myKeys = list(dictFileToRun.keys())
                    myKeys.sort()
                    print("Print file : " + dictFileToRun[myKeys[-1]] + " Duree (min) " + str(myKeys[-1]) )
                    printerCheckDict[printer]["pointer"].post_gcode(dictFileToRun[myKeys[-1]]) 
            else :
                print(printer + " : Cannot start file :  " + printerCheckDict[printer]["get_status"]["printer"]["state"])
                        
if errorDict != {} :
    # Color : https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
    print("\n\n" + '\x1b[6;30;41m' + "List of errors : " + '\x1b[0m')
    for printerName in errorDict :
        print(" * Printer : " + printerName)
        for errorText in errorDict[printerName] :
            print("  - " + errorText)
        