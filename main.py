'''
        DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                    Version 2, December 2004

 Copyright (C) 2022 Woofina <woofinalove@gmail.com>

 Everyone is permitted to copy and distribute verbatim or modified
 copies of this license document, and changing it is allowed as long
 as the name is changed.

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. You just DO WHAT THE FUCK YOU WANT TO.
'''

from os.path import exists as exists
from os.path import join as joinpath
from os import getcwd
from os import walk
from subprocess import check_output
from subprocess import run
from threading import Thread
from queue import Queue
from tqdm import tqdm

## There is currently no way to detect if a jxl file is indeed lossless or not
## Currently it assums all jxl are lossless

## Controlls the preset used in cjxl
speed = 7

## The D used in cjxl. Leave at 0 for lossless
lossy = 0

## Enables/Disables coverting lossy webp (and others in the future) to jxl
## jpgs are always coverted to jxl
## -1: Disabled
##  0: Coverts images to lossless jxl
## >0: Coverts images to lossy jxl
lossyTranscode = -1

## Enables trancode of jxls
jxlTranscode = False

## Number of workers
numThreads = 4


def delete(file):
    run(args='rm "{0}"'.format(file),shell=True)

def isLossless(file):
    fileType = file.split('.')[-1].lower()
    if (fileType == 'webp'):
        return 'Format: Lossless' in check_output('webpinfo "{0}"'.format(file),text=True,shell=True)
    elif (fileType == 'jxl'):
        return True

def encode(file, d):
    ## Converts input file to a jxl file of the same name
    newFileName = '.'.join(file.split('.')[0:-1]) + '.jxl'
    out = run(args='cjxl --quiet -e {0} -d {1} "{2}" "{3}"'.format(speed, str(d), file, newFileName),shell=True)
    if ( (out.returncode != 0) or (not exists(newFileName) )):
        raise Exception('Faild to encode {0} to JXL'.format(file))

def decode(file, output=''):
    ## Converts input file to a png file of the same name
    fileType = file.split('.')[-1].lower()
    if (output == ''):
        output = '.'.join(file.split('.')[0:-1]) + '.png'
    if (fileType == 'jxl'):
        out = run(args='djxl --quiet "{0}" "{1}"'.format(file, output),shell=True)
    elif (fileType == 'webp'):
        out = run(args='dwebp -quiet "{0}" -o "{1}"'.format(file, output),shell=True)
    if ( (out.returncode != 0) or (not exists(output)) ):
        raise Exception('Failed to decode {0}'.format(file))

def convert(q):
    while (q.qsize() > 0):
        file = q.get()
        fileType = file.split('.')[-1].lower()
        if (fileType == 'png'):
            encode(file, lossy)
            delete(file)
        elif (fileType in ['jpg','jpeg','jfif']):
            if (lossyTranscode > 0):
                encode(file, lossyTranscode)
            else:
                encode(file, 0)
            delete(file)
        elif (fileType == 'webp'):
            decode(file)
            if (isLossless(file)):
                encode('.'.join(file.split('.')[0:-1]) + '.png', lossy)
                delete(file)
            elif (lossyTranscode > 0):
                encode(file, lossyTranscode)
                delete(file)
            delete('.'.join(file.split('.')[0:-1]) + '.png')
        elif (fileType == 'jxl'):
            pass
        else:
            raise Exception('Unsupported file type {0}\nHow did we get here?'.format(fileType))
        progress.update(1)
        q.task_done()

def getFiles(dir):
    filesToProcess = []
    for root, subdirs, files in walk(dir):
        for file in files:
            fileType = file.split('.')[-1].lower()
            if (fileType in ['png', 'jpg','jpeg','jfif','webp','jxl']):
                filesToProcess.append(joinpath(root, file))
    print('Files Found: {0}'.format(len(filesToProcess)))
    return filesToProcess


def start(dir):
    global progress
    files = getFiles(dir)
    progress = tqdm(total=len(files))
    q = Queue()
    for file in files:
        q.put(file)
    for i in range(numThreads):
        Thread(target=convert, daemon=True, args=(q,)).start()
    q.join()



def main():
    path = input('Gib Path (or press enter to use current directory): ')
    if (path == ''):
        path = getcwd()
    start(path)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        input(e)
