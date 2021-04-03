from ftplib import FTP
import sys
import os
import ftplib
import shutil
import logging

logger = logging.getLogger(__name__)

class VoissFTPPutFiles:
  
  def __init__(self):#{{{#
    self.serverName_=''
    self.serverPort_=21
    self.user_=''
    self.password_=''
    self.defaultDir_='.'
    self.ftp_= None
    self.rootDir_= True
    self.remoteDir_ = '/'
    self.localDir_ = '.'
    #}}}#

  def setUser(self, user):#{{{#
    self.user_=user
    #}}}#

  def setPassword(self, password):#{{{#
    self.password_=password
    #}}}#

  def setServerName(self, serverName):#{{{#
    self.serverName_=serverName
    #}}}#

  def setServerPort(self, serverPort):#{{{#
    self.serverPort_=serverPort
    #}}}#

  def setLocalDir(self, localDir):#{{{#
    self.localDir_=localDir
    #}}}#

  def setRemoteDir(self, remoteDir):#{{{#
    self.remoteDir_= remoteDir
    #}}}#

  def uploadFiles(self):#{{{#
    
    logger.info( 'The file <' + self.localDir_ + '> Uploading files')
    
    #Validates the local directory
    if not os.path.exists(self.localDir_):
      logger.info( 'The file <' + self.localDir_ + '> it does not exists on the local machine')
      return
  
    #Make the FTP connection
    self.ftp_ = FTP(self.serverName_)
    self.ftp_.login(self.user_, self.password_)
    logger.info( 'Connected to server <'  + self.serverName_ + '> as user <' + self.user_ + '>')

    try:
      self.ftp_.cwd(self.remoteDir_)
    except ftplib.error_perm as detail:
      logger.info( 'The directory <' +  self.remoteDir_ + '> was not found on the server: <' + self.serverName_ + '>')
      self.ftp_.quit()
      return

    logger.info( 'Copying local files from  <' + self.localDir_ + '> to ftp://' + self.serverName_ + '/' + self.remoteDir_  )

    try:
      #self.ftp_.cwd('prices')
      self.ftp_.storbinary('STOR prices.txt' , open('glFTP/prices.txt', 'rb'))
    except ftplib.all_errors:
      pass
    
    self.ftp_.quit()
    logger.info('All the files are on the server now')
    #}}}#

