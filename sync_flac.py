#!/usr/bin/python
from optparse import OptionParser
import re
import os
import os.path
import posixpath
import shutil
import sys
import locale
from mutagen.flac import FLAC
from mutagen.id3 import ID3
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error
import mutagen
import subprocess

# Commad line parsing. Get destination and source directories.

usage = "Usage: %prog [options] destination"
parser = OptionParser(usage=usage)
parser.add_option("-s","--source",dest="source_dir",
                  help="Source Directory to convert from",
                  metavar="SOURCE_DEST")
parser.add_option("--tags_only", action='store_true', dest="tags_only")
(options, args) = parser.parse_args()

if len(args) != 1:
  parser.error("Incorrect number of arguments")

orig_dir=os.getcwd()
dest_dir=os.path.abspath(args[0])

if options.source_dir is None:
  source_dir=os.getcwd()
else:
  source_dir=os.path.abspath(options.source_dir)

  
enc = locale.getpreferredencoding()


# Walk through source directory
for root,dirs,files in os.walk(source_dir):
  dDir = os.path.join(dest_dir,os.path.relpath(root,source_dir))
  for file in files:
    sFileBase, sFileExt   = os.path.splitext(file)
    sFile = os.path.join(root,file)
    dFile = os.path.join(dDir,sFileBase + '.mp3')

    # Create directory if mp3 or flac exist.
    if sFileExt == '.flac' or sFileExt == '.mp3':
      if not os.path.exists(dDir):
        os.makedirs(dDir)
        print "Creating " + dDir

    if (not os.path.exists(dFile) or
        os.stat(dFile).st_mtime < os.stat(sFile).st_mtime or
        options.tags_only) :
      
      if sFileExt == '.mp3':
        if not options.tags_only:
          print "  Moving file  " +sFileBase + sFileExt + " to " + dDir
          shutil.copy(sFile, dDir)
        #Extract album art from file 
        id3 = ID3(dFile)
        for frame in id3.getall('APIC'):
          imgext = '.img'
          if (frame.mime == "image/jpeg") or (frame.mime == "image/jpg"): imgext = '.jpg'
          if (frame.mime == "image/png") : imgext = '.png'
          if (frame.mime == "image/gif") : imgext = '.gif'
        
          try:
            albumArtist = id3.getall('TPE2')[0].text[0]
          except IndexError:

            try:
              albumArtist = id3.getall('TPE1')[0].text[0]
            except IndexError:
              albumArtist = ""
          try:    
            album = id3.getall('TALB')[0].text[0]     
          except:
            album = ""
            
          albArtName = albumArtist + " - " + album
          albumArtFile = os.path.join(dDir,albArtName.encode(enc) + imgext)
          if not os.path.exists(albumArtFile):
            print "Creating file : " + albumArtFile
            file = open(albumArtFile,'wb')
            file.write(frame.data)
            file.close

      elif sFileExt == '.flac':
        if not options.tags_only:
          print "  Converting file  " + sFileBase + sFileExt + " to " + dDir
          command = "sox \"" +sFile + "\" \"" + dFile + "\""
          print "  " + command
          os.popen(command)

      #Read flac tags from FLAC file
        flacTags = FLAC(sFile)
        try:
          mp3 = MP3(dFile)
        except:
          print( dFile + "does not exist, or cannot be opened as mp3")
          break
        
        iso = 'iso-8859-1'
  
        for key, value in flacTags.items():
          if   key == 'album':        mp3['TALB']=mutagen.id3.TALB(encoding=3,text=[value[0]])
          elif key == 'artist':       mp3['TPE1']=mutagen.id3.TPE1(encoding=3,text=[value[0]])
          elif key == 'title':        mp3['TIT2']=mutagen.id3.TIT2(encoding=3,text=[value[0]])
          elif key == 'albumartist':  mp3['TPE2']=mutagen.id3.TPE2(encoding=3,text=[value[0]])
          elif key == 'album artist': mp3['TPE2']=mutagen.id3.TPE2(encoding=3,text=[value[0]])
          elif key == 'date':         mp3['TYER']=mutagen.id3.TYER(encoding=3,text=[value[0]])
          elif key == 'tracknumber':  mp3['TRCK']=mutagen.id3.TRCK(encoding=3,text=[value[0]])
          mp3.save() 
      
      # Get the picture tag from the flac file and store it
      # in the flac dir and the mp3 dir and the mp3 file.
        pictures = flacTags.pictures
        noOfPictures = 0
        for pic in pictures:
          noOfPictures = noOfPictures + 1
        #Save pic to file in source dir and in dest dir.
          imgext = '.img'
          if (pic.mime == "image/jpeg") or (frame.mime == "image/jpg"): imgext = '.jpg'
          if (pic.mime == "image/png") : imgext = '.png'
          if (pic.mime == "image/gif") : imgext = '.gif'
        
          if noOfPictures == 1:
            if flacTags.has_key('albumartist'):
              albumArtist = flacTags['albumartist'][0]
            elif flacTags.has_key('album artist'):
              albumArtist = flacTags['album artist'][0]
            elif flacTags.has_key('artist'):
              albumArtist = flacTags['artist'][0]
            else:
              albumArtist = ""

            if flacTags.has_key('album'):
              album = flacTags['album'][0]
            else: 
              album = ""

            if albumArtist == "" and album == "": 
              albumArtName = "art_" + noOfPictures
            else: 
              albumArtName = albumArtist + " - " + album

          else:
            albumArtName = "art_" + str(noOfPictures)
 
          albumArtFile = os.path.join(dDir,albumArtName.encode(enc) + imgext)
            
#          if not os.path.exists(albumArtFile):
#            print "Creating file : " + albumArtFile            
#            file = open(albumArtFile,'wb')
#            file.write(pic.data)
#            file.close

#          albumArtFile = os.path.join(root,albumArtName.encode(enc) + imgext)  
#          if not os.path.exists(albumArtFile):
#            print "Creating file : " + albumArtFile
#            file = open(albumArtFile,'wb')
#            file.write(pic.data)
#            file.close
#          if noOfPictures == 1:  
#            mp3.tags.add(
#              APIC( encoding = 3,
#                    mime     = pic.mime,
#                    type     = 3,
#                    desc=u'Cover',
#                    data=pic.data ))
#            mp3.save()
                
          
        


