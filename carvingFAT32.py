import struct, math

def chkDrive(driveName) :
   try:
      f = open(driveName, 'rb')
   except FileNotFoundError as e:
      print(e)
      exit(1)
   return f

#FAT32
#Reserved Area + FAT Area + Data Area


#Reserved Area
#Boot Sector + FSINFO + Boot Strap + More reserved sectors

#Boot Sector(sector #0) = VBR
def ReservedArea(f):
   global bytesPerSec, secPerCluster, reservedSector, RootDirClusterOffset, FSinfoOffset, FatSize, FATNum
   sp = f.read(512)
   #Get BPB info
   bytesPerSec = struct.unpack_from('<H', sp, 0xb)[0]
   secPerCluster = struct.unpack_from('B', sp, 0xd)[0]
   reservedSector = struct.unpack_from('<H', sp,0xe)[0]
   FATNum = struct.unpack_from('B', sp, 0x10)[0]
   FatSize = struct.unpack_from('<I', sp, 0x24)[0]
   RootDirClusterOffset = struct.unpack_from('<I', sp, 0x2c)[0]
   FSinfoOffset = struct.unpack_from('<H', sp, 0x30)[0]

#FSINFO(sector #1)
def FSinfo(f):
   f.seek(FSinfoOffset * bytesPerSec)
   sp = f.read(512)

   global signature, numberOfFreeCluster, nextFreeCluster
   signature = struct.unpack_from('>I', sp, 0x0)[0]
   numberOfFreeCluster = struct.unpack_from('I', sp, 0x1e8)[0]
   nextFreeCluster = struct.unpack_from('I', sp, 0x1ec)[0]
#End of Reserved Area

#FAT Area
#FAT #1 + FAT #2
#FAT #1,#2 = FAT Entry(Clusters #0...#n)
def FATArea(f):
   global FATEntry, FATAreaOffset, NumOfFATEntry
   FATAreaOffset = reservedSector * bytesPerSec
   f.seek(FATAreaOffset)
   sp = f.read(FatSize * bytesPerSec)

   NumOfFATEntry = math.ceil((FatSize * bytesPerSec) / 4) #NumOfCluster in FAT#1
   FATEntry = {0:'media_type', 1:'partition_status'} #Cluster #0, #1 reserved
   offset = 8 #Startpoint = Cluster #2 
   for key in range(2, NumOfFATEntry - 2):
      value = struct.unpack_from('<I', sp, offset)[0]
      FATEntry[key] = value
      offset += 4
#End of FAT Area

#Data Area
#Root Directory + File Data + Sub Directory
def DATAArea(f):
   global DATAAreaOffset
   DATAAreaOffset = FATAreaOffset + (FatSize * FATNum * bytesPerSec)

def chkSignature(f, clusterNum):
   signatureList = {"zip":0x504B0304, "docx, pptx, xlsx":0x504B030414000600, "7z":0x377ABCAF, "pdf":0x25504446, "jpeg":0xFFD8, "png":0x89504E470D0A1A0A, "hwp":0xD0CF11E0A1B11AE1}
   f.seek(clusterNum)
   sp = f.read(8)
   getsignature_2byte = struct.unpack_from('>H', sp, 0x0)[0] #2byte
   getsignature_4byte = struct.unpack_from('>I', sp, 0x0)[0] #4byte
   getsignature_8byte = struct.unpack_from('>Q', sp, 0x0)[0] #8byte
   
   if getsignature_4byte == signatureList["zip"]:
      if getsignature_8byte == signatureList["docx, pptx, xlsx"]:
         return list(signatureList.keys())[list(signatureList.values()).index(signatureList["docx, pptx, xlsx"])]
      else:
         return list(signatureList.keys())[list(signatureList.values()).index(signatureList["zip"])]
   elif getsignature_4byte == signatureList["7z"]:
      return list(signatureList.keys())[list(signatureList.values()).index(signatureList["7z"])]
   elif getsignature_4byte == signatureList["pdf"]:
      return list(signatureList.keys())[list(signatureList.values()).index(signatureList["pdf"])]
   elif getsignature_2byte == signatureList["jpeg"]:
      return list(signatureList.keys())[list(signatureList.values()).index(signatureList["jpeg"])]
   elif getsignature_8byte == signatureList["png"]:
      return list(signatureList.keys())[list(signatureList.values()).index(signatureList["png"])]
   elif getsignature_8byte == signatureList["hwp"]:
      return list(signatureList.keys())[list(signatureList.values()).index(signatureList["hwp"])]

def carvingUnallocate(f):
   cluster2 = 2
   for key in FATEntry:
      if (key >= cluster2) and (FATEntry[key] == 0x00): #check cluster#2
         DATAArea_clusterNum = DATAAreaOffset + (key - RootDirClusterOffset) * (secPerCluster * bytesPerSec)
         getsignature = chkSignature(f, DATAArea_clusterNum)
         if getsignature is not None:
            print(DATAArea_clusterNum, "-", getsignature)

def main():
   import sys
   args = sys.argv
   f = chkDrive(args[1])
   ReservedArea(f)
   FSinfo(f)
   FATArea(f)
   DATAArea(f)
   carvingUnallocate(f)
   

if __name__ == '__main__':
     main()