# coding=utf-8

from __future__ import unicode_literals
from dateutil.relativedelta import relativedelta
from django.utils.encoding  import python_2_unicode_compatible
from django.core.exceptions import NON_FIELD_ERRORS
from django.db import models
from glEmail.src.glemail import GLEmail
import datetime
import unicodedata
from glPdf.glQRCustomer import GLQRCustomer
import glPdf
import qrcode

import unidecode

import time
import logging
from django.core.exceptions import ValidationError
#import urllib2
import urllib
import errno
import os
import socket

logger = logging.getLogger(__name__)

ADD_CUSTOMER_COMMAND = "33"

USERS_TYPES=(
      ('WEB', 'WEB'),
      ('CONDUCTOR', 'CONDUCTOR'),
      ('DESPACHADOR', 'DESPACHADOR'),
      ('SUPERVISOR', 'SUPERVISOR'),
      ('OFICINA', 'OFICINA'),
      )

COMMAND_KIND=(
      ('NINGUNO', 'NINGUNO'),
      ('FACTURA ISLA', 'FACTURA ISLA'),
      ('FACTURA WEB', 'FACTURA WEB'),
      ('TICKET', 'TICKET'),
      )

COMMAND_STATUS=(
      ('ESPERA', 'Espera'),
      ('EN PROCESO', 'En Proceso'),
      ('FINALIZO', 'Finalizo'),
      )

CUSTOMER_COUNTRY=(
      ('MEXICO'   , 'México'),
      )

USER_SERVICE=(
      ('FLOTILLAS'   , 'Flotillas'),
      ('VALES'   , 'Vales'),
      ('PUNTOS'   , 'Puntos'),
      ('TAE'   , 'Tae'),
      )

CUSTOMER_KIND_GL=(
      ('CONTADO'   , 'Contado'),
      )

CUSTOMER_KIND=(
      ('DEBITO'   , 'Debito'),
      ('CREDITO'  , 'Credito'),
      ('EFECTIVO' , 'Efectivo'),
      )

CUSTOMER_BILLING=(
      ('AL PERIODO'   , 'Al Periodo'),
      ('INMEDIATO'  , 'Inmediato'),
      )

CUSTOMER_PERIOD=(
      ('SEMANAL'   , 'Semanal'),
      ('QUINCENAL'  , 'Quincenal'),
      ('MENSUAL'  , 'Mensual'),
      )

CUSTOMER_STATES=(
      ('AGUASCALIENTES'   , 'Aguascalientes'),
      ('BAJA CALIFORNIA'   , 'Baja California'),
      ('BAJA CALIFORNIA SUR'   , 'Baja California Sur'),
      ('CAMPECHE'   , 'Campeche'),
      ('CHIAPAS'   , 'Chiapas'),
      ('CHIHUAHUA'   , 'Chihuahua'),
      ('COAHUILA'   , 'Coahuila'),
      ('COLIMA'   , 'Colima'),
      ('CIUDAD DE MEXICO'   , 'Ciudad de México'),
      ('DURANGO'   , 'Durango'),
      ('GUANAJUATO'   , 'Guanajuato'),
      ('GUERRERO'   , 'Guerrero'),
      ('HIDALGO'   , 'Hidalgo'),
      ('JALISCO'   , 'Jalisco'),
      ('MEXICO'   , 'México'),
      ('MICHOACAN'   , 'Michoacán'),
      ('MORELOS'   , 'Morelos'),
      ('NAYARIT'   , 'Nayarit'),
      ('NUEVO LEON'   , 'Nuevo León'),
      ('OAXACA'   , 'Oaxaca'),
      ('PUEBLA'   , 'Puebla'),
      ('QUERETARO'   , 'Querétaro'),
      ('QUINTANA ROO'   , 'Quintana Roo'),
      ('SAN LUIS POTOSI'   , 'San Luis Potosí'),
      ('SINALOA'   , 'Sinaloa'),
      ('SONORA'   , 'Sonora'),
      ('TABASCO'   , 'Tabasco'),
      ('TAMAULIPAS'   , 'Tamaulipas'),
      ('TLAXCALA'   , 'Tlaxcala'),
      ('VERACRUZ'   , 'Veracruz'),
      ('YUCATAN'   , 'Yucatán'),
      ('ZACATECAS'   , 'Zacatecas'),
      )


def strip_accents(text):

   try:
      ext = str(text, 'utf-8')
   except NameError: # str is a default on python 3 
      pass
   text = strdata.normalize('NFD', text)
   text = text.encode('ascii', 'ignore')
   text = text.decode("utf-8")
   return str(text)

@python_2_unicode_compatible 
class GLStationGroup(models.Model):#{{{#
   vStationGroupId    = models.AutoField(primary_key=True)
   vStationName       = models.CharField(max_length=80,unique=True ,null=False, blank=False,verbose_name="Nombre del Grupo")
   vStationGroupDesc  = models.CharField(max_length=100, null=True, blank=True,verbose_name="Descripcion",default=None)

   def replicateStationGroup(self,host, port, moduleName, serviceName):

      urlHeader ='http://' + str(host) + ':' + str(port) + '/' + moduleName + '/' + serviceName + '/'
      print ('Replicating to ' + str(urlHeader))

      url=''
      url+='?stationName='+ str(self.vStationName)
      url+='&stationGroupName='+ str(self.vStationGroupDesc)

      url= url.replace(' ','_SPACE_')
      
      urlFinal = urlHeader + url

      try:
         response = urllib.request.urlopen(str(unidecode.unidecode(urlFinal))).read()
      except :
         raise ValueError(str(moduleName))


   def clean(self, *args, **kwargs):
      self.replicateStationGroup(socket.gethostbyname(socket.gethostname()),'20002','fleetsModule','AddStationGroup')
      self.replicateStationGroup(socket.gethostbyname(socket.gethostname()),'20003','pointsModule','AddStationGroup')
      self.replicateStationGroup(socket.gethostbyname(socket.gethostname()),'20004','taeModule','AddStationGroup')

   def full_clean(self, *args, **kwargs):
      return self.clean(*args, **kwargs)

   def save(self, *args, **kwargs):
      self.full_clean()
      super(GLStationGroup, self).save(*args, **kwargs)




   class Meta:
      verbose_name='Grupo'
      verbose_name_plural='Grupos'
   def __str__(self):
      return self.vStationGroupDesc
   #}}}#

@python_2_unicode_compatible 
class GLWebCommand(models.Model):#{{{#
   vWebCommandId           = models.AutoField(primary_key=True)
   vStationId              = models.ForeignKey('GLStation'  ,db_column="vStationId"  , blank=True, null=True , verbose_name="Estacion")
   vUserId                 = models.ForeignKey('GLUser',on_delete=models.SET_NULL,null=True,db_column='vUserId', verbose_name="Usuario")
   vCommandKind            = models.CharField(max_length=20, choices=COMMAND_KIND, default='FACTURA WEB', verbose_name="Tipo de Comando")
   vCommandInfo            = models.CharField(max_length=3000 ,blank=False, null=False, verbose_name="Información de Comando")
   vIsActive               = models.BooleanField(default=True, verbose_name="¿Esta Activo?")
   vCommandStatus          = models.CharField(max_length=25, choices=COMMAND_STATUS, default='ESPERA', verbose_name="Estado")
   vStartDate              = models.DateTimeField(auto_now_add=True, verbose_name="Hora de inicio ejecución")
   vEndDate                = models.DateTimeField(auto_now_add=True, verbose_name="Hora de fin ejecución")
   vStatusResponse         = models.CharField(max_length=200, null=True, blank=True,default=None, verbose_name="Respuesta")

   class Meta:
      verbose_name= 'Comando de Web'
      verbose_name_plural='Comandos de Web'
   def __str__(self):
      return self.vCommandKind
   #}}}#

@python_2_unicode_compatible 
class GLStation(models.Model):#{{{#
   vStationId          = models.AutoField(primary_key=True)
   vStationDesc        = models.CharField(max_length=100, null=False, blank=False, unique=True, verbose_name="Descripcion de la Estacion")
   vStationGroupId     = models.ForeignKey('GLStationGroup',on_delete=models.SET_NULL, db_column='vStationGroupId', null=True, blank=True, verbose_name="Grupo de la Estacion")
   vStationWHost       = models.CharField(max_length=100, null=True, blank=True, verbose_name="Dominio Remoto de la Estación")
   vStationLHost       = models.CharField(max_length=100, null=True, blank=True, verbose_name="Dominio Local de la Estación")
   vStationWPort       = models.CharField(max_length=10, null=True, blank=True, verbose_name="Puerto Web")
   vStationLPort       = models.CharField(max_length=10, null=True, blank=True, verbose_name="Puerto Local")
   vHeader             = models.CharField(max_length=500, null=True, blank=True, editable=False, verbose_name="Encabezado de Ticket")
   vFooter             = models.CharField(max_length=500, null=True, blank=True, editable=False, verbose_name="Pie de Ticket")
   vRequireDispatcher  = models.BooleanField(default=False, verbose_name="¿Requiere Despachador?")
   vRequireDriver      = models.BooleanField(default=False, verbose_name="¿Requiere Conductor?")
   vRequireAuth        = models.BooleanField(default=False, verbose_name="¿Liberar vales desde App?")
   vSignDispatchers    = models.BooleanField(default=False, verbose_name="¿Firmar Despachadores en Isla?")
   vMinAmount          = models.FloatField(default=0, verbose_name="Monto Minimo")
   vPaymentDays        = models.IntegerField( default=15,blank=True, null=True, verbose_name="Días Pago entre Estaciones")
   vBilling            = models.BooleanField(default=True, verbose_name="¿Facturar desde Web?")

   vPrintTime          = models.CharField( max_length=3,default=1,blank=False, null=False, verbose_name="Tiempo Max. Impresion")

   vSimulatePort       = models.BooleanField(default=False, verbose_name="¿Modo simulación puerto?")

   vHeader1            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Header 1")
   vHeader2            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Header 2")
   vHeader3            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Header 3")
   vHeader4            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Header 4")
   vHeader5            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Header 5")
   vHeader6            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Header 6")
   vHeader7            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Header 7")
   vHeader8            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Header 8")

   vFooter1            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Footer 1")
   vFooter2            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Footer 2")
   vFooter3            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Footer 3")
   vFooter4            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Footer 4")
   vFooter5            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Footer 5")
   vFooter6            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Footer 6")
   vFooter7            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Footer 7")
   vFooter8            = models.CharField(max_length=80, null=True, blank=True, verbose_name="Footer 8")


   vUsePoints          = models.BooleanField(default=False, verbose_name="¿Modulo Puntos?")
   vUseTAE             = models.BooleanField(default=False, verbose_name="¿Modulo TAE?")
   vUseFleets          = models.BooleanField(default=False, verbose_name="¿Modulo Flotillas?")

   vShowProductId     = models.BooleanField(default=False, verbose_name="¿Mostrar Producto Id?")
   vShowMaxAmount      = models.BooleanField(default=False, verbose_name="¿Mostrar Monto Máximo?")
   vShowMaxVolume      = models.BooleanField(default=False, verbose_name="¿Mostrar Volumen Máximo?")
   vShowDesc           = models.BooleanField(default=False, verbose_name="¿Mostrar Descripcion?")
   vShowBrand          = models.BooleanField(default=False, verbose_name="¿Mostrar Marca de Auto?")
   vShowModel          = models.BooleanField(default=False, verbose_name="¿Mostrar Modelo de Auto?")
   vShowPlate          = models.BooleanField(default=False, verbose_name="¿Mostrar Placa de Auto?")
   vShowEnumber        = models.BooleanField(default=False, verbose_name="¿Mostrar Número Economico?")
   vShowBalance        = models.BooleanField(default=False, verbose_name="¿Mostrar Saldo?")

   vPrintBoth         = models.BooleanField(default=False, verbose_name="¿Original y copia en primer impresion?")
 


   def replicateStation(self,host, port, moduleName, serviceName):

      urlHeader ='http://' + str(host) + ':' + str(port) + '/' + moduleName + '/' + serviceName + '/'
      print ('Replicating to ' + str(urlHeader))

      url=''
      url+='?stationDesc=' + str(self.vStationDesc) 
      if self.vStationGroupId:
         url+='&stationGroupId=' + str(self.vStationGroupId.vStationName)
      else:
         url+='&stationGroupId=' + str('')

      url+='&stationWHost='+ str(self.vStationWHost)
      url+='&stationLHost='+ str(self.vStationLHost)
      url+='&stationWPort='+ str(self.vStationWPort)
      url+='&stationLPort='+ str(self.vStationLPort)
      url+='&header='+ str(self.vHeader)
      url+='&footer='+ str(self.vFooter)
      url+='&minAmount='+ str(self.vMinAmount)

      if self.vRequireDispatcher:
         url+='&requireDispatcher='+ str(self.vRequireDispatcher)
      else:
         url+='&requireDispatcher='+ str('')

      if self.vRequireDriver:
         url+='&requireDriver='+ str(self.vRequireDriver)
      else:
         url+='&requireDriver='+ str('')

      if self.vRequireAuth:
         url+='&requireAuth='+ str(self.vRequireAuth)
      else:
         url+='&requireAuth='+ str('')

      if self.vSignDispatchers:
         url+='&signDispatchers='+ str(self.vSignDispatchers)
      else:
         url+='&signDispatchers='+ str('')

      if self.vPaymentDays:
         url+='&paymentDays='+ str(self.vPaymentDays)
      else:
         url+='&paymentDays='+ str('15')
      
      url= url.replace(' ','_SPACE_')

      urlFinal = urlHeader + url
      try:
         response = urllib.request.urlopen(str(unidecode.unidecode(urlFinal))).read()
         return True
      except Exception as e:
         print('Exceptiom:' +  str(e))
         return False

   def clean(self, *args, **kwargs):
      if self.vUseFleets:
         self.replicateStation(socket.gethostbyname(socket.gethostname()),'20002','fleetsModule','AddStation')
      if self.vUsePoints:
         self.replicateStation(socket.gethostbyname(socket.gethostname()),'20003','pointsModule','AddStation')
      if self.vUseTAE:
         self.replicateStation(socket.gethostbyname(socket.gethostname()),'20004','taeModule','AddStation')
      
      try:
         val= int(self.vStationDesc)
      except ValueError:
         raise ValidationError({NON_FIELD_ERRORS: [
                     'Descripción de estación solo puede ser numerica ',],})

   def full_clean(self, *args, **kwargs):
      return self.clean(*args, **kwargs)

   def save(self, *args, **kwargs):
      self.full_clean()
      super(GLStation, self).save(*args, **kwargs)

   class Meta:
      verbose_name= 'Estacion'
      verbose_name_plural='Estaciones'
   def __str__(self):
      return self.vStationDesc
   #}}}#

@python_2_unicode_compatible 
class GLDevice(models.Model): #{{{#

   vDeviceId          = models.AutoField(primary_key=True)
   vUserId            = models.ForeignKey('GLUser',on_delete=models.SET_NULL,null=True,db_column='vUserId', verbose_name="Usuario")
   vDeviceName        = models.CharField(max_length=50 ,unique=True,blank=False, null=False,verbose_name="Nombre de Dispositivo")
   vUserAgent         = models.CharField(max_length=200,blank=False, null=False, verbose_name="UserAgent")
   vOldUserAgent      = models.CharField(max_length=200,blank=True, null=True, verbose_name="Browser hash")
   vIPAddress         = models.CharField(max_length=50 ,blank=False, null=False, verbose_name="Direccion IP")
   vStationId         = models.ForeignKey('GLStation'  ,db_column="vStationId"  , blank=True, null=True , verbose_name="Estacion")
   vDeviceToken       = models.CharField(max_length=40 ,blank=False, null=False, verbose_name="Token")
   vIsActive          = models.BooleanField(default=False, verbose_name="¿Esta Activo?")
   vPrintTicket       = models.BooleanField(default=False, verbose_name="¿Imprimir Ticket?")

   vLogoutInactivity   = models.BooleanField(default=False, verbose_name="¿Salir por inactividad?")
   vTimeout            = models.IntegerField( default=1,blank=True, null=True, verbose_name="Minutos de inactividad")

   vVirtualKeyboard    = models.BooleanField(default=False, verbose_name="¿Teclado Virtual?")

   vResetStation       = models.BooleanField(default=False, verbose_name="¿Resetear estacion?")
   vResetAuth          = models.BooleanField(default=False, verbose_name="¿Resetear autorizacion?")
   vPrintLocal         = models.BooleanField(default=False, verbose_name="¿Impresion en terminal?")

   def replicateDevice(self,host, port, moduleName, serviceName):

      urlHeader ='http://' + str(host) + ':' + str(port) + '/' + moduleName + '/' + serviceName + '/'

      url=''
      if self.vUserId:
         url+='?userId='+ str(self.vUserId.vUserAccess)
      else:
         url+='?userId='+ str('')

      if self.vStationId:
         url+='&stationDesc='+ str(self.vStationId.vStationDesc)
      else:
         url+='&stationDesc='+ str('')

      url+='&deviceName='+ str(self.vDeviceName)
      url+='&userAgent='+ str(self.vUserAgent)
      url+='&oldUserAgent='+ str(self.vOldUserAgent)
      url+='&ipAddress='+ str(self.vIPAddress)
      url+='&deviceToken='+ str(self.vDeviceToken)

      if self.vIsActive:
         url+='&isActive='+ str(self.vIsActive)
      else:
         url+='&isActive='+ str('')

      if self.vPrintTicket:
         url+='&printTicket='+ str(self.vPrintTicket)
      else:
         url+='&printTicket='+ str('')

      url= url.replace(' ','_SPACE_')

      urlFinal = urlHeader + url

      try:
         response = urllib.request.urlopen(str(unidecode.unidecode(urlFinal))).read()
      except :
         raise ValueError(str(moduleName))


   def clean(self, *args, **kwargs):
      print ('')
      if self.vStationId:
         if self.vStationId.vUseFleets:
            print(f"{self.vStationId.vUseFleets}")
            self.replicateDevice(socket.gethostbyname(socket.gethostname()),'20002','fleetsModule','AddDevice') 
         if self.vStationId.vUsePoints:
            print(f"{self.vStationId.vUsePoints}")
            self.replicateDevice(socket.gethostbyname(socket.gethostname()),'20003','pointsModule','AddDevice') 
         if self.vStationId.vUseTAE:
            print(f"{self.vStationId.vUseTAE}")
            self.replicateDevice(socket.gethostbyname(socket.gethostname()),'20004','taeModule','AddDevice') 

   def full_clean(self, *args, **kwargs):
      return self.clean(*args, **kwargs)

   def save(self, *args, **kwargs):
      self.full_clean()
      super(GLDevice, self).save(*args, **kwargs)

   class Meta:
      verbose_name="Dispositivo"
      verbose_name_plural='Dispositivos'
   def __str__(self):
      return str(self.vDeviceName) + ' - ' + str(self.vDeviceToken)

#}}}#

@python_2_unicode_compatible 
class GLUser(models.Model): #{{{#
   vUserId           = models.AutoField(db_column='vUserId',primary_key= True)
   vStationId        = models.ForeignKey('GLStation',on_delete=models.SET_NULL,db_column="vStationId",null=True, blank=True, default="", verbose_name="Estacion")
   vActive           = models.BooleanField(default=True,verbose_name="¿Esta activo?")
   vMulti            = models.BooleanField(default=False,verbose_name="¿Multi estacion?")
   vKind             = models.CharField(max_length=11, choices=USERS_TYPES, default='WEB', verbose_name="Tipo")
   vName             = models.CharField(max_length=50 ,blank=False, null=False, verbose_name="Nombre")
   vLastname         = models.CharField(max_length=50 ,blank=False, null=False, verbose_name="Apellidos")
   vAge              = models.IntegerField(blank=True, null=True, verbose_name="Edad")
   vMail             = models.CharField(max_length=50 ,blank=True, null=True, verbose_name="Correo")
   vPhone            = models.CharField(max_length=20 ,blank=True, null=True, verbose_name="Telefono")
   vMobilePhone      = models.CharField(max_length=20 ,blank=True, null=True, verbose_name="Celular")
   vUserAccess       = models.CharField(max_length=100 ,blank=False, null=False, verbose_name="Usuario")
   vPassAccess       = models.CharField(max_length=100 ,blank=False, null=False, verbose_name="Password")
   vService          = models.CharField(max_length=9, choices=USER_SERVICE,null=True,blank=True, verbose_name="Acceso a servicio de")
   vRFC              = models.CharField(max_length=14 ,null=True, blank=True, verbose_name='RFC')
   vIsAdmin          = models.BooleanField(default=False,verbose_name="¿Permisos Admin?")
   vIsKiosk          = models.BooleanField(default=False,verbose_name="¿Modo Kiosco?")


   def replicateUser(self,host, port, moduleName, serviceName):

      urlHeader ='http://' + str(host) + ':' + str(port) + '/' + moduleName + '/' + serviceName + '/'

      url=''
      if self.vStationId:
         url+='?stationId='+ str(self.vStationId.vStationDesc)
      else:
         url+='?stationId='+ str('')

      if self.vActive:
         url+='&active='+ str(self.vActive)
      else:
         url+='&active='+ str('')

      if self.vMulti:
         url+='&multi='+ str(self.vMulti)
      else:
         url+='&multi='+ str('')

      url+='&kind='+ str(self.vKind)
      url+='&name='+ str(self.vName)
      url+='&lastName='+ str(self.vLastname)

      if self.vAge:
         if int(self.vAge)>0:
            url+='&age='+ str(self.vAge)
         else:
            url+='&age='+ str('0')
      else:
         url+='&age='+ str('0')

      url+='&mail='+ str(self.vMail)
      url+='&phone='+ str(self.vPhone)
      url+='&mobilePhone='+ str(self.vMobilePhone)
      url+='&userAccess='+ str(self.vUserAccess)
      url+='&passAccess='+ str(self.vPassAccess)
      url+='&service='+ str(self.vService)
      url+='&customerRFC='+ str(self.vRFC)

      if self.vIsAdmin:
         url+='&isAdmin='+ str(self.vIsAdmin)
      else:
         url+='&isAdmin='+ str('')

      if self.vIsKiosk:
         url+='&isKiosk='+ str(self.vIsKiosk)
      else:
         url+='&isKiosk='+ str('')


      url= url.replace(' ','_SPACE_')

      urlFinal = urlHeader + url

      try:
         response = urllib.request.urlopen(str(unidecode.unidecode(urlFinal))).read()
      except :
         raise ValueError(str(moduleName))


   def clean(self, *args, **kwargs):
      
      try:

         if self.vService:
            if not self.vRFC:
               raise ValidationError({NON_FIELD_ERRORS: [
                        'Debe escribir el RFC de cliente si desea crear un usuario para Cliente ',],})

         if not self:
               raise ValidationError({NON_FIELD_ERRORS: [
                        'Debes seleccionar todos los campos obligatorios ',],})

         if not self.vStationId:
               raise ValidationError({NON_FIELD_ERRORS: [
                        'Debes seleccionar la estación ',],})

         if not self.vUserAccess:
               raise ValidationError({NON_FIELD_ERRORS: [
                        'Debes escribir el nombre de usuario ',],})

         if not self.vPassAccess:
               raise ValidationError({NON_FIELD_ERRORS: [
                        'Debes escribir el password del usuario ',],})



         currentUser = GLUser.objects.filter(vPassAccess= self.vPassAccess, vStationId=self.vStationId)

         if currentUser:
            currentUser= currentUser[0]
            if currentUser.vUserId != self.vUserId:
               raise ValidationError({NON_FIELD_ERRORS: [
                        'Introduce un password diferente, no se permite mas de un usuario en la misma estacion con el mismo password ',],})

      except GLUser.DoesNotExist:
         logger.info('User does not exist')
      if self.vStationId:
         if self.vStationId.vUseFleets:
            self.replicateUser(socket.gethostbyname(socket.gethostname()),'20002','fleetsModule','AddUser') 
         if self.vStationId.vUsePoints:
            self.replicateUser(socket.gethostbyname(socket.gethostname()),'20003','pointsModule','AddUser') 
         if self.vStationId.vUseTAE:
            self.replicateUser(socket.gethostbyname(socket.gethostname()),'20004','taeModule','AddUser') 
      #super(GLUser, self).clean(*args, **kwargs)

   def full_clean(self, *args, **kwargs):
      return self.clean(*args, **kwargs)


   def createFunction(self, functionName, currentIndex):
      newFunction = GLFunctions()
      newFunction.vFunctionName=functionName
      newFunction.vFunctionDesc=functionName
      newFunction.vOrder= currentIndex
      newFunction.save()
      return newFunction

   def validateFunctions(self):
      print('Validando funciones')
      functions=["Ticket","Factura","Tira Inv","Servicios","Puntos","Preset","Cancela Preset","Flotillas"]
      currentIndex=1
      for functionName in functions:
         currentFunction = GLFunctions.objects.filter(vFunctionName=functionName)
         functionId=None
         if not currentFunction:
            functionId=self.createFunction(functionName, currentIndex)
         else:
            functionId= currentFunction[0]
         currentIndex= currentIndex+1
         currentUserFunction= GLUserFunction.objects.filter(vFunctionsId=functionId, vUserId=self)
         if not currentUserFunction:
            newUserFunction= GLUserFunction()
            newUserFunction.vFunctionsId= functionId
            newUserFunction.vUserId=self
            newUserFunction.save()



   def save(self, *args, **kwargs):
      self.full_clean()
   

      super(GLUser, self).save(*args, **kwargs)
      self.validateFunctions()


   class Meta:
      verbose_name = 'Usuario'
      verbose_name_plural='Usuarios'
      unique_together = ('vStationId', 'vUserAccess',)
   def __str__(self):
      return self.vName + ' ' + self.vLastname
#}}}#

def sendAddCustomer(ipAddress, 
                        port,
                        businessName,
                        commercialName, 
                        rfc, 
                        status,
                        mail,
                        accountBank,
                        bank,
                        street, 
                        externalNumber,
                        internalNumber, 
                        colony,
                        location, 
                        reference, 
                        town,
                        state, 
                        country,
                        cp, 
                        phone
                        ):#{{{#

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        clientsocket.settimeout(10)
        clientsocket.connect((ipAddress , port))
        clientsocket.send( (ADD_CUSTOMER_COMMAND 
                          + businessName.rjust(100)[:100]
                          + rfc.rjust(15)[:15] 
                          + status.rjust(1)[:1]  
                          + mail.ljust(50)[:50] 
                          + accountBank.ljust(10)[:10] 
                          + bank.ljust(30)[:30] 
                          + street.ljust(100)[:100] 
                          + externalNumber.ljust(50)[:50]
                          + internalNumber.ljust(25)[:25]
                          + colony.ljust(50)[:50] 
                          + location.ljust(50)[:50] 
                          + reference.ljust(50)[:50] 
                          + town.ljust(50)[:50] 
                          + state.ljust(31)[:31] 
                          + cp.ljust(5)[:5] 
                          + phone.ljust(50)[:50] )
                          )
        time.sleep(1)

        while True:
            try:
                msg = clientsocket.recv(4096)
            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    sleep(1)
                    continue
                else:
                    msg=err
                    break
            else:
                break

        clientsocket.close()
    except socket.error as msg:
        return 'No se pudo conectar a servidor <' + str(msg) + '>'


    if "AddCustomerOK" in msg:
        return msg
    else:
        return "ERROR :" + str(msg)
#}}}#

@python_2_unicode_compatible 
class GLCustomer(models.Model):#{{{#
   vCustomerId       = models.AutoField(primary_key=True)
   vStationId        = models.ForeignKey('GLStation',on_delete=models.SET_NULL,db_column="vStationId1",null=True, blank=False, default="", verbose_name="Estacion")

   vBusinessName     = models.CharField(max_length=100, null=True,default=None, verbose_name="Razón Social")
   vCommercialName   = models.CharField(max_length=100, blank=False,null=False,default=None, verbose_name="Nombre Comercial")
   vRFC              = models.CharField(max_length=20, null=False, verbose_name="RFC")
   vCreationDate     = models.DateTimeField(default=datetime.datetime.now())
   vStatus           = models.BooleanField(default=True, verbose_name="¿Activo?")
   vKind             = models.CharField(max_length=11, choices=CUSTOMER_KIND_GL, default='CONTADO', verbose_name="Tipo")
   vMail             = models.CharField(max_length=100,  null=False,blank=False,verbose_name="Correo")
   vAccountBank      = models.CharField(max_length=100, blank=True,null=True,default=None, verbose_name="No. de Cuenta")
   vBank             = models.CharField(max_length=100, blank=True,null=True,default=None, verbose_name="Banco")
   vStreet           = models.CharField(max_length=255, null=False, blank=False, default=None,verbose_name="Calle")
   vExternalNumber   = models.CharField(max_length=255, null=False, blank=False, default=None,verbose_name="Número Exterior")
   vInternalNumber   = models.CharField(max_length=255,  null=False, blank=False, default=None,verbose_name="Número Interior")
   vColony           = models.CharField(max_length=100,  null=False, blank=False, default=None,verbose_name="Colonia")
   vLocation         = models.CharField(max_length=200, null=False, blank=False, default=None,verbose_name="Localidad")
   vReference        = models.CharField(max_length=255, null=False, blank=False, default=None,verbose_name="Referencia")
   vTown             = models.CharField(max_length=200, null=False, blank=False, default=None,verbose_name="Municipio")
   vState            = models.CharField(max_length=31,  choices=CUSTOMER_STATES, default='AGUASCALIENTES', verbose_name="Estado")
   vCountry          = models.CharField(max_length=6,   choices=CUSTOMER_COUNTRY, default='MEXICO', verbose_name="País")
   vCP               = models.CharField(max_length=6,   null=False, blank=False,default=None ,verbose_name="Codigo Postal")
   vPhone            = models.CharField(max_length=50,  null=True, blank=True, verbose_name="Telefono")
   vSendQR           = models.BooleanField(default=False,null=False, blank=False, verbose_name="¿Enviar QR a correo?")

   def remove_accents(self,input_str):
   #nfkd_form = strdata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'xmlcharrefreplace')
    return only_ascii

   def sendMail(self,subject, mail, body):

      logger.info('Sending  mail to ' +  str(mail))

      email = GLEmail()
      response = email.send(
         subject,
         mail,
         body,
         "")
      logger.info( 'Mail response:'  + str(response))
      return response

   class Meta:
      verbose_name= 'Cliente'
      verbose_name_plural = "Clientes"

   def __str__(self):
      return self.vBusinessName 

   def clean(self, *args, **kwargs):

      status=0
      if self.vStatus:
         status =1

      if not self.vBusinessName or not self.vCommercialName or not self.vRFC or not self.vStreet or not self.vExternalNumber or not self.vColony or not self.vTown or not self.vStatus or not self.vCountry or not self.vCP:
            raise ValidationError({NON_FIELD_ERRORS: [
                     'Todos los campos en negritas son obligatorios',],})


      allStations = GLStation.objects.filter(vBilling=True)
      maxTries=3
      for currentStation in allStations:
         for currentTry in range(maxTries):
            logger.info('Replicating into station: ' +  str(currentStation) + ' with current try:' + str(currentTry))


            response = sendAddCustomer(currentStation.vStationWHost, 
                                        int(currentStation.vStationWPort),
                                        self.remove_accents(str(self.vBusinessName)), 
                                        self.remove_accents(str(self.vCommercialName)), 
                                        str(self.vRFC), 
                                        str(status),
                                        str(self.vMail),
                                        str(self.vAccountBank), 
                                        str(self.vBank), 
                                        self.remove_accents(str(self.vStreet)), 
                                        self.remove_accents(str(self.vExternalNumber)),
                                        self.remove_accents(str(self.vInternalNumber)), 
                                        self.remove_accents(str(self.vColony)), 
                                        self.remove_accents(str(self.vLocation)), 
                                        self.remove_accents(str(self.vReference)),
                                        self.remove_accents(str(self.vTown)), 
                                        str(self.vState), 
                                        self.remove_accents(str(self.vCountry)), 
                                        str(self.vCP),
                                        str(self.vPhone)
                                        )
            logger.info('App response: ' + str(response))

            try:
               if not "AddCustomerOK" in response:
                  logger.error('(0)FATAL : Error replicating on  station: ' +  str(currentStation) + ' and Customer : ' +  str(self.vRFC)+ ' trying again')
               else:
                  logger.info('Customer was saved succesfully at try :' + str(currentTry))
                  break
            except:
               logger.error('(1)FATAL : Error replicating on  station: ' +  str(currentStation) + ' and Customer : ' +  str(self.vRFC)+ ' trying again')

         if not "AddCustomerOK" in response:
            self.sendMail('ERROR REPLICANDO CLIENTE','lalberto.ralbino@gmail.com',"Estacion : "+ str(currentStation) + ', RFC: ' +  str(self.vRFC))
            self.sendMail('ERROR REPLICANDO CLIENTE','villaro70@hotmail.com',"Estacion : "+ str(currentStation) + ', RFC: ' +  str(self.vRFC))
            logger.error('(3)FATAL : Error replicating on  station: ' +  str(currentStation) + ' and Customer : ' +  str(self.vRFC)+ ' no more tries')
         else:
            logger.info('Customer was saved succesfully on station' + str(currentStation))


      if self.vSendQR:
         logger.info('Sending QR to mail')

         qrFileName = "QR_" + str(self.vBusinessName) 
         logger.info("Generating pdf file : " + str(qrFileName) + '.pdf' )

         currentTicket = glPdf.glQRCustomer.GLQRCustomer('glPdf/' + str(qrFileName) + '.pdf')

         qrcodes = qrcode.QRCode(
                     version=1,
                     error_correction=qrcode.constants.ERROR_CORRECT_L,
                     box_size=10,
                     border=4,
                  )
         qrcodes.add_data(self.vRFC) 
         qrcodes.make(fit=True)

         imagec = qrcodes.make_image()
         imagec.save('glQr/' + self.vRFC + '.jpg')
         currentTicket.setImage( 'glQr/' + self.vRFC + '.jpg')
         currentTicket.setBusinessName(self.vBusinessName)

         currentTicket.generateTicket()

         if self.vMail:
            email = GLEmail()
            response = email.send(
               "Codigo Qr para Facturar ",
               self.vMail,
               "Estimado cliente, le enviamos su codigo QR con el cual podra facturar sus ventas en nuestras estaciones de servicio",
               os.path.dirname(os.path.abspath(__file__)) + "/../glPdf/" + qrFileName + ".pdf")
            logger.info( 'Mail has been sent to customer mail:'  + str(response))



   def full_clean(self, *args, **kwargs):
      return self.clean(*args, **kwargs)

   def save(self, *args, **kwargs):
      self.full_clean()
      super(GLCustomer, self).save(*args, **kwargs)

#}}}#

@python_2_unicode_compatible 
class GLAudit(models.Model):#{{{#
   vAuditId            = models.AutoField(primary_key=True)
   vAuditUser          = models.ForeignKey('GLUser',on_delete=models.SET_NULL,db_column='vUserId',null=True, verbose_name="Usuario")
   vAuditAction        = models.CharField(max_length=50, null=False, blank=False, verbose_name="Accion")
   vAuditDescription   = models.CharField(max_length=200, null=False, blank=False, verbose_name="Descripcion")
   vAuditDate          = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
   class Meta:
      verbose_name= 'Auditoria'
      verbose_name_plural = "Auditorias"
   def __str__(self):
      return str(self.vAuditDescription)
   #}}}#

class GLShift(models.Model):#{{{#
   vShiftId    = models.AutoField(blank=False, null=False,primary_key=True ,verbose_name="Id")
   vShift      = models.CharField(blank=False, null=False,unique=False, default="",max_length=10, verbose_name="Turno")
   vStationId  = models.ForeignKey('GLStation',on_delete=models.SET_NULL,db_column="vStationId",null=True, blank=False, default="", verbose_name="Estacion")

   class Meta:
      verbose_name= 'Turno'
      verbose_name_plural = "Turnos"
   def __str__(self):
      return str(self.vShift)
#}}}#

class GLPartialDelivery(models.Model):#{{{#
   vPartialDeliveryId = models.AutoField(primary_key=True)
   vUserId            = models.ForeignKey('GLUser',on_delete=models.SET_NULL,null=True,db_column='vUserId', verbose_name="Despachador")
   vDate              = models.DateTimeField(default=datetime.datetime.now(), verbose_name="Fecha")
   vShiftId           = models.ForeignKey('GLShift',on_delete=models.SET_NULL,null=True,db_column='vShiftId', verbose_name="Turno")
   vCashAmount        = models.CharField(max_length=10, verbose_name="Total Efectivo")
   vVoucherAmountC    = models.CharField(max_length=10, verbose_name="Total Tarjeta Crédito")
   vVoucherAmountD    = models.CharField(max_length=10, verbose_name="Total Tarjeta Débito")
   vOthersAmount      = models.CharField(max_length=10, default="",verbose_name="Total Otros")
   vOthersDesc        = models.CharField(max_length=70, default="",verbose_name="Desc Otros")
   vIsland            = models.IntegerField(default=1, verbose_name="Isla")
   

   class Meta:
      verbose_name= 'Entrega'
      verbose_name_plural = "Entregas"
   def __str__(self):
      return str(self.vUserId) + '-' + str(self.vShiftId) + '-' + str(self.vPartialDeliveryId) + '-' + str(self.vCashAmount)
#}}}#

class GLUserFunction(models.Model):#{{{#
   vUserFunctionId    = models.AutoField(primary_key=True)
   vFunctionsId       = models.ForeignKey('GLFunctions'  ,db_column="vFunctionsId"  , default=None , verbose_name="Funcion")
   vUserId            = models.ForeignKey('GLUser',blank=True, null=True, verbose_name="Usuario")
   #}}}#

class GLSubfunctions(models.Model):#{{{#
   vSubfunctionsId     = models.AutoField(primary_key=True)
   vSubfunctionName    = models.CharField(max_length=50, null=False,blank=False, verbose_name="Nombre de la función")
   vSubfunctionDesc    = models.CharField(max_length=100, null=True,blank=True,verbose_name="Descripción de la función")
   class Meta:
      verbose_name= 'Subfuncion'
      verbose_name_plural = "Subfunciones"
   def __str__(self):
      return str(self.vSubfunctionName) 
#}}}#

class GLFunctions(models.Model):#{{{#
   vFunctionsId     = models.AutoField(primary_key=True)
   vFunctionName    = models.CharField(max_length=50, null=False,blank=False, verbose_name="Nombre de la función")
   vFunctionDesc    = models.CharField(max_length=100, null=True,blank=True,verbose_name="Descripción de la función")
   vOrder           = models.IntegerField(default=0,verbose_name="Orden")
   class Meta:
      verbose_name= 'Funcion'
      verbose_name_plural = "Funciones"
   def __str__(self):
      return str(self.vFunctionName) 
#}}}#
