import sys
import os
import glob
import time
import textwrap
from ShotGlobals import *
from NukeJob import *
from QuickTimeJob import *
from DosJob import *
from LinuxJob import *
from XSubmit import *
from XAssets.prod import Shot

TMP_DIR = '/X/tmp/elements/'

def makePlateQTs(plate_path, plateformat, **kwargs):
    """makeplatesqts.py
    @return: tuple of generated thumbnail path and movie path
    """
    stereo = kwargs.has_key('stereo')
    
    if plateformat == 1:
        qtsize = '720x525'
    elif plateformat in [2,3,5,11,13,16]:
        qtsize = '720x547'
    elif plateformat in [4,10,12,19]:
        if stereo:
            qtsize = '720x810'
        else:
            qtsize = '720x405'
    elif plateformat == 6:
        qtsize = '720x306'
    elif plateformat in [7,8]:
        qtsize = '720x410'
    elif plateformat == 9:
        qtsize = '720x540'
    elif plateformat in [14,17]:
        qtsize = '720x274'
    elif plateformat in [15,18]:
        if stereo:
            qtsize = '720x720'
        else:
            qtsize = '720x360'
    elif plateformat == 20:
        qtsize = '1920x1080'
    
    if kwargs.has_key('lut'):
        lut = kwargs['lut']
    else:
        if plateformat in [4,9,10]:
            lut = '0'
        elif plateformat == 12:
            lut = '4'
        elif plateformat == 18:
            lut = '6'
        else:
            lut = '1'
            
    if kwargs.has_key('kk'):
        burnin = 'Keycode'
    elif kwargs.has_key('tc'):
        burnin = 'Timecode'
    else:
        burnin = 'None'
    
    if kwargs.has_key('clean'):
        guides = '0'
    else:
        guides = '0.5'
    
    if kwargs.has_key('offsetPerf'):
        offsetPerf = 'Frames'
    else:
        offsetPerf = 'Perfs'
        
    if kwargs.has_key('flop'):
        flop = kwargs['flop']
    else:
        flop = 'None'
    if flop == 'l':
        flop = 'Left'
    elif flop == 'r':
        flop = 'Right'
    
    if kwargs.has_key('show'):
        show_name = kwargs['show']
    else:
        show_name = None
    
    if kwargs.has_key('shot'):
        shot_name = kwargs['shot']
    else:
        shot_name = None
    
    if kwargs.has_key('elem'):
        elem_name = kwargs['elem']
    else:
        elem_name = None
    
    cwdir = plate_path
    
    if cwdir[:11] == Studio.getP() + "projects" :
        showName = cwdir[cwdir.rfind("projects/")+9:cwdir.find("/",cwdir.rfind("projects/")+9)]
    elif cwdir[:11] == Studio.getX() + "projects" :
        showName = cwdir.split('/')[2]
    else:
        print "Please run this from inside a show directory on X: or P:, or X:\library\elements"
        return (None, None)
        
    JPG_PATH = TMP_DIR + showName + "/_movies/"
    MOVIE_CLEAN_PATH = TMP_DIR + showName + "/"
    THUMB_CLEAN_PATH = TMP_DIR + showName + "/thumbs/"

    THUMB_PATH = None
    MOVIE_PATH = None

    if not os.path.exists(JPG_PATH):
        os.makedirs(JPG_PATH)
    if not os.path.exists(MOVIE_CLEAN_PATH):
        os.makedirs(MOVIE_CLEAN_PATH)
    if not os.path.exists(THUMB_CLEAN_PATH):
        os.makedirs(THUMB_CLEAN_PATH)
        
    ignore_me = ["ANIM", "ANIMG", "flattened", "ANIMR", "FLAT_JPG", "FLAT_JPG_QTR", "HALF", "HDRED", "HI", "HDCROP"]
    for root, dirs, files in os.walk(cwdir):
        for ignore in ignore_me:
            if ignore in dirs:
                dirs.remove(ignore)
        if files :
            #check all files in folder
            tmpFile = files[0]
            checkBaseStr = files[0].split('.')[0]
            for f in files:
                getBaseStr = f.split('.')[0]
                if checkBaseStr != getBaseStr:
                    #different files sequence in folder
                    if getBaseStr.endswith('_left'):
                        tmpFile = f
                        break
            baseStr = tmpFile.split('.')[0]
            padStr = "%0" + str(len(tmpFile.split('.')[1])) + "d"
            try:
                extStr = os.path.splitext(tmpFile)[1]
            except:
                print "ERROR: Problem parsing ", tmpFile
                sys.exit()
            
            globStr = root + os.sep + baseStr + ".*" + extStr
            
            seq = sorted(glob.glob(globStr))
            
            startFrame = int(seq[0].split('.')[1])
            endFrame = int(seq[-1].split('.')[1])
            #length = endFrame-startFrame+1
            length = len(seq)
            
            clipStr = root + os.sep + baseStr + "." + padStr + extStr
            clipStr = clipStr.replace("\\","/")
            if stereo:
                clipStr = clipStr.replace("left","%V")
                baseStr = baseStr[0:-(len(baseStr.split('_')[-1])+1)]
                
            temp_jpg_path = JPG_PATH + "jpg_tmp/" + baseStr + "/" + \
                                                    str(time.time()).split('.')[0] + "/" + \
                                                    baseStr + "." + padStr + ".jpg"
            Studio.mrx_makeDir(os.path.dirname(temp_jpg_path))
            
            custom_lut = ''
            if lut == "7":
                shot = Shot(show_name, shot_name)
                if shot and shot.lut and os.path.isfile(shot.lut):
                    custom_lut = shot.lut
                else:
                    lut = "0"
                    
            stereoHeader = 'Root { views "left #ff0000 \nright #00ff00"}\n'
            nukeScript = textwrap.dedent("""
                Read {
                 file %s
                 colorspace linear
                 last %s
                 }
                webplate2 {
                 format %s
                 stereo %s
                 lut %s
                 custom_lut "%s"
                 burnin %s
                 offsetPerfs %s
                 flop %s
                 guides %s
                 frames %s
                 filename %s
                 file %s
                }
            """ % (clipStr, endFrame, plateformat, stereo, lut, custom_lut,
                    burnin, offsetPerf, flop, guides, endFrame, baseStr,
                    temp_jpg_path))
            if stereo:
                nukeScript = stereoHeader + nukeScript
                
            if not os.path.isdir(Studio.getP() + "/XRender/nuketemp"):
                os.makedirs(Studio.getP() + "/XRender/nuketemp")
            nkFileName = Studio.getP() + "/XRender/nuketemp/plateqt_" + baseStr + str(int((time.time()+time.clock())*100)) + ".nk"
            nkFile = file(nkFileName, "w")
            nkFile.write(nukeScript)
            nkFile.close
            
            if stereo: # Put the clipStr back so the thumbnail gizmo can find it
                clipStr = clipStr.replace("%V","left")
            
            THUMB_PATH = THUMB_CLEAN_PATH + baseStr + ".jpg"
            
            nukeScript2 = textwrap.dedent("""
                Read {
                 file %s
                 colorspace linear
                 last %s
                 }
                webplatethumb {
                 format %s
                 lut %s
                 custom_lut "%s"
                 guides %s
                 file %s
                }
            """ % (clipStr, endFrame, plateformat, lut, custom_lut, guides, THUMB_PATH))
            
            if not os.path.isdir(Studio.getP() + "/XRender/nuketemp"):
                os.makedirs(Studio.getP() + "/XRender/nuketemp")
            nkFileName2 = Studio.getP() + "/XRender/nuketemp/platethumb_" + baseStr + str(int((time.time()+time.clock())*100)) + ".nk"
            nkFile2 = file(nkFileName2, "w")
            nkFile2.write(nukeScript2)
            nkFile2.close
            
            shot = ShotGlobals()
            shot.setShow(showName)
            shot.setShot('_default')
            shot.setSoftwareType('plates')
            shot.setNumParts(1)
            shot.setSlaveGroup('NUKE')
            
            thumbFrame = int((startFrame + endFrame) / 2)
            shot.setFrames(thumbFrame, thumbFrame)
            thumb = NukeJob("plateThumb_" + baseStr,shot)
            thumb.setNukeFile(nkFileName2)
            thumb.setJobName("plateThumb_" + baseStr)
            
            shot.setFrames(startFrame,endFrame+4)
            shot.setNumParts(str((endFrame-startFrame+5)/20 +1))
            plateQT = NukeJob("plateQT_" + baseStr + "_jpg",shot)
            plateQT.setNukeFile(nkFileName)
            plateQT.setJobName("plateQT_" + baseStr + "_jpg")
            
            baseName = temp_jpg_path.replace("P:","/P").replace("X:","/X")
            
            if elem_name:
                MOVIE_PATH = MOVIE_CLEAN_PATH.replace("P:","/P").replace("X:","/X").replace("\\","/") + '/' + elem_name + '.mov'
            else:
                MOVIE_PATH = MOVIE_CLEAN_PATH.replace("P:","/P").replace("X:","/X").replace("\\","/") + '/' + baseStr + '.mov'
                
            formatWidth, formatHeight = qtsize.split('x')
            if int(formatHeight) % 2 == 1:
                formatHeight = int(formatHeight) + 1
            qtsize = formatWidth + 'x' + str(formatHeight)
            shot.setNumParts(1)
            shot.setSlaveGroup('LINUX')
            qt = LinuxJob("plateQT_" + baseStr + "_qt", shot)
            command = Studio.getX() + '/tools/binlinux/_makeplateqt.py %s %s %s' % (baseName, qtsize, MOVIE_PATH)
            qt.setBatchFile(command)
            qt.setJobName("plateQT_" + baseStr + "_qt")
            
            # xelements import
            xelem = LinuxJob("xelements_import" + baseStr, shot)
            xelem.setBatchFile()
            
            # submit thumbnail jobs
            if (plateformat != 20):
                todo = XSubmit()
                todo.addPass(thumb, 2)
                todo.submit()
            
            todo = XSubmit()
            # plate quicktime ffmpeg
            todo.addPass(plateQT)
            # plate quicktime ffmpeg
            todo.addPass(qt, 2)
            
            
            
            # finally, submit to farm
            todo.submit()
            
    return (THUMB_PATH, MOVIE_PATH)




def main():
    if len(sys.argv) < 2:
        # "/P/projects/benhur/plates/DIRT_ELEMENT/3840x2160/DIRT_BH_EL10/"
        print 'Need path to element directory'
        return 1
    plate_path = sys.argv[1]
    
    
if __name__ == '__main__':
    sys.exit(main())
    