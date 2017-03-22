import cv2
import sys
import numpy as np
from random import randint
import math

#Image Loading and initializations
InputName = "in.jpg"
TargetIMG = "qq.jpg"
img_sample = cv2.imread(InputName)
img_target = cv2.imread(TargetIMG)
img_width  = img_target.shape[1]
img_height = img_target.shape[0]
sample_width = img_sample.shape[1]
sample_height = img_sample.shape[0]
img = np.zeros((img_height,img_width,3), np.uint8)
PatchSize = int(4)
OverlapWidth = int(2)
InitialThresConstant = float(25)
#PatchSize = int(10)
#OverlapWidth = int(2)
#InitialThresConstant = float(15)

#Picking random patch to begin
randomPatchHeight = randint(0, sample_height - PatchSize)
randomPatchWidth = randint(0, sample_width - PatchSize)
for i in range(PatchSize):
    for j in range(PatchSize):
        img[i, j] = img_sample[randomPatchHeight + i, randomPatchWidth + j]
#initializating next 
GrowPatchLocation = (0,0)
#---------------------------------------------------------------------------------------#
#|                      Best Fit Patch and related functions                           |#
#---------------------------------------------------------------------------------------#

def OverlapError( px,x, y ):
    xx,yy=px
    a= 0
    b= 0
    OverlapErr= 0
    for i in range(PatchSize):
        for j in range(PatchSize):
            a+= 0.2126 * img_sample[x+j , y+i][0] + 0.7152 * img_sample[x+j , y+i][1] + 0.0722 * img_sample[x+j ,y+i][2]
            b+= 0.2126 * img_target[xx+j , yy+i][0] + 0.7152 * img_target[xx+j , yy+i][1] + 0.0722 *img_target[xx+j ,yy+i][2]
    OverlapErr = ((a/(PatchSize**2))-(b/(PatchSize**2)))
    return abs(OverlapErr)
def GetBestPatches( px ):
    PixelList = []
    for i in range(OverlapWidth,sample_height- PatchSize-OverlapWidth,10 ):
        for j in range(OverlapWidth,sample_width- PatchSize-OverlapWidth,10):
            #print(j)
            #print(PatchSize)
            error = OverlapError(px,i,j )
            if error  < ThresholdOverlapError:
                PixelList.append((i,j))
            elif error < ThresholdOverlapError/2:
                return [(i,j)]
    return PixelList
#-----------------------------------------------------------------------------------------------#
#|                              Quilting and related Functions                                 |#
#-----------------------------------------------------------------------------------------------#

def SSD_Error( offset, imgPx, samplePx ):
    err_r = int(img[imgPx[0] + offset[0], imgPx[1] + offset[1]][0]) -int(img[samplePx[0] + offset[0], samplePx[1] + offset[1]][0])
    err_g = int(img[imgPx[0] + offset[0], imgPx[1] + offset[1]][1]) - int(img[samplePx[0] + offset[0], samplePx[1] + offset[1]][1])
    err_b = int(img[imgPx[0] + offset[0], imgPx[1] + offset[1]][2]) - int(img[samplePx[0] + offset[0], samplePx[1] + offset[1]][2])
    return (err_r**2 + err_g**2 + err_b**2)/3.0

#---------------------------------------------------------------#
#|                  Calculating Cost                           |#
#---------------------------------------------------------------#

def GetCostVertical(imgPx, samplePx):
    Cost = np.zeros((PatchSize, OverlapWidth))
    for j in range(OverlapWidth):
        for i in range(PatchSize):
            if i == PatchSize - 1:
                Cost[i,j] = SSD_Error((i ,j - OverlapWidth), imgPx, samplePx)
            else:
                if j == 0 :
                    Cost[i,j] = SSD_Error((i , j - OverlapWidth), imgPx, samplePx) + min( SSD_Error((i + 1, j - OverlapWidth), imgPx, samplePx),SSD_Error((i + 1,j + 1 - OverlapWidth), imgPx, samplePx) )
                elif j == OverlapWidth - 1:
                    Cost[i,j] = SSD_Error((i, j - OverlapWidth), imgPx, samplePx) + min( SSD_Error((i + 1, j - OverlapWidth), imgPx, samplePx), SSD_Error((i + 1, j - 1 - OverlapWidth), imgPx, samplePx) )
                else:
                    Cost[i,j] = SSD_Error((i, j -OverlapWidth), imgPx, samplePx) + min(SSD_Error((i + 1, j - OverlapWidth), imgPx, samplePx),SSD_Error((i + 1, j + 1 - OverlapWidth), imgPx, samplePx),SSD_Error((i + 1, j - 1 - OverlapWidth), imgPx, samplePx))
    return Cost

def GetCostHorizntl(imgPx, samplePx):
    Cost = np.zeros((OverlapWidth, PatchSize))
    for i in range( OverlapWidth ):
        for j in range( PatchSize ):
            if j == PatchSize - 1:
                Cost[i,j] = SSD_Error((i - OverlapWidth, j), imgPx, samplePx)
            elif i == 0:
                Cost[i,j] = SSD_Error((i - OverlapWidth, j), imgPx, samplePx) + min(SSD_Error((i - OverlapWidth, j + 1), imgPx, samplePx), SSD_Error((i + 1 - OverlapWidth, j + 1), imgPx, samplePx))
            elif i == OverlapWidth - 1:
                Cost[i,j] = SSD_Error((i - OverlapWidth, j), imgPx, samplePx) + min(SSD_Error((i - OverlapWidth, j + 1), imgPx, samplePx), SSD_Error((i - 1 - OverlapWidth, j + 1), imgPx, samplePx))
            else:
                Cost[i,j] = SSD_Error((i - OverlapWidth, j), imgPx, samplePx) + min(SSD_Error((i - OverlapWidth, j + 1), imgPx, samplePx), SSD_Error((i + 1 - OverlapWidth, j + 1), imgPx, samplePx), SSD_Error((i - 1 - OverlapWidth, j + 1), imgPx, samplePx))
    return Cost

#---------------------------------------------------------------#
#|                  Finding Minimum Cost Path                  |#
#---------------------------------------------------------------#

def FindMinCostPathVertical(Cost):
    Boundary = np.zeros((PatchSize),np.int)
    ParentMatrix = np.zeros((PatchSize, OverlapWidth),np.int)
    for i in range(1, PatchSize):
        for j in range(OverlapWidth):
            if j == 0:
                ParentMatrix[i,j] = j if Cost[i-1,j] < Cost[i-1,j+1] else j+1
            elif j == OverlapWidth - 1:
                ParentMatrix[i,j] = j if Cost[i-1,j] < Cost[i-1,j-1] else j-1
            else:
                curr_min = j if Cost[i-1,j] < Cost[i-1,j-1] else j-1
                ParentMatrix[i,j] = curr_min if Cost[i-1,curr_min] < Cost[i-1,j+1] else j+1
            Cost[i,j] += Cost[i-1, ParentMatrix[i,j]]
    minIndex = 0
    for j in range(1,OverlapWidth):
        minIndex = minIndex if Cost[PatchSize - 1, minIndex] < Cost[PatchSize - 1, j] else j
    Boundary[PatchSize-1] = minIndex
    for i in range(PatchSize - 1,0,-1):
        Boundary[i - 1] = ParentMatrix[i,Boundary[i]]
    return Boundary

def FindMinCostPathHorizntl(Cost):
    Boundary = np.zeros(( PatchSize),np.int)
    ParentMatrix = np.zeros((OverlapWidth, PatchSize),np.int)
    for j in range(1, PatchSize):
        for i in range(OverlapWidth):
            if i == 0:
                ParentMatrix[i,j] = i if Cost[i,j-1] < Cost[i+1,j-1] else i + 1
            elif i == OverlapWidth - 1:
                ParentMatrix[i,j] = i if Cost[i,j-1] < Cost[i-1,j-1] else i - 1
            else:
                curr_min = i if Cost[i,j-1] < Cost[i-1,j-1] else i - 1
                ParentMatrix[i,j] = curr_min if Cost[curr_min,j-1] < Cost[i-1,j-1] else i + 1
            Cost[i,j] += Cost[ParentMatrix[i,j], j-1]
    minIndex = 0
    for i in range(1,OverlapWidth):
        minIndex = minIndex if Cost[minIndex, PatchSize - 1] < Cost[i, PatchSize - 1] else i
    Boundary[PatchSize-1] = minIndex
    for j in range(PatchSize - 1,0,-1):
        Boundary[j - 1] = ParentMatrix[Boundary[j],j]
    return Boundary

#---------------------------------------------------------------#
#|                      Quilting                               |#
#---------------------------------------------------------------#

def QuiltVertical(Boundary, imgPx, samplePx):
    for i in range(PatchSize):
        for j in range(Boundary[i], 0, -1):
            img[imgPx[0] + i, imgPx[1] - j] = img_sample[ samplePx[0] + i, samplePx[1] - j ]
def QuiltHorizntl(Boundary, imgPx, samplePx):
    for j in range(PatchSize):
        for i in range(Boundary[j], 0, -1):
            img[imgPx[0] - i, imgPx[1] + j] = img_sample[samplePx[0] - i, samplePx[1] + j]

def QuiltPatches( imgPx, samplePx ):
    #check for top layer
    if imgPx[0] == 0:
        Cost = GetCostVertical(imgPx, samplePx)
        # Getting boundary to stitch
        Boundary = FindMinCostPathVertical(Cost)
        #Quilting Patches
        QuiltVertical(Boundary, imgPx, samplePx)
    #check for leftmost layer
    elif imgPx[1] == 0:
        Cost = GetCostHorizntl(imgPx, samplePx)
        #Boundary to stitch
        Boundary = FindMinCostPathHorizntl(Cost)
        #Quilting Patches
        QuiltHorizntl(Boundary, imgPx, samplePx)
    #for pixel placed inside 
    else:
        CostVertical = GetCostVertical(imgPx, samplePx)
        CostHorizntl = GetCostHorizntl(imgPx, samplePx)
        BoundaryVertical = FindMinCostPathVertical(CostVertical)
        BoundaryHorizntl = FindMinCostPathHorizntl(CostHorizntl)
        QuiltVertical(BoundaryVertical, imgPx, samplePx)
        QuiltHorizntl(BoundaryHorizntl, imgPx, samplePx)


#--------------------------------------------------------------------------------------------------------#
#                                   Growing Image Patch-by-patch                                        |#
#--------------------------------------------------------------------------------------------------------#

def FillImage( imgPx, samplePx ):
    for i in range(PatchSize):
        for j in range(PatchSize):
            img[ imgPx[0] + i, imgPx[1] + j ] = img_sample[ samplePx[0] + i, samplePx[1] + j ]

pixelsCompleted = 0
TotalPatches = ( (img_height - 1 )/ PatchSize )*((img_width)/ PatchSize) - 1
sys.stdout.write("TotalPatches %d " % (TotalPatches))
sys.stdout.write("Progress : [%-20s] %d%% | PixelsCompleted: %d | ThresholdConstant: --.------" % ((pixelsCompleted*20/TotalPatches), (100*pixelsCompleted)/TotalPatches, pixelsCompleted))
sys.stdout.flush()
r=0
while GrowPatchLocation[0] + PatchSize < img_height:
    pixelsCompleted += 1
    ThresholdConstant = InitialThresConstant
    #set progress to zer0
    progress = 0 
    while progress == 0:
        ThresholdOverlapError = ThresholdConstant
        #Get Best matches for current pixel
        List = GetBestPatches(GrowPatchLocation)
        if len(List) > 0:
            progress = 1
            #Make A random selection from best fit pxls
            sampleMatch = List[ randint(0, len(List) - 1) ]
            FillImage( GrowPatchLocation, sampleMatch )
            #Quilt this with in curr location
            QuiltPatches( GrowPatchLocation, sampleMatch )
            #upadate cur pixel location
            GrowPatchLocation = (GrowPatchLocation[0], GrowPatchLocation[1] + PatchSize)
            if GrowPatchLocation[1] + PatchSize > img_width:
                GrowPatchLocation = (GrowPatchLocation[0] + PatchSize, 0)
        #if not progressed, increse threshold
        else:
            ThresholdConstant *= 1.1
            print('increse ThresholdConstant')
    # print pixelsCompleted, ThresholdConstant
    print(pixelsCompleted/TotalPatches)
    if(r==0  and pixelsCompleted/TotalPatches>5):
        cv2.imwrite('C:\\Users\\Pinlin-Admin\\Desktop\\Patch-Based-Texture-Synthesis-master\\CC.jpg' , img)
        r=1
    #sys.stdout.write('\r')
    #sys.stdout.write("Progress : [%-20s] %d%% | PixelsCompleted: %d | ThresholdConstant: %f" % ((pixelsCompleted*20/TotalPatches), (100*pixelsCompleted)/TotalPatches, pixelsCompleted, ThresholdConstant))
    #sys.stdout.write('\r')
    #sys.stdout.flush()
    
# Displaying Images
#cv2.imshow('Sample Texture',img_sample)
#cv2.waitKey(0)
#cv2.destroyAllWindows()
cv2.imshow('Generated Image',img)
cv2.waitKey(0)
cv2.destroyAllWindows()
