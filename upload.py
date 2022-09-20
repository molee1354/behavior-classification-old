from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import os

from pathExtract import TASK_ID, TRIAL_ID
import sys

try:
    TASK_ID = sys.argv[1]
except IndexError:
    pass
try:
    TRIAL_ID = sys.argv[2]
except IndexError:
    pass


# Below code does the authentication
# part of the code
gauth = GoogleAuth()

# Creates local webserver and auto
# handles authentication.
gauth.LocalWebserverAuth()	
drive = GoogleDrive(gauth)

# make parent folder
def make_Parent_Folder(folderName):
    

    folder = drive.CreateFile({
        'title' : folderName,
        'mimeType' : 'application/vnd.google-apps.folder'
    })

    # todo return fileID for parent
    folder.Upload()
    print('\nSuccessfully created',folderName)
    
    #list of parent ids to return
    parentIDs = []

    #finding the file id of the folder we just created
    fileList = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    for file in fileList:
        # print('Title: %s, ID: %s' % (file['title'], file['id']))
        # Get the folder ID that you want
        if(file['title'] == folderName):
            parentID = file['id']
            parentIDs.append(parentID)
    
    #parent ids have to be a list now
    #returning the file id for files to return
    return parentID

# folder = drive.CreateFolder()
def make_GDrive_Folder(parentID: str,folderName: str) -> str:

    """A function that takes parent folder ID and the generated foldernames as inputs and returns the fileID as a string.
    """

    folder = drive.CreateFile({
        'title' : folderName,
        'parents' : [{'id' : parentID}], #todo added new
        'mimeType' : 'application/vnd.google-apps.folder'
    })

    folder.Upload()
    print('\n\tSuccessfully created',folderName)
    #finding the file id of the folder we just created
    # ! the keyword 'root' is replacedby the parent id we input, so we look in that folder instead.
    fileList = drive.ListFile({'q': "'{}' in parents and trashed=false".format(parentID)}).GetList()
    for file in fileList:

        if(file['title'] == folderName):
            fileID = file['id']

    #returning the file id for files to return
    return fileID


#creating a file
#a function to create a file
def make_GDrive_File_at_Folder(fileID,getfileName):
    file = drive.CreateFile({
        'parents' : [{'id' : fileID}]
    })

    file.SetContentFile(getfileName)
    file.Upload()
    print('\t\tSuccessfully uploaded',getfileName)


# def main():
def upload_files(filepath):

    from datetime import datetime
    now = datetime.now()
    nowName = now.strftime('%m%d%H%M')

    #uploading the files from the local directory
    parentID = make_Parent_Folder(f"{TASK_ID}_Data Extracts [{nowName}]")

    os.chdir(filepath)
    for extractFile in os.listdir(filepath):
        make_GDrive_File_at_Folder(parentID,extractFile)

def main():
    path = os.getcwd()
    upload_files(path+f"\\data_Extracts\\data_Extract_{TASK_ID}_{TRIAL_ID}")

if __name__ == '__main__':
    main()
