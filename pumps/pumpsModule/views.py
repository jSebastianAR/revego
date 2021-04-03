# coding=utf-8

from django.shortcuts import render
from django.core.cache import cache
import socket
import json
from glPdf.glSendQR import GLSendQR
from glFTP.VoissFTPPutFiles import VoissFTPPutFiles
import logging
from django.db import connection
from django.db.models import Q
from django.conf import settings
from glEmail.src.glemail import GLEmail

from datetime import datetime, timedelta
from glXls.VoissExportCustomers import VoissExportCustomers 
from time import mktime
import time
import datetime
import sys
import errno
import unidecode
import unicodedata
from django.contrib.auth.models import User
from pumpsModule.models import GLUser
from pumpsModule.models import GLShift
from pumpsModule.models import GLPartialDelivery
from pumpsModule.models import GLStationGroup
from pumpsModule.models import GLStation
from pumpsModule.models import GLCustomer
from pumpsModule.models import GLWebCommand
from pumpsModule.models import GLDevice
from pumpsModule.models import GLFunctions
from pumpsModule.models import GLUserFunction
from django.contrib.admin.models import LogEntry
from django.http import HttpResponse
import simplejson
import uuid
from pumpsModule.VoissReports import GLReportsEngine
import re
from pumpsModule.error_codes_fleets import DICT_ERRORS_FLEETS
from pumpsModule import threads
import binascii
import pickle

logger = logging.getLogger(__name__)
VERSION =  "1.0.43"
currentTransaction=1
TICKET_COMMAND  = "01"
TICKET_DELIVERY_COMMAND  = "43"
INVENTORY_COMMAND  = "11"
BILLING_COMMAND = "02"
PRESET_COMMAND  = "03"
CANCEL_COMMAND  = "04"
SHIFT_COMMAND  = "41"
TICKET_BILLING_COMMAND  = "44"

BILLING_WEB_COMMAND = "60"
GET_PRICES_COMMAND = "61"

CODE_QUERY = "27"
CODE_INSERT = "28"
KIND_TICKET_COMMAND = "29"

REPORTS_DIR = 'reports/'
STATIC_DATA = "00105Tiket 0000000009478 1000^0100COMPUMAR DEMO^0100 Pemex ES 5189^0000R.F.C. VIEE7001301U3^0000PERMISO CRE: PL/22638/EXP/ES/2019^0   SERVICIO SUGASTI XALAPA^0000 00106Tiket 0000000009478 1000^0000*************************************^0100  CONTADO ORIGINAL^0000*************************************^0000 00106Tiket 0000000009478 1000^0000     Cliente:  Publico en General^0000 Fecha Venta: 2020/07/30 19:33:32^0000 Fecha Impre: 2020/07/30 19:33:38^0000       Turno: 2020072201^0000 00106Tiket 0000000009478 1000^0101Transaccion^01013015^0000^0000       Venta: 9478^0000      Web Id: t00100000301502^0000        Isla: 1^0000       Bomba: 1^0000    Manguera: 1 00106Tiket 0000000009478 1000^0000    Forma Pago: ^0000^0000Producto  Cantidad Precio  Total ^0000-----------------------------------^0000Magna  0.815    81.40    14.80^0000 00106Tiket 0000000009478 1000^0000    Subtotal: 12.77^0000         IVA: 2.03^0000       Total: 14.80^0000^0000CATORCE PESOS CON 80/100 M.N. 00106Tiket 0000000009478 1000^0000-----------------------------------^BARQ0518902t0010000030150200014.8202007301933^0   ESTE TICKET ES FACTURABLE SOLO^0   EL DIA DE SU CONSUMO 00107Tiket 0000000009478 1000^0   FACTURACION EN LINEA:^0   gl-operacion.com.mx"


#Common

def commonGetCustomers(station, userRFC):#{{{#

   customersDict=[]
   try:
      if userRFC:
            allCustomers= GLCustomer.objects.filter(vRFC=userRFC)
      else:
         if station:
            currentStation= GLStation.objects.get(vStationDesc= station)
            allCustomers= GLCustomer.objects.filter(vStationId=currentStation).order_by('vCustomerId')
         else:
            allCustomers= GLCustomer.objects.all().order_by('vCustomerId')

      for currentCustomer in allCustomers:
         currentObject = {}
         currentObject['Id']= str(currentCustomer.vCustomerId)

         currentObject['StationId']= str(currentCustomer.vStationId.vStationDesc)
         currentObject['BusinessName']= str(currentCustomer.vBusinessName)
         currentObject['CommercialName']= str(currentCustomer.vCommercialName)
         currentObject['RFC']= str(currentCustomer.vRFC)
         currentObject['CreationDate']= str(currentCustomer.vCreationDate.strftime('%d/%m/%Y %H:%M:%S'))
         currentObject['Status']= str(currentCustomer.vStatus)
         currentObject['Kind']= str(currentCustomer.vKind)
         currentObject['Mail']= str(currentCustomer.vMail)
         currentObject['AccountBank']= str(currentCustomer.vAccountBank)
         currentObject['Bank']= str(currentCustomer.vBank)
         currentObject['Street']= str(currentCustomer.vStreet)
         currentObject['ExternalNumber']= str(currentCustomer.vExternalNumber)
         currentObject['InternalNumber']= str(currentCustomer.vInternalNumber)
         currentObject['Colony']= str(currentCustomer.vColony)
         currentObject['Location']= str(currentCustomer.vLocation)
         currentObject['Reference']= str(currentCustomer.vReference)
         currentObject['Town']= str(currentCustomer.vTown)
         currentObject['State']= str(currentCustomer.vState)
         currentObject['Country']= str(currentCustomer.vCountry)
         currentObject['CP']= str(currentCustomer.vCP)
         currentObject['Phone']= str(currentCustomer.vPhone)

         customersDict.append(currentObject)
   except GLCustomer.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' No customers configured yet')
   except GLStation.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' No station configured yet')

   return customersDict

   #}}}#

def commonGetGroups(groupDesc):#{{{#

   groupsDict=[]
   try:
      if groupDesc:
         allGroups= GLStationGroup.objects.get(vStationName=groupDesc)
      else:
         allGroups= GLStationGroup.objects.all().order_by('vStationGroupId')

      for currentGroup in allGroups:
         currentObject = {}
         currentObject['Id']= str(currentGroup.vStationGroupId)
         currentObject['Name']= currentGroup.vStationName
         currentObject['Desc']= currentGroup.vStationGroupDesc
         groupsDict.append(currentObject)
   except GLStationGroup.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' No groups configured yet')

   return groupsDict

   #}}}#
   
def commonGetTransactions(user):#{{{#

   transactionsDict=[]
   #try:
   #   allTransactions= GLTr.objects.get(vStationName=groupDesc)
#
#      for currentGroup in allTransactions:
#         currentObject = {}
#         currentObject['Id']= str(currentGroup.vStationGroupId)
#         currentObject['Name']= currentGroup.vStationName
#         currentObject['Desc']= currentGroup.vStationGroupDesc
#         transactionsDict.append(currentObject)
#   except GLStationGroup.DoesNotExist:
#      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' No groups configured yet')

#   return transactionsDict

   #}}}#

def getValueStation(currentStation):
   currentObject = {}
   currentObject['Id']                = str(currentStation.vStationId)
   currentObject['StationDesc']       = str(currentStation.vStationDesc)
   if currentStation.vStationGroupId is not None:
      currentObject['StationGroupId']    = str(currentStation.vStationGroupId.vStationGroupId)
      currentObject['StationGroupDesc']    = str(currentStation.vStationGroupId.vStationGroupDesc)
   else:
      currentObject['StationGroupId']    = 'None'
      currentObject['StationGroupDesc']    = 'None'

   currentObject['StationWHost']      = str(currentStation.vStationWHost)
   currentObject['StationLHost']      = str(currentStation.vStationLHost)
   currentObject['StationWPort']      = str(currentStation.vStationWPort)
   currentObject['StationLPort']      = str(currentStation.vStationLPort)
   currentObject['RequireDispatcher'] = str(currentStation.vRequireDispatcher)
   currentObject['RequireDriver']     = str(currentStation.vRequireDriver)
   currentObject['RequireAuth']       = str(currentStation.vRequireAuth)
   currentObject['UseFleets']        = str(currentStation.vUseFleets)
   currentObject['UsePoints']        = str(currentStation.vUsePoints)
   currentObject['UseTAE']           = str(currentStation.vUseTAE)

   return currentObject

def commonGetStations(stationDesc):#{{{#

   stationsDict=[]
   try:
      if stationDesc:
         allStations= GLStation.objects.get(vStationDesc=stationDesc)
         stationsDict.append(getValueStation(allStations))
      else:
         allStations= GLStation.objects.all().order_by('vStationId')
         for currentStation in allStations:
            stationsDict.append(getValueStation(currentStation))

   except GLStation.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' No stations configured yet')

   return stationsDict

   #}}}#

def commonGetUsers(stationDesc, userAccess,rfc):#{{{#

   usersDict=[]
   try:
      if len(stationDesc)>0:
         currentStation= GLStation.objects.get(vStationDesc=stationDesc)
         if userAccess:
            allUsers= GLUser.objects.filter( vKind="CONDUCTOR",vStationId=currentStation,vUserAccess__iexact=userAccess )
         else:
            if rfc and not 'undefined' in rfc:
               allUsers= GLUser.objects.filter( vKind="CONDUCTOR",vStationId=currentStation, vRFC=rfc).order_by('vUserId')
            else:
               allUsers= GLUser.objects.filter( vStationId=currentStation).order_by('vName')
      else:
         allUsers= GLUser.objects.all(vKind="CONDUCTOR").order_by('vUserId')


      for currentUser in allUsers:
         currentObject = {}
         currentObject['Id']             = str(currentUser.vUserId)
         currentObject['StationId']      = str(currentUser.vStationId.vStationDesc)
         currentObject['Active']         = str(currentUser.vActive)
         currentObject['Kind']           = str(currentUser.vKind)
         currentObject['Name']           = str(currentUser.vName)
         currentObject['Lastname']       = str(currentUser.vLastname)
         if currentUser.vAge:
            currentObject['Age']            = str(currentUser.vAge)
         else:
            currentObject['Age']            = "0"
         currentObject['Mail']           = str(currentUser.vMail)
         currentObject['Phone']          = str(currentUser.vPhone)
         currentObject['MobilePhone']    = str(currentUser.vMobilePhone)
         currentObject['UserAccess']     = str(currentUser.vUserAccess)
         currentObject['PassAccess']     = str(currentUser.vPassAccess)
         currentObject['IsAdmin']     = str(currentUser.vIsAdmin)
         usersDict.append(currentObject)
   except GLUser.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' No users configured yet')
   except GLStation.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' No station found')

   return usersDict

   #}}}#

def commonDevices(userId,deviceName):#{{{#

   devicesDict=[]
   try:
      if len(userId)>0:
         currentUser= GLUser.objects.get(vUserId=userId)
         allDevices= GLDevice.objects.filter(vUserId=currentUser).order_by('vDeviceId')
      else:
         if deviceName:
            allDevices= GLDevice.objects.get(vDeviceName=deviceName)
         else:
            allDevices= GLDevice.objects.all().order_by('vDeviceId')

      for currentDevice in allDevices:
         currentObject = {}
         currentObject['Id']           = str(currentDevice.vDeviceId)
         currentObject['UserId']       = str(currentDevice.vUserId)
         currentObject['DeviceId']     = str(currentDevice.vDeviceName)
         currentObject['UserAgent']    = str(currentDevice.vUserAgent)
         currentObject['OldUserAgent'] = str(currentDevice.vOldUserAgent)
         currentObject['IPAddress']    = str(currentDevice.vIPAddress)
         currentObject['DeviceToken']  = str(currentDevice.vDeviceToken)
         currentObject['IsActive']     = str(currentDevice.vIsActive)
         currentObject['PrintTicket']  = str(currentDevice.vPrintTicket)

         devicesDict.append(currentObject)
   except GLUser.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' No user found')
   except GLDevice.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' No devices configured yet')

   return devicesDict

   #}}}#



#Internal methods


def json_response(func):#{{{#
    """
    A decorator thats takes a view response and turns it
    into json. If a callback is added through GET or POST
    the response is JSONP.
    """
    def decorator(request, *args, **kwargs):
        objects = func(request, *args, **kwargs)
        if isinstance(objects, HttpResponse):
            return objects
        try:
            data = simplejson.dumps(objects)
            if 'callback' in request.REQUEST:
                # a jsonp response!
                data = '%s(%s);' % (request.REQUEST['callback'], data)
                return HttpResponse(data, "text/javascript")
        except:
            data = simplejson.dumps(str(objects))
        return HttpResponse(data, "application/json")
            
    return decorator
#}}}#

def logTiket(currentTransaction,error, token, user, station,pump,saleId):#{{{#
   try:
      currentUser = User.objects.get(username='REQUEST_SERVICE')

      newLog = LogEntry(
                  user=currentUser,
                  object_repr=str('Ticket[ ' + str(error) + 
                                 ' ] , Estacion[ ' + str(station) + 
                                 ' ] , Usuario[ ' + str(user) + 
                                 ' ] , Bomba[' + str(pump) +
                                 ' ] , Venta[' + str(saleId) + ']' 
                                 )[0:200],
                  action_flag=2)

      newLog.save()
   except User.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+'Trying to log into database but the user REQUEST_SERVICE does not exist, please create it through the admin site]')
   #}}}#

def logBilling(currentTransaction,error, token, user, station,pump,rfc, billingId):#{{{#
   try:
      currentUser = User.objects.get(username='REQUEST_SERVICE')

      newLog = LogEntry(
                  user=currentUser,
                  object_repr=str('Factura[ ' + str(error) + 
                                 ' ] , Estacion[ ' + str(station) + 
                                 ' ] , Usuario[ ' + str(user) + 
                                 ' ] , Bomba[' + str(pump) + 
                                 ' ] , Cliente[' + str(rfc) +
                                 ' ] , Id Factura[' + str(billingId) + ']' 
                                 )[0:200],
                  action_flag=2)

      newLog.save()
   except User.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+'Trying to log into database but the user REQUEST_SERVICE does not exist, please create it through the admin site]')
   #}}}#

def logLogin(currentTransaction,error, token, user, password,stationId):#{{{#
   try:
      currentUser = User.objects.get(username='REQUEST_SERVICE')

      newLog = LogEntry(
                  user=currentUser,
                  object_repr=str('Error[ ' + str(error) + 
                                 ' ] , Station[ ' + str(stationId) + 
                                 ' ] , token[ ' + str(token) + 
                                 ' ] , user[ ' + str(user) + 
                                 ' ] , pass[ ' + str(password) + 
                                 ' ]'   )[0:200],
                  action_flag=10)

      newLog.save()
   except User.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+'Trying to log into database but the user REQUEST_SERVICE does not exist, please create it through the admin site]')
   #}}}#

@json_response
def generateCustomers(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START generateCustomers')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GenerateCustomers ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   createObj = VoissExportCustomers()
   createObj.setFileName("ClientesGero.xlsx")
   createObj.createCustomers()
      
   resultJSON['GenerateCustomers'] = 'OK'


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END generateCustomers')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def getShiftsAndDispatchers(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getShiftsAndDispatchers')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GetShiftsAndDispatchers ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetShiftsAndDispatchers'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetShiftsAndDispatchers'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   allShifts = GLShift.objects.filter(vStationId=localStationId).order_by("-vShiftId")
   shiftsDict=[]
   for currentShift in allShifts:
      currentObject = {}
      currentObject['Id']     = str(currentShift.vShiftId)
      currentObject['Shift']  = str(currentShift.vShift)

      shiftsDict.append(currentObject)

   usersDict=[]
   try:
      allUsers= GLUser.objects.filter(vKind="DESPACHADOR").order_by('vName')
      for currentUser in allUsers:
         currentObject = {}
         currentObject['Id']             = str(currentUser.vUserId)
         currentObject['StationId']      = str(currentUser.vStationId.vStationDesc)
         currentObject['Name']           = str(currentUser.vName) + ' ' + str(currentUser.vLastname)
         usersDict.append(currentObject)
   except GLUser.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' No users configured yet')
   except GLStation.DoesNotExist:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' No station found')
      

   resultJSON['Shifts']= shiftsDict
   resultJSON['Dispatchers']= usersDict
   resultJSON['GetShiftsAndDispatchers'] = 'OK'


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getShiftsAndDispatchers')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def getDeliveryReport(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getDeliveryReport')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GetDeliveryReport ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('shift') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'SHIFT           : [' + request.GET['shift']+ ']')

   if request.GET.get('dispatcher') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DISPATCHER      : [' + request.GET['dispatcher']+ ']')

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetDeliveryReport'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetDeliveryReport'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   currentShift = GLShift.objects.get(vShift=request.GET['shift'])

   if not "TODOS" in request.GET['dispatcher']:
      currentDispatcher = GLUser.objects.get(vUserId= request.GET['dispatcher'])
      allDeliveries = GLPartialDelivery.objects.filter(vShiftId=currentShift, vUserId=currentDispatcher).order_by("vPartialDeliveryId")
      deliveriesDict=[]

      for currentDelivery in allDeliveries:
         currentObject = {}
         currentObject['Id']     = str(currentDelivery.vPartialDeliveryId)
         currentObject['DateR']  = str(currentDelivery.vDate.strftime('%d/%m/%Y %H:%M:%S'))
         currentObject['Island'] = str(currentDelivery.vIsland)
         currentObject['Cash']   = str(currentDelivery.vCashAmount)
         currentObject['Credit'] = str(currentDelivery.vVoucherAmountC)
         currentObject['Debit']  = str(currentDelivery.vVoucherAmountD)
         currentObject['Others']  = str(currentDelivery.vOthersAmount)
         currentObject['OthersDesc']  = str(currentDelivery.vOthersDesc)

         deliveriesDict.append(currentObject)

      resultJSON['Deliveries']= deliveriesDict
      resultJSON['GetDeliveryReport'] = 'OK'

   else:
      
      customQuery=""
      try:
           
         customQuery+=' '

         customQuery+='select "vIsland" "island", '
         customQuery+='       SUM(cast(CASE WHEN "vCashAmount" = \'\' THEN \'0\' ELSE "vCashAmount" END as float)) "totalCash", '
         customQuery+='       SUM(cast(CASE WHEN "vVoucherAmountC" = \'\' THEN \'0\' ELSE "vVoucherAmountC" END as float)) "totalCredit", '
         customQuery+='       SUM(cast(CASE WHEN "vVoucherAmountD" = \'\' THEN \'0\' ELSE "vVoucherAmountD" END as float)) "totalDebit", '
         customQuery+='       SUM(cast(CASE WHEN "vOthersAmount" = \'\' THEN \'0\' ELSE "vOthersAmount" END as float)) "totalOthers", '
         customQuery+='       "use"."vName" || \' \' || "use"."vLastname" "dispatcher" '
         customQuery+='from "pumpsModule_glpartialdelivery" as pde '
         customQuery+='join "pumpsModule_glshift" as gls '
         customQuery+='   on "pde"."vShiftId"="gls"."vShiftId"  '
         customQuery+='join "pumpsModule_gluser" use '
         customQuery+='   on "use"."vUserId"="pde"."vUserId"  '
         customQuery+='where "gls"."vShift"=\'' + request.GET['shift'] + '\' '
         customQuery+='group by "vIsland", '
         customQuery+='         "use"."vName", '
         customQuery+='         "use"."vLastname" '
         customQuery+='order by "vIsland";'


         cursor = connection.cursor()
         cursor.execute(customQuery)


         recordsDict=[]
         for currentRow in cursor.fetchall():
            currentObject = {}
            currentObject['Island']     = currentRow[0]
            currentObject['Cash']       = currentRow[1]
            currentObject['Credit']     = currentRow[2]
            currentObject['Debit']      = currentRow[3]
            currentObject['Others']     = currentRow[4]
            currentObject['Dispatcher'] = currentRow[5]

            recordsDict.append(currentObject)

         
         resultJSON['Records'] =recordsDict
         resultJSON['GetDeliveryReport'] = 'OK'
      except Exception as e:
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+'Error executing the query ' +  customQuery)


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getDeliveryReport')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def downloadReport(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START downloadReport')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New DownloadReport ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')


   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')


   if not request.GET.get('currentStation') is None:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')
   else:
      return resultJSON

   if not request.GET.get('shift') is None:
      logger.info('LOG_ID<' + currentTransaction + '> '+'SHIFT           : [' + request.GET['shift']+ ']')
   else:
      return resultJSON

   if not request.GET.get('userId') is None:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER ID         : [' + request.GET['userId']+ ']')
   else:
      return resultJSON



   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetReport'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetReport'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Generating report : ')

   resultJSON['DownloadReport'] = 'OK'
   serverPath = "http://" + request.META['HTTP_HOST'] + settings.STATIC_URL + REPORTS_DIR

   reports = GLReportsEngine()

   if 'TODOS'  in request.GET['userId']:
      reportId='1'
   else:
      reportId='2'

   fileNameReport = reports.getReportAsPdf(reportId,request)

   filePath =  serverPath + fileNameReport

   resultJSON['URL']       = filePath

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END downloadReport')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON

#}}}#

@json_response
def registerDevice(request):#{{{#

   resultJSON = {}
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'START registerDevice')
   logger.info('LOG_ID<' + currentTransaction + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New Register device Request ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT :' + request.META['HTTP_USER_AGENT'])
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING :' + request.META['QUERY_STRING'] )
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD :' + request.method)
   logger.info('LOG_ID<' + currentTransaction + '> '+'REMOTE_ADDR :'+ request.META['REMOTE_ADDR'])
   logger.info('LOG_ID<' + currentTransaction + '> '+'CSRF_COOKIE:' + request.META['CSRF_COOKIE'] )

   logger.info('LOG_ID<' + currentTransaction + '> '+'USER :' + request.GET['lsUser'])
   logger.info('LOG_ID<' + currentTransaction + '> '+'PASS :' + request.GET['lsPass'])
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT :'  + request.META['HTTP_USER_AGENT'])

   if request.GET.get('hash') is None:
      logger.info('LOG_ID<' + currentTransaction + '> '+'HASH            : NOT_SENT')
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'HASH            : [' + request.GET['hash']+ ']')

   try:
      user = GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'],vPassAccess=request.GET['lsPass'])
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER AUTENTICATED SUCCESFULLY, CREATING NEW DEVICE')
      logger.info('LOG_ID<' + currentTransaction + '> '+'Login Ok, with user : ' + user.vUserAccess )
      resultJSON['Login']  = 'GOOD_USER'
      resultJSON['Device']  = request.GET['DEVICE_NAME']
      resultJSON['Activation'] = "GOOD_ACTIVATION"
      resultJSON['UserName']  = user.vUserAccess.lower()

      try:
         device  = GLDevice.objects.get(vUserAgent=request.META['HTTP_USER_AGENT'], vDeviceName=request.GET['DEVICE_NAME'])
         logger.info('LOG_ID<' + currentTransaction + '> '+"THE DEVICE IS ALREADY ON THE SYSTEM")
         if device.vIsActive:
            resultJSON['ReadyToActivate'] = "NO"
            resultJSON['SERVICE_MESSAGE']  = 'El dispositivo ' + request.GET['DEVICE_NAME'] + ' ya existe en el sistema, porfavor cambie el nombre del dispositivo'
            resultJSON['TOKEN_DEVICE']= device.vDeviceToken
            logger.info('LOG_ID<' + currentTransaction + '> '+"THIS DEVICE IS ALREADY ACTIVATED")
         else:
            logger.info('LOG_ID<' + currentTransaction + '> '+' THIS DEVICE IS ALREADY ACTIVATED')
            resultJSON['ReadyToActivate'] = "YES"
               

      except GLDevice.DoesNotExist:
         
         try:
            device = GLDevice.objects.get(vUserId=user, vDeviceName=request.GET['DEVICE_NAME'])
            logger.info('LOG_ID<' + currentTransaction + '> '+"THE DEVICE " + device.vDeviceName + ' EXISTS WITH THE SAME USER ON DIFFERENT PHYSICAL DEVICE, PLEASE CHANGE THE NAME OF THE NEW DEVICE')
            resultJSON['ReadyToActivate'] = "NO"
            resultJSON['SERVICE_MESSAGE']  = 'YA EXISTE EL NOMBRE DE DISPOSITIVO CON SU USUARIO Y EN DIFERENTE DISPOSITIVO FISICO, ASIGNE OTRO NOMBRE PARA REGISTRAR OTRO DISPOSITIVO CON SU CUENTA'
         except:
      
            logger.info('LOG_ID<' + currentTransaction + '> '+"CREATING NEW DEVICE WITH USER AGENT :" + request.META['HTTP_USER_AGENT'])
            newDevice = GLDevice(vUserId=user, 
                                vDeviceName=request.GET['DEVICE_NAME'], 
                                vUserAgent = request.META['HTTP_USER_AGENT'], 
                                vIPAddress=request.META['REMOTE_ADDR'], 
                                vStationId= user.vStationId,
                                vOldUserAgent= request.GET['hash'],
                                vDeviceToken=uuid.uuid4())
            newDevice.save()
            logger.info('LOG_ID<' + currentTransaction + '> '+"THE DEVICE IS WAITING FOR THE ACTIVATION CODE ...")
            resultJSON['ReadyToActivate'] = "YES"


   except GLUser.DoesNotExist:
      logger.error('LOG_ID<' + currentTransaction + '> '+'BAD AUTHENTICATION')
      resultJSON['Login']  = 'BAD_USER'

   logger.info('LOG_ID<' + currentTransaction + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + currentTransaction + '> '+'END registerDevice')
   logger.info('LOG_ID<' + currentTransaction + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#

@json_response
def activateDevice(request):#{{{#

   resultJSON = {}
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'START activateDevice')
   logger.info('LOG_ID<' + currentTransaction + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New Activate Device Request '+ VERSION )
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT :' + request.META['HTTP_USER_AGENT'])
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING :' + request.META['QUERY_STRING'] )
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD :' + request.method)
   logger.info('LOG_ID<' + currentTransaction + '> '+'REMOTE_ADDR :'+ request.META['REMOTE_ADDR'])
   logger.info('LOG_ID<' + currentTransaction + '> '+'CSRF_COOKIE:' + request.META['CSRF_COOKIE'] )

   logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE:' + request.GET['TOKEN_DEVICE'])

   try:
      device  = GLDevice.objects.get(vUserAgent=request.META['HTTP_USER_AGENT'], vDeviceToken=request.GET['TOKEN_DEVICE'])
      logger.info('LOG_ID<' + currentTransaction + '> '+"THE DEVICE EXISTS ON THE SYSTEM, READY TO BE ACTIVATED")
      user  = device.vUserId
      if device.vIsActive:
         logger.info('LOG_ID<' + currentTransaction + '> '+"                  THE DEVICE IS ALREADY ACTIVATED, CHECKING THE PRINTER CONFIGURATION")

      device.vIsActive = True
      device.save()
      resultJSON['Activation'] = "GOOD_ACTIVATION"
      resultJSON['Station'] = device.vUserId.vStationId.vStationDesc
      logger.info('LOG_ID<' + currentTransaction + '> '+"DEVICE WITH NAME :" + device.vDeviceName + " IS READY TO MAKE  TRANSACTIONS")

      
      try:
         stations =  GLStation.objects.all()
         stationObjects = []
         resultJSON['Stations'] = "NO"
         for station in stations:
            logger.info('LOG_ID<' + currentTransaction + '> '+' CURRENT STATION:' + station.vStationDesc)
            stationObjects.append(station.vStationDesc)
            resultJSON['Stations'] = "YES"
         resultJSON['StationNames'] = stationObjects

      except Station.DoesNotExist:
         logger.info(' THERE ARE NO STATIONS CONFIGURED')
         resultJSON['Stations'] = "NO"

   except GLDevice.DoesNotExist:
      resultJSON['Activation'] = "BAD_ACTIVATION"
      logger.error('LOG_ID<' + currentTransaction + '> '+"THE TOKEN IS WRONG")

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END activateDevice')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#

def askCurrentShiftService(ipAddress, #{{{#
                      port,
                      deviceId):



    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        clientsocket.connect((ipAddress , port))
        clientsocket.send( (SHIFT_COMMAND
                          + deviceId.rjust(36)  
                          + VERSION.rjust(10)).encode())
        #time.sleep(0.1)
        time.sleep(1)

        clientsocket.settimeout(30)
        msg=''
        while True:
            try:
                msg = clientsocket.recv(4096)
                if "ShiftOK" in str(msg):
                    if not "Pumps:" in str(msg):
                        msg1 = clientsocket.recv(4096)
                        msg= msg + msg1
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


    if "ShiftOK" in str(msg):
        return msg
    else:
        return "ERROR :" + str(msg)
#}}}#

def remove_accents(input_str):
   nfkd_form = strdata.normalize('NFKD', input_str)
   only_ascii = nfkd_form.encode('ASCII', 'ignore')
   return only_ascii

def split_gasTypes(gasTypes):
   gas_list_types = gasTypes.split(":")
   gas_list_types.remove('')

   final_list = []
   for type_gas in gas_list_types:
      id_gas   = type_gas.split(':')[0]
      gas_name = type_gas.split(':')[1]
      final_list.append([id_gas,gas_name])

   return final_list

def split_islands(pumpsIsland):

   list_one = pumpsIsland.split('@')
   list_one.remove('')
   #print(list_one)

   dict_islands = {}

   for counter1 in range(0,len(list_one)): #Desde 0 hasta la última posicion de la lista
      
      data = list_one[0].split(':')
      island = data[1] #Obtiene la isla
      
      list_pumps = [] #Lista de bombas para la isla en específico
      index_pair = 0 #Indice en el que se buscara el elemento(generalmente la primer posicion)
      for counter2 in range(0,len(list_one)):
         
         e = list_one[index_pair]#toma el primer elemento
         e_splited = e.split(':')

         
         if e_splited[1]==island: #Si encuentra que pertenece a la isla
            list_pumps.append(e_splited[0])#lo agrega
            #print(f"Pump {e[0]} added to island {island}")
            list_one.remove(e)#lo remueve de la lista
         else:#sino lo encuentra mueve la posicion en donde buscara
            index_pair+=1

      #print(list_one)      
      dict_islands[island] = list_pumps #se agrega el listado de bombas para esa isla
      if len(list_one)==0: #si la lista ya esta vacía
         break;
            
   return dict_islands
   logger.info('LOG_ID<' + currentTransaction + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'Islands Dictionary')
   logger.info('LOG_ID<' + currentTransaction + '> '+ str(dict_islands))
   logger.info('LOG_ID<' + currentTransaction + '> '+'******************************')

def getRealIslands(dict_islands):
   
   NumIslands = len(dict_islands)
   Islands = []
   for numIsland in range(0,NumIslands):
      Islands.append(str(numIsland+1))

   return Islands   

@json_response
def loginUser(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + currentTransaction + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'START loginUser')
   logger.info('LOG_ID<' + currentTransaction + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New Login Request ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['station']+ ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('hash') is None:
      logger.info('LOG_ID<' + currentTransaction + '> '+'HASH            : NOT_SENT')
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'HASH            : [' + request.GET['hash']+ ']')

   
   try:
      station = GLStation.objects.get(vStationDesc = request.GET['station'])
   except GLStation.DoesNotExist:
      logger.error('LOG_ID<' + currentTransaction + '> '+'THE STATION DOES NOT EXIST ON THE SYSTEM')
      resultJSON['Login']  = 'Terminal Pertenece a estacion : ' +  str(request.GET['station'] + ' pero la estacion no existe en el sistema')
      resultJSON['ERROR_MESSAGE']  = 'La estacion:' + str(request.GET['station']) + ' no existe en el sistema'


   device=None

   try:
      if len(request.GET['tokenDevice'])==15:
         logger.info('LOG_ID<' + currentTransaction + '> '+'Device with IMEI ' + str(request.GET['tokenDevice']) + ' found ')
         device= GLDevice.objects.filter(vDeviceToken=request.GET['tokenDevice'])
         if not device:
            user = GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'],vPassAccess=request.GET['lsPass'])
            station =  GLStation.objects.get(vStationDesc=request.GET['station'])
            logger.info('LOG_ID<' + currentTransaction + '> '+'Creating a new Device with UUID:' + str(request.GET['tokenDevice']) )
            newDevice = GLDevice()
            newDevice.vUserId= user
            newDevice.vUserAgent='IMEI'
            newDevice.vIPAddress='0.0.0.0'
            newDevice.vDeviceName= 'TERM-' + str(request.GET['tokenDevice'])
            newDevice.vDeviceToken= request.GET['tokenDevice']
            newDevice.vIsActive=True
            newDevice.save()
            logger.info('LOG_ID<' + currentTransaction + '> '+'Device was successful created with id : ' +  str(newDevice.vDeviceId) )
   except GLUser.DoesNotExist:
      logger.error('LOG_ID<' + currentTransaction + '>'+'BAD AUTHENTICATION')
      resultJSON['Login']  = 'BAD_USER'
      resultJSON['ERROR_MESSAGE']  = '(0)El usuario y/o password son incorrectos'
      logLogin(currentTransaction,"User / Password incorrect", request.GET['tokenDevice'],request.GET['lsUser'], request.GET['lsPass'],request.GET['station'])
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
      return resultJSON

      


   logger.info('LOG_ID<' + currentTransaction + '> '+'********************** Validating device config to reset ... INI')
   device= GLDevice.objects.filter(vDeviceToken=request.GET['tokenDevice'])
   if device:
      device= device[0]
      logger.info('LOG_ID<' + currentTransaction + '> '+'Device Found with name :' +  str(device.vDeviceName))
      if device.vResetStation:
         logger.info('LOG_ID<' + currentTransaction + '> '+'Sending device RESET STATION')
         resultJSON['ResetStation']=True
         device.vResetStation=False
         device.save()
      if device.vResetAuth:
         logger.info('LOG_ID<' + currentTransaction + '> '+'Sending device RESET AUTH')
         resultJSON['ResetAuth']=True
         device.vResetAuth=False
         device.save()
   else:
      #Reset station and authorization when is a new terminal
      resultJSON['ResetAuth']=True
      #Creaates the device register if is an IMEI
      logger.info('LOG_ID<' + currentTransaction + '> '+'********************** The terminal with UUID does not exit on system')

   logger.info('LOG_ID<' + currentTransaction + '> '+'********************** Validating device config to reset ... END')

   #For ReveGas drivers

   if "USER_DEVICE" in request.GET['tokenDevice']:
      try:
         user = GLUser.objects.get(Q(vKind="CONDUCTOR") , vUserAccess__iexact=request.GET['lsUser'],vPassAccess=request.GET['lsPass'])
         resultJSON['Transactions']  = commonGetTransactions(user)
         resultJSON['Login']  = 'GOOD_USER'
         resultJSON['UserName']  = user.vUserAccess.lower()
         resultJSON['User']  = user.vUserAccess
         resultJSON['Password']  = user.vPassAccess
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
         return resultJSON

      except GLUser.DoesNotExist:
         logger.error('LOG_ID<' + currentTransaction + '>'+'BAD AUTHENTICATION')
         resultJSON['Login']  = 'BAD_USER'
         resultJSON['ERROR_MESSAGE']  = '(1)El usuario y/o password son incorrectos'
         logLogin(currentTransaction,"User / Password incorrect", request.GET['tokenDevice'],request.GET['lsUser'], request.GET['lsPass'],request.GET['station'])
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
         return resultJSON

   try:
      try:
         station=None
         if len(request.GET['station'])>0 :
            station =  GLStation.objects.get(vStationDesc=request.GET['station'])
            resultJSON['RequireNIPDispatcher']  = station.vRequireDispatcher
            
            

            userM = GLUser.objects.filter(vUserAccess__iexact=request.GET['lsUser'],vPassAccess=request.GET['lsPass'],vMulti=True )
            
            if userM:
               user= userM[0]
            else:
               user = GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'],vPassAccess=request.GET['lsPass'] ,vStationId__vStationDesc=request.GET['station'])
               logger.info(user)
            

            logger.info('LOG_ID<' + currentTransaction + '> '+'USER FOUND ' +  str(user))


            if user.vKind=="DESPACHADOR":
               resultJSON['IsDispatcher'] = True
            else:
               resultJSON['IsDispatcher'] = False
            resultJSON['IsAdmin'] = bool(user.vIsAdmin)
            resultJSON['IsKiosk'] = bool(user.vIsKiosk)
            if station.vSignDispatchers:
               #TODO get the islands frmo station
               islandsDict = []
               islandsDict.append('1')
               islandsDict.append('2')
               islandsDict.append('3')
               islandsDict.append('4')
               islandsDict.append('5')
               islandsDict.append('6')
               islandsDict.append('7')
               islandsDict.append('8')
               resultJSON['Islands'] = islandsDict
            else:
               islandsDict = []
               resultJSON['Islands'] = islandsDict
         else:
            user = GLUser.objects.get(Q(vKind="WEB") | Q(vKind="DESPACHADOR") | Q(vKind="CONDUCTOR") | Q(vKind="SUPERVISOR") | Q(vKind="OFICINA"), vUserAccess__iexact=request.GET['lsUser'],vPassAccess=request.GET['lsPass'])
            if user.vKind=="DESPACHADOR":
               resultJSON['IsDispatcher'] = True
            elif user.vKind=="CONDUCTOR":
               station = user.vStationId
            else:
               resultJSON['IsDispatcher'] = False

         allStations = []
         if user.vMulti:
            if station:
               if station.vStationGroupId:
                  stationsPerGroup = GLStation.objects.filter(vStationGroupId= station.vStationGroupId)
                  for currentStation in stationsPerGroup:
                     allStations.append(currentStation.vStationDesc)
                     logger.info('LOG_ID<' + currentTransaction + '> '+'Adding    : ' + currentStation.vStationDesc + ' to current Group')
         resultJSON['StationsPerGroup'] = allStations



         if station:
            logger.info('LOG_ID<' + currentTransaction + '> '+'STATION   : [' + str(station.vStationDesc)+ ']')
            if not "TODAS" in station.vStationDesc:
               devices  = GLDevice.objects.filter(vDeviceToken=request.GET['tokenDevice'])
               if devices:
                  device= devices[0]
               else:
                  device=None
            else:
               device  = None
               resultJSON['Transactions']  = commonGetTransactions(user)
         else:
            devices  = GLDevice.objects.filter(vDeviceToken=request.GET['tokenDevice'])
            if not devices:
               logger.info('LOG_ID<' + currentTransaction + '> '+' Device not found by token, searching by hash')
               if not request.GET.get('hash') is None:

                  logger.info('LOG_ID<' + currentTransaction + '> '+' HashD1')
                  user     = GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'],vPassAccess=request.GET['lsPass'])
                  logger.info('LOG_ID<' + currentTransaction + '> '+' User found :' + str(user))
                  devices  = GLDevice.objects.filter(vOldUserAgent=request.GET['hash'] , vStationId=user.vStationId)
                  logger.info('LOG_ID<' + currentTransaction + '> '+' HashD2')
                  
                  if devices:
                     logger.info('LOG_ID<' + currentTransaction + '> '+' Device found by hash')
                     device= devices[0]
                     station= device.vStationId

                     #The user and pass must be part of the station recover by hash

                     
                     userSt = GLUser.objects.filter(vUserAccess__iexact=request.GET['lsUser'],vPassAccess=request.GET['lsPass'],vStationId= station )

                     if not userSt:
                        resultJSON['Login']  = 'BAD_TOKEN'
                        resultJSON['ERROR_MESSAGE']  = '(0)Es necesario dar de alta el dispositivo antes de usar el sistema, por favor delo de alta  <a href="register/index.html"><span id="voissLinkRegister"><b style="color:red"> AQUI </span></b></a>'
                        logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
                        return resultJSON


                     logger.info('LOG_ID<' + currentTransaction + '> '+' HashD3')
                     if station.vSignDispatchers:
                        #TODO get the islands frmo station
                        islandsDict = []
                        islandsDict.append('1')
                        islandsDict.append('2')
                        islandsDict.append('3')
                        islandsDict.append('4')
                        logger.info('LOG_ID<' + currentTransaction + '> '+' HashD4')
                        resultJSON['Islands'] = islandsDict
                        resultJSON['IsAdmin'] = bool(user.vIsAdmin)
                        resultJSON['IsKiosk'] = bool(user.vIsKiosk)
                        resultJSON['LocalIP']  = station.vStationLHost
                        resultJSON['LocalPort']  = station.vStationLPort
                        resultJSON['Station']  = station.vStationDesc
                        resultJSON['BusinessId']  = station.vStationId
                     else:
                        islandsDict = []
                        resultJSON['Islands'] = islandsDict
                  else:
                     resultJSON['Login']  = 'BAD_TOKEN'
                     resultJSON['ERROR_MESSAGE']  = '(1)Es necesario dar de alta el dispositivo antes de usar el sistema, por favor delo de alta  <a href="register/index.html"><span id="voissLinkRegister"><b style="color:red"> AQUI </span></b></a>'
                     logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
            
                     return resultJSON

         resultJSON['Login']  = 'GOOD_USER'
         

         if user.vService:
            resultJSON['User_RFC']= user.vRFC
            resultJSON['User_Service']= user.vService

         resultJSON['UserName']  = user.vUserAccess.lower()

         if device:
            resultJSON['Device']  = device.vDeviceName
            resultJSON['TokenDevice']  = device.vDeviceToken
            resultJSON['VirtualKeyboard']  = device.vVirtualKeyboard

            resultJSON['LogoutInactivity']  = device.vLogoutInactivity
            resultJSON['LogoutTimeout']     = device.vTimeout
            device.vOldUserAgent= request.GET['hash']
            device.save()
         else:
            resultJSON['Device']  = ""

         if station:
            resultJSON['LocalIP']  = station.vStationLHost
            resultJSON['LocalPort']  = station.vStationLPort
            resultJSON['Station']  = station.vStationDesc
            resultJSON['BusinessId']  = station.vStationId
         else:
            resultJSON['LocalIP']  = ''
            resultJSON['LocalPort']  = ''
            resultJSON['Station']  = ''
            resultJSON['BusinessId']  = ''
         
         resultJSON['AddPermission']  = True
         resultJSON['QueryPermission']  = True

         resultJSON['CustomerPermission']  = True
         resultJSON['AssignPermission']  = True


         if not "DESPACHADOR" in user.vKind and not "SUPERVISOR" in user.vKind:
            resultJSON['ChangePermission']  = True
         else:
            resultJSON['ChangePermission']  = False

         allFunctions = GLFunctions.objects.all().order_by('vOrder');

         currentFunctionDict=[]
         for currentFunction in allFunctions:
            allUserPermissions = GLUserFunction.objects.filter(vFunctionsId= currentFunction)
            usersDict=[]
            allFunctionsDict = {}
            allFunctionsDict['FunctionName']= currentFunction.vFunctionName
            for currentPermission in allUserPermissions:
               currentUserObj ={}
               currentUserObj['UserId'] = currentPermission.vUserId.vUserAccess
               usersDict.append(currentUserObj)
            allFunctionsDict['FunctionUsers'] = usersDict
            currentFunctionDict.append(allFunctionsDict)

         resultJSON['Functions'] = currentFunctionDict


         headers =''
         footers =''

         if station:

            headers= headers+ str(station.vHeader1) + '|'
            headers= headers+ str(station.vHeader2) + '|'
            headers= headers+ str(station.vHeader3) + '|'
            headers= headers+ str(station.vHeader4) + '|'
            headers= headers+ str(station.vHeader5) + '|'
            headers= headers+ str(station.vHeader6) + '|'
            headers= headers+ str(station.vHeader7) + '|'
            headers= headers+ str(station.vHeader8) 

            footers= footers+ str(station.vFooter1) + '|'
            footers= footers+ str(station.vFooter2) + '|'
            footers= footers+ str(station.vFooter3) + '|'
            footers= footers+ str(station.vFooter4) + '|'
            footers= footers+ str(station.vFooter5) + '|'
            footers= footers+ str(station.vFooter6) + '|'
            footers= footers+ str(station.vFooter7) + '|'
            footers= footers+ str(station.vFooter8) 


         #Just for Dispatcher Users
         if user:
            if "DESPACHADOR" in user.vKind or "SUPERVISOR" in user.vKind or "OFICINA" in user.vKind or "WEB" in user.vKind:
               
               """
               logger.info('LOG_ID<' + currentTransaction + '> '+'ASKING FOR CURRENT SHIFT ON HOST:' + str(station.vStationWHost) + ' AND PORT: ' + station.vStationWPort)
               responseShift = askCurrentShiftService(station.vStationWHost,int(station.vStationWPort),request.GET['tokenDevice'])
               if responseShift:
                  logger.info('LOG_ID<' + currentTransaction + '> '+'Response : ' + str(responseShift))
                  if "ShiftOK" in str(responseShift):
                     responseShift= str(responseShift.decode("utf-8") )
                  else:
                     logger.error('LOG_ID<' + currentTransaction + '> '+'No Response from Server')
                     resultJSON['Login']  = 'ERROR'
                     resultJSON['ERROR_MESSAGE']  = 'Servidor no se pudo conectar a estacion en :' + str(station.vStationWHost) +':'+ str(station.vStationWPort)
                     return resultJSON
                     
               logger.info('LOG_ID<' + currentTransaction + '> '+'RESPONSE : ' + str(responseShift))
               """

               responseShift = 'ShiftOK_2017123101_01:Efectivo@02:Cheque nominativo@03:Transferencia electronica de fondos@04:Tarjeta de credito@05:Monedero electronico@06:Dinero electronico@08:Vales de despensa@12:Dacion en pago@13:Pago por subrogacion@14:Pago por consignacion@15:Condonacion@17:Compensacion@23:Novacion@24:Confusion@25:Remision de deuda@26:Prescripcion o caducidad@27:A satisfaccion del acreedor@28:Tarjeta de debito@29:Tarjeta de servicios@30:Aplicacion de anticipos@99:Por definir@_D01:Honorarios medicos dentales y gastos hospitalarios.@D02:Gastos medicos por incapacidad o discapacidad@D03:Gastos funerales.@D04:Donativos.@D05:Intereses reales efectivamente pagados por creditos hipotecarios (casa habitacion).@D06:Aportaciones voluntarias al SAR.@D07:Primas por seguros de gastos medicos.@D08:Gastos de transportacion escolar obligatoria.@D09:Depositos en cuentas para el ahorro primas que tengan como base planes de pensiones.@D10:Pagos por servicios educativos (colegiaturas)@G01:Adquisicion de mercancias@G02:Devoluciones descuentos o bonificaciones@G03:Gastos en general@I01:Construcciones@I02:Mobilario y equipo de oficina por inversiones@I03:Equipo de transporte@I04:Equipo de computo y accesorios@I05:Dados troqueles moldes matrices y herramental@I06:Comunicaciones telefonicas@I07:Comunicaciones satelitales@I08:Otra maquinaria y equipo@P01:Por definir@_E:Egreso@I:Ingreso@N:Nomina@P:Pago@T:Traslado@_01:Nota de credito de los documentos relacionados@02:Nota de debito de los documentos relacionados@03:Devolucion de mercancia sobre facturas o traslados previos@04:Sustitucion de los CFDI previos@05:Traslados de mercancias facturados previamente@06:Factura generada por los traslados previos@07:CFDI por aplicacion de anticipo@_Pumps:4_1:EFECTICARD@2:ACCORD@3:BANCOMER@4:BANAMEX@_1:1@2:1@3:2@4:2@_1:MAGNA@2:PREMIUM@'
               if "ShiftOK" in str(responseShift):
                  #shifts        = GLShift.objects.filter(vStationId = station,vShift=str(responseShift).split("_")[1])
                  payments      = responseShift.split("_")[2]
                  cfdiUses      = responseShift.split("_")[3]
                  proofTypes    = responseShift.split("_")[4]
                  relationTypes = responseShift.split("_")[5]
                  pumpsNo       = responseShift.split("_")[6]
                  gasCoupons    = responseShift.split("_")[7]
                  pumpsIsland   = responseShift.split("_")[8]
                  gasTypes      = responseShift.split("_")[9] 

                  logger.info('LOG_ID<' + currentTransaction + '> '+'PAYMENTS : ' + str(payments))
                  logger.info('LOG_ID<' + currentTransaction + '> '+'CFDI     : ' + str(cfdiUses))
                  logger.info('LOG_ID<' + currentTransaction + '> '+'PROOF    : ' + str(proofTypes))
                  logger.info('LOG_ID<' + currentTransaction + '> '+'RELATION : ' + str(relationTypes))
                  logger.info('LOG_ID<' + currentTransaction + '> '+'PUMPS NO : ' + str(pumpsNo))
                  logger.info('LOG_ID<' + currentTransaction + '> '+'GAS COUPONS : ' + str(gasCoupons))
                  logger.info('LOG_ID<' + currentTransaction + '> '+'PUMPS ISLAND : ' + str(pumpsIsland))
                  logger.info('LOG_ID<' + currentTransaction + '> '+'GAS TYPES : ' + str(gasTypes))

                  """
                  if not shifts:
                     newShift = GLShift()
                     newShift.vStationId= station
                     newShift.vShift= responseShift.split("_")[1]
                     logger.info('LOG_ID<' + currentTransaction + '> '+'SAVING NEW SHIFT ON SYSTEM : '+ str(responseShift.split("_")[1]) )
                     newShift.save()               
                  """
                  #pumpsIsland = '1:1@2:1@3:2@4:2@5:3@6:3@7:4@8:4@9:5@10:5@'
                  resultJSON['Shift']          = responseShift.split("_")[1]
                  resultJSON['Payments']       = payments
                  resultJSON['PumpsNo']        = int(pumpsNo.split(":")[1])
                  resultJSON['CfdiUses']       = cfdiUses
                  resultJSON['ProofTypes']     = proofTypes
                  resultJSON['RelationTypes']  = relationTypes
                  resultJSON['GasCoupons']     = gasCoupons  
                  resultJSON['PumpsIsland']    = split_islands(pumpsIsland)
                  resultJSON['GasTypes']       = str(gasTypes)
                  resultJSON['Islands']        = getRealIslands(resultJSON['PumpsIsland'])

               else:
                  resultJSON['Shift']          = ''
                  resultJSON['Payments']       = ''
                  resultJSON['CfdiUses']       = ''
                  resultJSON['ProofTypes']     = ''
                  resultJSON['RelationTypes']  = ''
                  resultJSON['GasCoupons']     = ''
                  resultJSON['PumpsIsland']    = ''
                  resultJSON['GasTypes']       = ''
            else:
               resultJSON['Shift']          = ''
               resultJSON['Payments']       = ''
               resultJSON['CfdiUses']       = ''
               resultJSON['ProofTypes']     = ''
               resultJSON['RelationTypes']  = ''
               resultJSON['GasCoupons']     = ''
               resultJSON['PumpsIsland']    = ''
               resultJSON['GasTypes']       = ''

         resultJSON['Headers']  = str(headers)
         resultJSON['Footers']  = str(footers)

         logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT SHIFT ON STATION: '+ str(resultJSON['Shift']))


         logger.info('LOG_ID<' + currentTransaction + '> '+'USER ' + user.vName + ' IS NOW IN THE SYSTEM ')
         if device:
            logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE [ ' + device.vDeviceName +' ]' )
         logger.info('LOG_ID<' + currentTransaction + '> '+'USER AUTENTICATED SUCCESFULLY')
         logLogin(currentTransaction,"OK", request.GET['tokenDevice'],request.GET['lsUser'], "****",request.GET['station'])

      except GLDevice.DoesNotExist:
      


         logger.error('LOG_ID<' + currentTransaction + '> '+'THE USER AND PASS ARE RIGHT BUT THE DEVICE IS NOT REGISTERED YET OR THE COOKIES ON THE BROWSER WERE DELETED')
         resultJSON['Login']  = 'BAD_TOKEN'
         resultJSON['ERROR_MESSAGE']  = 'Es necesario dar de alta el dispositivo antes de usar el sistema, por favor delo de alta  <a href="register/index.html"><span id="voissLinkRegister"><b style="color:red"> AQUI </span></b></a>'
         logLogin(currentTransaction,"The devices is not registered", request.GET['tokenDevice'],request.GET['lsUser'], request.GET['lsPass'],request.GET['station'])
      except GLStation.DoesNotExist:
         logger.error('LOG_ID<' + currentTransaction + '> '+'THE STATION DOES NOT EXIST ON THE SYSTEM')
         resultJSON['Login']  = 'Terminal Pertenece a estacion : ' +  str(request.GET['station'] + ' pero la estacion no existe en el sistema')
         resultJSON['ERROR_MESSAGE']  = 'La estacion:' + str(request.GET['station']) + ' no existe en el sistema'
         logLogin(currentTransaction,"The station it does not exist on the system", request.GET['tokenDevice'],request.GET['lsUser'], request.GET['lsPass'],request.GET['station'])
      except GLShift.DoesNotExist:
         logger.error('LOG_ID<' + currentTransaction + '> '+'THERE IS NO SHIFT CONFIGURED ON THE SYSTEM')
         resultJSON['Login']  = 'NO SHIFT'
         resultJSON['ERROR_MESSAGE']  = 'No existen turnos en el sistema'

   except GLUser.DoesNotExist:
      logger.error('LOG_ID<' + currentTransaction + '>'+'BAD AUTHENTICATION')
      resultJSON['Login']  = 'BAD_USER'
      resultJSON['ERROR_MESSAGE']  = '(3)El usuario y/o password son incorrectos'
      logLogin(currentTransaction,"User / Password incorrect", request.GET['tokenDevice'],request.GET['lsUser'], request.GET['lsPass'],request.GET['station'])


   logger.info('LOG_ID<' + currentTransaction + '> '+'Validating device config to reset ... INI')


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END loginUser')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#

@json_response
def validateUser(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + currentTransaction + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'START validateUser')
   logger.info('LOG_ID<' + currentTransaction + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New Validate User ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['station']+ ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'KIND            : [' + request.GET['kind']+ ']')

   try:
      user = GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'],vPassAccess=request.GET['lsPass'], vKind=request.GET['kind'],vStationId__vStationDesc=request.GET['station'])

      resultJSON['ValidateUser']  = 'GOOD_USER'
      resultJSON['vName']  = user.vName
      resultJSON['vLastname']  = user.vLastname
      resultJSON['vPassAccess']  = user.vPassAccess
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER EXIST ON THE SYSTEM')

   except GLUser.DoesNotExist:
      resultJSON['ValidateUser']  = 'BAD_USER'
      logger.error('LOG_ID<' + currentTransaction + '>'+'BAD AUTHENTICATION')
      resultJSON['Login']  = 'BAD_USER'
      resultJSON['ERROR_MESSAGE']  = 'El usuario y/o password son incorrectos'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END validateUser')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON

#}}}#

def askTicketService(ipAddress, #{{{#
                      port,
                      pump, 
                      deviceId,
                      dispatcher,
                      driver,
                      deviceName,
                      island,
                      maxTime,
                      getInfo,
                      NameUser,
                      paymentKind,
                      bank,
                      account,
                      refundId):

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ipAddress = "127.0.0.1"              
    #ipAddress = "192.168.0.12"              
    port = 5021
    #data2 = "01869182030467860                                 4.0.1                 01              101="
    
    data = "01321-723-681                                 4.0.1                 02              199?"
    try:
        clientsocket.connect((ipAddress , port))
        logger.info('LOG_ID<' + str(currentTransaction) + '> '+'IP: '+ipAddress+" PORT: "+str(port))
        logger.info('LOG_ID<' + str(currentTransaction) + '> '+'DATA TO SEND: '+data)
        logger.info('LOG_ID<' + str(currentTransaction) + '> '+'DATA ENCODED TO SEND: '+str(data.encode()))
        clientsocket.send(data.encode())
        #time.sleep(0.1)
        time.sleep(1)

        clientsocket.settimeout(90)
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

    print(f"Respuesta de gaslight terminal: {msg}")
    if "TicketOK" in str(msg):
        return msg
    else:
        return "ERROR :" + str(msg)
#}}}#

def askDeliveryTicketService(ipAddress, #{{{#
                      port,
                      deviceId,
                      deviceName,
                      driverName,
                      shift,
                      island,
                      totalCash,
                      totalCredit,
                      totalDebit,
                      totalOthers,
                      othersDesc,
                      copy):

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        clientsocket.connect((ipAddress , port))
        clientsocket.send( (TICKET_DELIVERY_COMMAND
                          + deviceId.rjust(36)  
                          + deviceName.rjust(20)
                          + driverName.rjust(50)
                          + shift.rjust(12)
                          + island.rjust(2)
                          + totalCash.rjust(12)
                          + totalCredit.rjust(12)
                          + totalDebit.rjust(12)
                          + totalOthers.rjust(12)
                          + othersDesc.rjust(50)
                          + str(copy)).encode()
                          )
        #time.sleep(0.1)
        time.sleep(1)

        clientsocket.settimeout(90)
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


    if "TicketOK" in str(msg):
        return msg
    else:
        return "ERROR :" + str(msg)
#}}}#

def askBillingTicketService(ipAddress, #{{{#
                      port,
                      billingId):

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        clientsocket.connect((ipAddress , port))
        clientsocket.send( (TICKET_BILLING_COMMAND
                          + billingId  ).encode()
                          )
        #time.sleep(0.1)
        time.sleep(1)

        clientsocket.settimeout(90)
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


    if "TicketOK" in str(msg):
        return msg
    else:
        return "ERROR :" + str(msg)
#}}}#


def askInventoryService(ipAddress, #{{{#
                      port,
                      deviceId,
                      dispatcher,
                      deviceName):

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        clientsocket.connect((ipAddress , port))
        clientsocket.send( (INVENTORY_COMMAND
                          + deviceId.rjust(36)  
                          + VERSION.rjust(10)
                          + dispatcher.rjust(10)
                          + deviceName.rjust(20)).encode()
                          )
        #time.sleep(0.1)
        time.sleep(1)

        clientsocket.settimeout(90)
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


    if "InventoryOK" in str(msg):
        return msg
    else:
        return "ERROR :" + str(msg)
#}}}#

def askBillingService(ipAddress, #{{{#
                      port,
                      pump, 
                      rfc,
                      paymentKind,
                      cfdiUse,
                      proofKind,
                      relationKind,
                      bank,
                      account,
                      deviceId,
                      dispatcher,
                      island, 
                      maxTime):

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        clientsocket.connect((ipAddress , port))
        clientsocket.send( (BILLING_COMMAND
                          + deviceId.rjust(36) 
                          + VERSION.rjust(10)
                          + dispatcher.rjust(10) 
                          + " ".rjust(10)  
                          + pump.rjust(2)
                          + rfc.rjust(15)
                          + bank.rjust(50)
                          + account.rjust(10)
                          + island.rjust(2)
                          + paymentKind.rjust(3)
                          + cfdiUse.rjust(3)
                          + proofKind.rjust(3)
                          + relationKind.rjust(3)
                          + maxTime.rjust(3)).encode()
                          )
        #time.sleep(0.1)
        time.sleep(1)

        clientsocket.settimeout(90)
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


    if "BillingOK" in str(msg):
        return msg
    else:
        return "ERROR :" + str(msg)
#}}}#

def askBillingWebService(ipAddress, #{{{#
                      port,
                      saleId,
                      amount,
                      rfc,
                      paymentKind,
                      cfdiUse,
                      proofKind,
                      bank,
                      account):

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        clientsocket.connect((ipAddress , port))
        clientsocket.send( (BILLING_WEB_COMMAND
                          + saleId.rjust(15)
                          + amount.rjust(10)
                          + rfc.rjust(15)
                          + bank.rjust(50)
                          + account.rjust(10)
                          + paymentKind.rjust(3)
                          + cfdiUse.rjust(3)
                          + proofKind.rjust(3)).encode()
                          )
        #time.sleep(0.1)
        time.sleep(1)

        clientsocket.settimeout(90)
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


    if "BillingOK" in str(msg):
        return msg
    else:
        return "ERROR :" + str(msg)
#}}}#

def askCancelService(ipAddress, #{{{#
                      port,
                      pump, 
                      deviceId,
                      dispatcher,
                      driver):

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        clientsocket.connect((ipAddress , port))
        clientsocket.send( (CANCEL_COMMAND
                          + deviceId.rjust(36)  
                          + VERSION.rjust(10)
                          + dispatcher.rjust(10) 
                          + driver.rjust(10)  
                          + pump.rjust(2)).encode() )  
        #time.sleep(0.1)
        time.sleep(1)

        clientsocket.settimeout(90)
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


    if "CancelOK" in str(msg):
        return msg
    else:
        return "ERROR :" + str(msg)
#}}}#

def sendPresetService(ipAddress, #{{{#
                      port,
                      pump, 
                      deviceId,
                      dispatcher,
                      driver,
                      product, 
                      kind, 
                      amount):

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        clientsocket.connect((ipAddress , port))
        clientsocket.send( (PRESET_COMMAND
                          + deviceId.rjust(36)  
                          + VERSION.rjust(10)
                          + dispatcher.rjust(10) 
                          + driver.rjust(10)  
                          + pump.rjust(2)
                          + product.rjust(10)
                          + kind.rjust(1)
                          + amount.rjust(10)).encode()
                          )
        #time.sleep(0.1)
        time.sleep(1)

        clientsocket.settimeout(90)
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


    if "PresetOK" in str(msg):
        return msg
    else:
        return "ERROR :" + str(msg)
#}}}#

def initServer():

   logger.info('Iniciando hilo de escucha para GLTERMINAL')
   listener = threads.listener_thread()
   listener.start()
   
def waitForResponseThread():
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    serverSocket.bind((socket.gethostbyname(socket.gethostname()),50000)) #makes the link of the socket with the ip address and the port
    serverSocket.listen(5)  #Specifies the number of clients which can listen at the same times
    print('Listen in: {}'.format(socket.gethostbyname(socket.gethostname())))

    try:

        print('Esperando respuesta de Thread')
        conn, addr = serverSocket.accept()
        print(f'Django Back {socket.gethostbyname(socket.gethostname())} port: 50000')

        while True:
            try:
                msg = conn.recv(4096) #gets the data from the client
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
    except Exception as e:
        msg = e
    else:
        conn.close()

    data_list = pickle.loads(msg)
    logger.info('LOG_ID'+ str(currentTransaction)+ ' DJANGO RECIBIO TRAMA DE PARTE DE HILO: '+str(data_list))

    return data_list

def get_format_and_sentences(data):
   
   split_data = lambda fullsentence: [fullsentence[0:4],fullsentence[4:]] if len(fullsentence)>4 else ['\n']

   splited_data = list(map(split_data,data.split('^')))

   return splited_data

def xor_strings(data):
	
   only_data = data[1:len(data)-2]
   print(f"Data: {data}\n")
   for i in range(0,len(only_data)):
      if i==0:
         result = chr(ord(only_data[i]) ^ ord(only_data[i+1]))
         #print(f"{data[i]} xor {data[i+1]}={result}")
      elif i>0 and i+1<len(only_data): 
         aux = result
         result = chr(ord(result) ^ ord(only_data[i+1]))
         #print(f"{aux} xor {data[i+1]}={result}")

   print(f"Resultado CRC: {result}")
   return result

def build_trama(dict_data):

   #Si es ticket
   if dict_data['command'] == '01':
      
      logger.info('LOG_ID<' + str(currentTransaction) + 'FUNCION TICKET')

      if len(dict_data['pump']) == 1:
         pump = '0'+dict_data['pump']

      trama = ""+ \
         dict_data['command'].rjust(2)+ \
         "321-723-681".ljust(44)+ \
         "4.0.1".ljust(22)+ \
         pump.ljust(16)+ \
         dict_data['methodPayment'].rjust(1)+ \
         dict_data['paymentCode'].rjust(2)+ ""

   #Si es factura
   elif dict_data['command'] == '02':
      pass
   #Si es preset
   elif dict_data['command'] == '03':
      pass
   #Si es cancela preset
   elif dict_data['command'] == '04':
      pass
   #Si es asigna
   elif dict_data['command'] == '09':
      pass
   #Si es corte de turno
   elif dict_data['command'] == '10':
      
      logger.info('LOG_ID<' + str(currentTransaction) + 'FUNCION CORTE DE TURNO')
      trama = ""+ \
         dict_data['command'].rjust(2)+ \
         "321-723-681".ljust(44)+ \
         "4.0.1".ljust(12)+ ""

   #Si es inventario de tanques
   elif dict_data['command'] == '11':
      
      logger.info('LOG_ID<' + str(currentTransaction) + 'FUNCION INVENTARIO DE TANQUES')
      trama = ""+ \
         dict_data['command'].rjust(2)+ \
         "321-723-681".ljust(44)+ \
         "4.0.1".ljust(12)+ ""

   #Si es transacción de cliente
   elif dict_data['command'] == '12':
      pass
   #Si es turno copia
   elif dict_data['command'] == '14':
      pass
   else:
      trama = ''

   if len(trama)>0:
      trama += xor_strings(trama)

   logger.info('LOG_ID<' + str(currentTransaction) + 'TRAMA FINAL: '+trama)
   return trama

#http://127.0.0.1:20000/pumpsModule/askKindTicket/?lsUser=admin&lsPass=1234&tokenDevice=869182030467860&stationId=5189&pump=1
def askKindTicketService(ipAddress,port,trama,prod):
       
   
   ipAddress = socket.gethostbyname(socket.gethostname())              
   port = 5021
   #data  = "01321-723-681                                 4.0.1                 01              101="
   #data  = ""+command.rjust(2)+"321-723-681".ljust(44)+"4.0.1".ljust(22)+pump.ljust(16)+methodPayment.rjust(1)+paymentCode.rjust(2)+""
 
   logger.info('LOG_ID<' + str(currentTransaction) + '> TRAMA: '+trama)
   if prod:
      logger.info('LOG_ID<' + str(currentTransaction) + '> Writing info on socket 3')
      logger.info('LOG_ID<' + str(currentTransaction) + '> Sending data to GLTerminal in '+ipAddress+':'+str(port))
      clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
         clientsocket.connect((ipAddress , port))
         clientsocket.send(trama.encode())
         clientsocket.close()

         msg = waitForResponseThread()

      except socket.error as msg:
         return 'No se pudo conectar a servidor <' + str(msg) + '>'
         print(f"Mensaje recibido de gaslight terminal: {msg}")    
   else:
      #msg = waitForResponseThread()
      msg = trama
   
   return msg

@json_response
def askKindTicket(request):
   resultJSON = {}
   logger.info('')
   logger.info('')

   global currentTransaction
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START askKindTicket')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'New Ticket Request 3 ' + VERSION)
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'USER            : [' + request.GET['lsUser']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PASS            : [' + request.GET['lsPass']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'STATIONID       : [' + request.GET['stationId']+ ']')
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PUMP            : [' + request.GET['pump']+ ']')
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'COMMAND         : [' + request.GET['command']+ ']')
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'METHODPAYMENT   : [' + request.GET['methodPayment']+ ']')
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PAYMENTCODE     : [' + request.GET['paymentCode']+ ']')



   currentTransaction+=1

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
      device  = GLDevice.objects.get(vDeviceToken=request.GET['tokenDevice'])
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Device Found : ' + str(request.GET['tokenDevice']) + '')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Max Time configured on station : ' + str(localStationId.vPrintTime) + '')

      if not device.vIsActive:
         error='^DISPOSITIVO^'+ device.vDeviceName +'^DESHABILITADO^DE SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device : ' + str(device.vIsActive) + ' is not active on the system')
         resultJSON['askKindTicket'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON


   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['askKindTicket'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON
   except GLDevice.DoesNotExist:
      error='^EL DISPOSITIVO^' + str(request.GET['tokenDevice']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device : ' + str(request.GET['tokenDevice']) + ' does not exist on system')
      resultJSON['askKindTicket'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON

   if len(request.GET['lsUser'])>0:
      try:
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
         localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK {' + localUserId.vName + ' ' + localUserId.vLastname + '}' )
         resultJSON['Dispatcher']= localUserId.vName + ' ' + localUserId.vLastname
      except GLUser.DoesNotExist:
         error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
         resultJSON['askKindTicket'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Sending ticket request to server _ : '  +  str(localStationId.vStationWHost) + ':' + str(localStationId.vStationWPort) )

   if not localStationId.vStationWHost or not localStationId.vStationWPort:
         error='^ES NECESARIO^ ^CONFIGURAR SERVIDOR^Y PUERTO DE ESTACION'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The server and port need to be configured properly')
         resultJSON['askKindTicket'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON



   trama = build_trama(request.GET)
   #For true values
   response = askKindTicketService(localStationId.vStationWHost, int(localStationId.vStationWPort),trama,True)
   #For dev version
   #response = askKindTicketService(localStationId.vStationWHost, int(localStationId.vStationWPort),trama,False)


   """
   if "InfoOK" in str(response):
      #response = 'TicketInfoOK_00'
      #TicketIInfoOK_11

      resultJSON['askKindTicket'] = 'OK'
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Response received by station : ' + str(response))
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Ticket was successfull  ')
      response=str(response)

      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Info returned by the database' + response)
      isOriginal = response.split('_')[1][0]
      isNormal   = response.split('_')[1][1]
      
      if isOriginal=="0":
         resultJSON['askData'] = 'True'
      else:
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' SE IMPRIMIRA LA COPIA NO. ')
         resultJSON['askData'] = 'False'

      if isNormal=="0":
         resultJSON['kindTicket'] = 'NORMAL'
      else:
         resultJSON['kindTicket'] = 'FLOTILLAS'      

      logger.info('LOG_ID<' + str(currentTransaction) + '> IS ORIGINAL           :  ' + resultJSON['askData'])
      logger.info('LOG_ID<' + str(currentTransaction) + '> KIND TICKET           :  ' + resultJSON['kindTicket'])
   
   else:
      resultJSON['askKindTicket'] = 'ERROR'
      resultJSON['ERROR'] = str(response)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Ticket throws the next error : ' + str(response))
         
   """

   resultJSON['Result'] = response
   resultJSON['askKindTicket'] = 'OK'
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END askKindTicket')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON


@json_response
def ticket(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')

   global currentTransaction
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START ticket')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'New Ticket Request 1' + VERSION)
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'USER            : [' + request.GET['lsUser']+ '     ]')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PASS            : [' + request.GET['lsPass']+ '     ]')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'STATIONID       : [' + request.GET['stationId']+ '  ]')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PUMP            : [' + request.GET['pump']+ '       ]')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PRINT_TICKET    : [' + request.GET['printTicket']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'SEND_MAIL       : [' + request.GET['sendMail']+ '   ]')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'MAIL            : [' + request.GET['mail']+ '       ]')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'DISPATCHER      : [' + request.GET['dispatcher']+ ' ]')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'ISLAND          : [' + request.GET['island']+ '     ]')
   
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PAYMENT KIND    : [' + request.GET['paymentKind']+ ']')
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'BANK            : [' + request.GET['bank']+ '       ]')
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'ACCOUNT         : [' + request.GET['account']+ '    ]')
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'REFUND ID         : [' + request.GET['refundId']+ ' ]')


   currentTransaction+=1

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
      device  = GLDevice.objects.get(vDeviceToken=request.GET['tokenDevice'])
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Device Found : ' + str(request.GET['tokenDevice']) + '')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Max Time configured on station : ' + str(localStationId.vPrintTime) + '')

      if not device.vIsActive:
         error='^DISPOSITIVO^'+ device.vDeviceName +'^DESHABILITADO^DE SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device : ' + str(device.vIsActive) + ' is not active on the system')
         resultJSON['Ticket'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON


   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['Ticket'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON
   except GLDevice.DoesNotExist:
      error='^EL DISPOSITIVO^' + str(request.GET['tokenDevice']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device : ' + str(request.GET['tokenDevice']) + ' does not exist on system')
      resultJSON['Ticket'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON

   if len(request.GET['lsUser'])>0:
      try:
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
         localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK {' + localUserId.vName + ' ' + localUserId.vLastname + '}' )
         resultJSON['Dispatcher']= localUserId.vName + ' ' + localUserId.vLastname
      except GLUser.DoesNotExist:
         error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
         resultJSON['Ticket'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   localDispatcherId= None
   localDriverId= None

   if len(request.GET['dispatcher'].lstrip("0"))>0:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating dispatcher in station ' + str(localStationId))
      try:
         localDispatcherId= GLUser.objects.get(vPassAccess=request.GET['dispatcher'], vKind='DESPACHADOR', vStationId= localStationId)
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Dispatcher is OK {' + localDispatcherId.vName + ' ' + localDispatcherId.vLastname + '}' )
         
      except GLUser.DoesNotExist:
         error='^EL DESPACHADOR^ ^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The dispatcher : ' + str(request.GET['dispatcher']) + ' does not exist on system')
         resultJSON['Ticket'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   getInfo=0
   if device.vPrintLocal:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Getting all the info to print in local printer from server: ' + str(localStationId.vStationWHost) + ':' + localStationId.vStationWPort)
      resultJSON['TicketKind'] = 'Terminal'
      getInfo=1

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Sending ticket request to server: 127.0.0.1 5021' )

   if not localStationId.vStationWHost or not localStationId.vStationWPort:
         error='^ES NECESARIO^ ^CONFIGURAR SERVIDOR^Y PUERTO DE ESTACION'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The server and port need to be configured properly')
         resultJSON['Ticket'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   bank="bank"#request.GET['bank']
   account="account"#request.GET['account']
   refundId= "refundid"#request.GET['refundId']
   #if "undefined" in request.GET['bank']:
   #   bank=""
   #if "undefined" in request.GET['account']:
   #   account=""
   #if "undefined" in request.GET['refundId']:
   #   refundId=""

   """
   paymentKind=request.GET['paymentKind']
   if "EFECTIVO" in request.GET['paymentKind']:
      paymentKind="1"
   """
   response = askTicketService(localStationId.vStationWHost, 
                                int(localStationId.vStationWPort), 
                                request.GET['pump'],
                                request.GET['tokenDevice'],
                                request.GET['dispatcher'],
                                "",
                                device.vDeviceName,
                                request.GET['island'],
                                str(localStationId.vPrintTime) ,
                                str(getInfo),
                                resultJSON['Dispatcher'],
                                "paymentKind",
                                bank,
                                account,
                                refundId
                                )


   
   if "TicketOK" in str(response):
      #response = 'TicketOK_ 83 _ 19/01/2018 13:16:34 13206 3998 _ 3998 _1 _ 1 _ 1 _ 1 _2017123101 _ 3998 MAGNA   12.832 $09.00   $115.48   _ Ciento Quince Pesos 48/100 M.N. _                                    Francisco Duran _15.27093_100.2091_Efectivo  _666_2_  _'
      #response = 'TicketOK_ 83 _ 19/01/2018 13:16:34 13206 3998 _ 3998 _1 _ 1 _ 1 _ 1 _2017123101 _ 3998 MAGNA   12.832 $09.00   $115.48   _ Ciento Quince Pesos 48/100 M.N. _                                    Francisco Duran _15.27093_100.2091_Efectivo  _666_2_3344_34_FLOTILLAS PRUEBA_3_ERFA-123_2001_12345_PRUEBA_  _1_ DEBITO_ 0'
      resultJSON['Ticket'] = 'OK'
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Response received by station : ' + str(response))
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Ticket was successfull  ')
      response=str(response)
      if len(response.split('_')):
         saleId= response.split('_')[1]
      else:
         saleId=""


      if getInfo:
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Info returned by the database')

         #Info general de ticket
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Copies          :  '     +  str(response.split('_')[1]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' BuyDate         :  '     +  str(response.split('_')[2]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Station         :  '     +  str(response.split('_')[3]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Ticket Id       :  '     +  str(response.split('_')[4]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Island          :  '     +  str(response.split('_')[5]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Pump            :  '     +  str(response.split('_')[6]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Shift           :  '     +  str(response.split('_')[7]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' SaleId          :  '     +  str(response.split('_')[8]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Info Sale       :  '     +  str(response.split('_')[9]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Amount Text     :  '     +  str(response.split('_')[10]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Name Dispatcher :  '     +  str(response.split('_')[11].strip()))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' IVA             :  '     +  str(response.split('_')[12]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Subtotal        :  '     +  str(response.split('_')[13]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Kind Payment    :  '     +  str(response.split('_')[14]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Transaction     :  '     +  str(response.split('_')[15]))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Hose            :  '     +  str(response.split('_')[16]))
         
         #Si es ticket de flotillas
         if not (response.split('_')[17])=='  ':
            resultJSON['kind_ticket'] = 'Fleets'

            logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Tag            :  ' +  str(response.split('_')[17]))
            logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Client         :  ' +  str(response.split('_')[18]))
            logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Company        :  ' +  str(response.split('_')[19]))
            logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Vehicle        :  ' +  str(response.split('_')[20]))
            logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Plate          :  ' +  str(response.split('_')[21]))
            logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Model          :  ' +  str(response.split('_')[22]))
            logger.info('LOG_ID<' + str(currentTransaction) + '> '+' No. Eco        :  ' +  str(response.split('_')[23]))
            logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Driver         :  ' +  str(response.split('_')[24]))
            logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Ref            :  ' +  str(response.split('_')[25]))
            logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Odom           :  ' +  str(response.split('_')[26]))
            logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Kind Client    :  ' +  str(response.split('_')[27]))
            logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Ren            :  ' +  str(response.split('_')[28]))

            
         else:
            resultJSON['kind_ticket'] = 'Normal'

         
         #Si se puede imprimir original
         if response.split('_')[1].strip()=="0":
            
            #Si es de flotillas
            if resultJSON['kind_ticket'] == 'Fleets':
               #Si se va a imprimir solo el original
               if not localStationId.vPrintBoth:
                  resultJSON['IsOriginal'] = 'True'

               #Se va a imprimir original y copia
               else:
                  response_copy = askTicketService(localStationId.vStationWHost, 
                                   int(localStationId.vStationWPort), 
                                   request.GET['pump'],
                                   request.GET['tokenDevice'],
                                   request.GET['dispatcher'],
                                   "",
                                   device.vDeviceName,
                                   request.GET['island'],
                                   str(localStationId.vPrintTime) ,
                                   str(getInfo),
                                   resultJSON['Dispatcher'],
                                   "payment",
                                   "bank",
                                   "account",
                                   "refundId"
                                   )
                  response_copy= str(response_copy)
                  resultJSON['IsOriginal'] = 'Both'
                  logger.info('LOG_ID<' + str(currentTransaction) + '> '+'No. Copie to print     :  ' +  str(response_copy.split('_')[1]))
                  resultJSON['Copy']       = str(response_copy.split('_')[1].strip())

            #Si es ticket normal      
            elif resultJSON['kind_ticket'] == 'Normal':
               resultJSON['IsOriginal'] = 'True'
         #Si solo se puede imprimir copias
         else:
            resultJSON['IsOriginal'] = 'False'
            resultJSON['Copy']       = str(response.split('_')[1].strip())


         
         resultJSON['BuyDate']    = str(response.split('_')[2].strip())
         resultJSON['Station']    = str(response.split('_')[3].strip())
         resultJSON['TicketId']   = str(response.split('_')[4].strip())
         resultJSON['Island']     = str(response.split('_')[5].strip())
         resultJSON['Pump']       = str(response.split('_')[6].strip())
         resultJSON['Shift']      = str(response.split('_')[7].strip())
         resultJSON['SaleId']     = str(response.split('_')[8].strip())
         resultJSON['InfoSale']   = str(response.split('_')[9].strip())
         resultJSON['AmountText'] = str(response.split('_')[10].strip())
         resultJSON['NameDispatcher'] = str(response.split('_')[11].strip())
         resultJSON['IVA']            = str(response.split('_')[12].strip())
         resultJSON['Subtotal']       = str(response.split('_')[13].strip())
         resultJSON['KindPayment']    = str(response.split('_')[14].strip())
         resultJSON['Transaction']    = str(response.split('_')[15].strip())
         resultJSON['Hose']           = str(response.split('_')[16].strip())
         

         #TipoCliente_transacción_manguera_Rendimiento

         #Si el ticket es de flotillas se guardan sus valores
         if resultJSON['kind_ticket'] == 'Fleets':

            resultJSON['idCard']       = str(response.split('_')[17].strip())
            resultJSON['Client']       = str(response.split('_')[18].strip())
            resultJSON['Company']      = str(response.split('_')[19].strip())
            resultJSON['Vehicle']      = str(response.split('_')[20].strip())
            resultJSON['Plate']        = str(response.split('_')[21].strip())
            resultJSON['Model']        = str(response.split('_')[22].strip())
            resultJSON['NoEco']        = str(response.split('_')[23].strip())
            resultJSON['Driver']       = str(response.split('_')[24].strip())
            resultJSON['Ref']          = str(response.split('_')[25].strip())
            resultJSON['Odom']         = str(response.split('_')[26].strip())
            resultJSON['KindClient']   = str(response.split('_')[27].strip())
            resultJSON['Ren']          = str(response.split('_')[28].strip())



      logTiket(currentTransaction, "OK", request.GET['tokenDevice'],request.GET['lsUser'],request.GET['stationId'],request.GET['pump'] ,saleId)

   else:
      resultJSON['Ticket'] = 'ERROR'
      resultJSON['ERROR'] = str(response)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Ticket throws the next error : ' + str(response))
      logTiket(currentTransaction, "ERROR", request.GET['tokenDevice'],request.GET['lsUser'],request.GET['stationId'],request.GET['pump'],'' )

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END ticket')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#

@json_response
def delivery(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')

   global currentTransaction
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START delivery')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'New Delivery ' + VERSION)
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   currentTransaction+=1

   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('shift') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'SHIFT           : [' + request.GET['shift']+ ']')

   if request.GET.get('totalCash') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOTAL CASH     : [' + request.GET['totalCash']+ ']')

   if request.GET.get('totalVoucherC') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOTAL T CREDITO  : [' + request.GET['totalVoucherC']+ ']')

   if request.GET.get('totalVoucherD') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOTAL T DEBITO  : [' + request.GET['totalVoucherD']+ ']')

   if request.GET.get('totalOthers') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOTAL OTHERS    : [' + request.GET['totalOthers']+ ']')

   if request.GET.get('descOthers') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'DESC OTHERS     : [' + request.GET['descOthers']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['Delivery'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(Q(vKind="WEB") | Q(vKind="DESPACHADOR"),vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['Delivery'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   currentDelivery = GLPartialDelivery()
   currentDelivery.vUserId= localUserId
   currentDelivery.vDate = datetime.datetime.now()
   currentShift = GLShift.objects.get(vStationId= localStationId, vShift=request.GET['shift'])
   
   currentDelivery.vShiftId = currentShift

   currentDelivery.vCashAmount = request.GET['totalCash']
   currentDelivery.vVoucherAmountC = request.GET['totalVoucherC']
   currentDelivery.vVoucherAmountD = request.GET['totalVoucherD']
   currentDelivery.vOthersAmount = request.GET['totalOthers']
   currentDelivery.vOthersDesc = request.GET['descOthers']
   currentDelivery.vIsland = request.GET['island']

   currentDelivery.save()

   resultJSON['Delivery'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Sending delivery ticket request to server: ' + str(localStationId.vStationWHost) + ':' + str(localStationId.vStationWPort))

   response = askDeliveryTicketService (localStationId.vStationWHost, 
                                int(localStationId.vStationWPort), 
                                request.GET['tokenDevice'],
                                "",
                                localUserId.vName + ' ' + localUserId.vLastname,
                                currentShift.vShift,
                                request.GET['island'],
                                request.GET['totalCash'],
                                request.GET['totalVoucherC'],
                                request.GET['totalVoucherD'],
                                request.GET['totalOthers'],
                                request.GET['descOthers'],
                                0
                                )

   response=str(response)
   if "TicketOK" in str(response):
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Delivery ticket printed succesfully')
   else:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' Error while trying to print delivery ticket')

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END delivery')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#

@json_response
def printDelivery(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')

   global currentTransaction
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START printDelivery')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'New Delivery ' + VERSION)
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   currentTransaction+=1

   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['PrintDelivery'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(Q(vKind="WEB") | Q(vKind="DESPACHADOR"),vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['PrintDelivery'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   currentDeliveries= GLPartialDelivery.objects.filter(vUserId=localUserId).order_by('-vDate')

   if currentDeliveries:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Sending delivery ticket request to server: ' + str(localStationId.vStationWHost) + ':' + str(localStationId.vStationWPort))
      currentDelivery = currentDeliveries[0]

      response = askDeliveryTicketService (localStationId.vStationWHost, 
                                   int(localStationId.vStationWPort), 
                                   request.GET['tokenDevice'],
                                   "",
                                   localUserId.vName + ' ' + localUserId.vLastname,
                                   currentDelivery.vShiftId.vShift,
                                   str(currentDelivery.vIsland),
                                   currentDelivery.vCashAmount,
                                   currentDelivery.vVoucherAmountC,
                                   currentDelivery.vVoucherAmountD,
                                   currentDelivery.vOthersAmount,
                                   currentDelivery.vOthersDesc,
                                   1
                                   )

      response=str(response)
      if "TicketOK" in str(response):
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Delivery ticket printed succesfully')
         resultJSON['PrintDelivery'] = 'OK'
      else:
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' Error while trying to print delivery ticket')
         resultJSON['PrintDelivery'] = 'ERROR'
         resultJSON['ERROR'] = 'No existen registros de entregas'
   else:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' Error while trying to print delivery ticket')
      resultJSON['PrintDelivery'] = 'ERROR'
      resultJSON['ERROR'] = 'No existen registros de entregas'


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END printDelivery')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#

@json_response
def printBilling(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')

   global currentTransaction
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START printBilling')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'New Print Billing ' + VERSION)
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   currentTransaction+=1

   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('billingId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'BILLING ID      : [' + request.GET['billingId']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['PrintBilling'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Sending billing ticket request to server: ' + str(localStationId.vStationWHost) + ':' + str(localStationId.vStationWPort))

   response = askBillingTicketService (localStationId.vStationWHost, 
                                int(localStationId.vStationWPort), 
                                request.GET['billingId']
                                )

   response=str(response)
   if "BillingTicketOK" in str(response):
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Billing ticket printed succesfully')
      resultJSON['PrintBilling'] = 'OK'
   else:
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' Error while trying to print billing ticket')
      resultJSON['PrintBilling'] = 'ERROR'
      resultJSON['ERROR'] = 'No existen registros de entregas'


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END printBilling')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#

def turn_on_dict(string,t,number_tank,percentage):

   #dict for ticket's date
   if t=="0":
      # Data received: TicketOK_95_18/02/2020 02:26:37 p.m.
      ticket = {}
      data = string.split("_")
      ticket["TicketOK"] = data[0]
      ticket["Percentage"] = data[1]
      ticket["Date"] = data[2]
      return ticket

      #dict for tank
   elif t=="1":
      #Data received: MAGNA_100000_0_99000_94050_0_0_0_0_0_
      tank = {}
      tank["Num_tank"] = str(number_tank)
      data = string.split("_")
      tank["gasType"] = data[0]
      tank["tankCapacity"] = data[1]
      tank["volume"] = data[2]
      tank["toFill"] = data[3]
      tank["p_ToFill"] = percentage
      tank["l_ToFill"] = data[4]
      tank["ctVolume"] = data[5]
      tank["level"] = data[6]
      tank["waterVol"] = data[7]
      tank["water"] = data[8]
      tank["temp"] = data[9]
      return tank
    




def split_tank(data):
   #data = all the string of data about tanks

   Data_Tanks = re.split(r"_\d_T.",data) #split all tanks
   Date_Ticket = Data_Tanks[0] 
   Dict_Data = {}

   #Dict_Data["DateTicket"] = turn_on_dict(Date_Ticket,"0",None,None)
   Dict_Ticket = turn_on_dict(Date_Ticket,"0",None,None)
   index = 1
   for tank in Data_Tanks[1:]:
      dict_tank = turn_on_dict(tank,"1",index,Dict_Ticket["Percentage"])
      print("=====================================================================")
      print("Tank: {}".format(dict_tank))
      print("=====================================================================")
      Dict_Data["Tank_"+str(index)] = dict_tank
      index += 1

   return [Dict_Data,Dict_Ticket]


@json_response
def inventory(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')

   global currentTransaction
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START Tank Inventory Ticket')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'New Ticket Inventory Request ' + VERSION)
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'USER            : [' + request.GET['lsUser']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PASS            : [' + request.GET['lsPass']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'STATIONID       : [' + request.GET['stationId']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'DISPATCHER      : [' + request.GET['dispatcher']+ ']')


   currentTransaction+=1

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
      device  = GLDevice.objects.get(vDeviceToken=request.GET['tokenDevice'])
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Device Found : ' + str(request.GET['tokenDevice']) + '')

      if not device.vIsActive:
         error='^DISPOSITIVO^'+ device.vDeviceName +'^DESHABILITADO^DE SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device : ' + str(device.vIsActive) + ' is not active on the system')
         resultJSON['Ticket'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON
      else:
         if device.vPrintLocal:
            resultJSON['InventoryKind'] = 'Terminal'
         else:
            resultJSON['InventoryKind'] = ''
            
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['Inventory'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON
   except GLDevice.DoesNotExist:
      error='^EL DISPOSITIVO^' + str(request.GET['tokenDevice']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device : ' + str(request.GET['tokenDevice']) + ' does not exist on system')
      resultJSON['Inventory'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON

   if len(request.GET['lsUser'])>0:
      try:
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
         localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
      except GLUser.DoesNotExist:
         error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
         resultJSON['Inventory'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   localDispatcherId= None
   localDriverId= None

   if len(request.GET['dispatcher'].lstrip("0"))>0:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating dispatcher in station ' + str(localStationId))
      try:
         localDispatcherId= GLUser.objects.get(vPassAccess=request.GET['dispatcher'], vKind='DESPACHADOR', vStationId= localStationId)
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Dispatcher is OK {' + localDispatcherId.vName + ' ' + localDispatcherId.vLastname + '}' )
         resultJSON['Dispatcher']= localDispatcherId.vName + ' ' + localDispatcherId.vLastname
      except GLUser.DoesNotExist:
         error='^EL DESPACHADOR^ ^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The dispatcher : ' + str(request.GET['dispatcher']) + ' does not exist on system')
         resultJSON['Inventory'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Sending ticket request to server: ' + str(localStationId.vStationWHost) + ':' + localStationId.vStationWPort)

   if not localStationId.vStationWHost or not localStationId.vStationWPort:
         error='^ES NECESARIO^ ^CONFIGURAR SERVIDOR^Y PUERTO DE ESTACION'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The server and port need to be configured properly')
         resultJSON['Inventory'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON


   response = askInventoryService(localStationId.vStationWHost, 
                                int(localStationId.vStationWPort), 
                                request.GET['tokenDevice'],
                                request.GET['dispatcher'],
                                device.vDeviceName
                                )


   response=str(response)
   if "InventoryOK" in str(response):

      resultJSON['Inventory'] = 'OK'
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Response received by station : ' + str(response))
      [resultJSON["InfoInventory"],resultJSON["DateTicket"]] = split_tank(response)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Inventory was successfull  ')
      


   else:
      resultJSON['Inventory'] = 'ERROR'
      resultJSON['ERROR'] = str(response)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Inventory throws the next error : ' + str(response))

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END inventory')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#

@json_response
def billing(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')

   global currentTransaction
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START billing')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'New Billing Request ' + VERSION)
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'USER            : [' + request.GET['lsUser']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PASS            : [' + request.GET['lsPass']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'STATIONID       : [' + request.GET['stationId']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PUMP            : [' + request.GET['pump']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'RFC             : [' + request.GET['rfc']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PAYMENT KIND    : [' + request.GET['paymentKind']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'CFDI USE        : [' + request.GET['cfdiUse']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PROOF KIND      : [' + request.GET['proofKind']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'RELATION KIND   : [' + request.GET['relationKind']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'BANK            : [' + request.GET['bank']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'ACCOUNT         : [' + request.GET['account']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'DISPATCHER      : [' + request.GET['dispatcher']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'ISLAND          : [' + request.GET['island']+ ']')


   currentTransaction+=1

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['Billing'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON

   if len(request.GET['lsUser'])>0:
      try:
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
         localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
      except GLUser.DoesNotExist:
         error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
         resultJSON['Billing'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   try:
      device  = GLDevice.objects.get(vDeviceToken=request.GET['tokenDevice'])
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Device Found : ' + str(request.GET['tokenDevice']) + '')

      if not device.vIsActive:
         error='^DISPOSITIVO^'+ device.vDeviceName +'^DESHABILITADO^DE SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device : ' + str(device.vIsActive) + ' is not active on the system')
         resultJSON['Billing'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   except GLDevice.DoesNotExist:
      error='^EL DISPOSITIVO^' + str(request.GET['tokenDevice']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device : ' + str(request.GET['tokenDevice']) + ' does not exist on system')
      resultJSON['Ticket'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON


   localDispatcherId= None
   localDriverId= None

   if len(request.GET['dispatcher'])>0:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating dispatcher in station ' + str(localStationId))
      try:
         localDispatcherId= GLUser.objects.get(vPassAccess=request.GET['dispatcher'], vKind='DESPACHADOR', vStationId= localStationId)
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Dispatcher is OK {' + localDispatcherId.vName + ' ' + localDispatcherId.vLastname + '}' )
         resultJSON['Dispatcher']= localDispatcherId.vName + ' ' + localDispatcherId.vLastname
      except GLUser.DoesNotExist:
         error='^EL DESPACHADOR^ ^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The dispatcher : ' + str(request.GET['dispatcher']) + ' does not exist on system')
         resultJSON['Billing'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Sending billing request to server: ' + str(localStationId.vStationWHost) + ':' + localStationId.vStationWPort)


   if not localStationId.vStationWHost or not localStationId.vStationWPort:
         error='^ES NECESARIO^ ^CONFIGURAR SERVIDOR^Y PUERTO DE ESTACION'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The server and port need to be configured properly')
         resultJSON['Billing'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Max Time configured on station : ' + str(localStationId.vPrintTime) + '')

   response = askBillingService(localStationId.vStationWHost, 
                                int(localStationId.vStationWPort), 
                                request.GET['pump'],
                                request.GET['rfc'],
                                request.GET['paymentKind'],
                                request.GET['cfdiUse'],
                                request.GET['proofKind'],
                                request.GET['relationKind'],
                                request.GET['bank'],
                                request.GET['account'],
                                request.GET['tokenDevice'],
                                request.GET['dispatcher'],
                                request.GET['island'],
                                str(localStationId.vPrintTime)
                                )



   response=str(response)
   if "BillingOK" in str(response):

      billingId = response.split("_")[1]
      resultJSON['Billing'] = 'OK'
      resultJSON['BillingId'] = billingId
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Response received by station : ' + str(response))
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Billing was successfull  ')
      logBilling(currentTransaction, "OK", request.GET['tokenDevice'],request.GET['lsUser'],request.GET['stationId'],request.GET['pump'] ,request.GET['rfc'], billingId)

   else:
      resultJSON['Billing'] = 'ERROR'
      resultJSON['ERROR'] = str(response)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Billing throws the next error : ' + str(response))
      logBilling(currentTransaction, "ERROR", request.GET['tokenDevice'],request.GET['lsUser'],request.GET['stationId'],request.GET['pump'] ,request.GET['rfc'],'')

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END billing')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#

@json_response
def cancel(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')

   global currentTransaction
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START cancel')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'New Cancel Request ' + VERSION)
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'USER            : [' + request.GET['lsUser']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PASS            : [' + request.GET['lsPass']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'STATIONID       : [' + request.GET['stationId']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PUMP            : [' + request.GET['pump']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'DISPATCHER      : [' + request.GET['dispatcher']+ ']')


   currentTransaction+=1

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['Cancel'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON

   if len(request.GET['lsUser'])>0:
      try:
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
         localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
      except GLUser.DoesNotExist:
         error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
         resultJSON['Cancel'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   localDispatcherId= None
   localDriverId= None

   if len(request.GET['dispatcher'])>0:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating dispatcher in station ' + str(localStationId))
      try:
         localDispatcherId= GLUser.objects.get(vPassAccess=request.GET['dispatcher'], vKind='DESPACHADOR', vStationId= localStationId)
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Dispatcher is OK {' + localDispatcherId.vName + ' ' + localDispatcherId.vLastname + '}' )
         resultJSON['Dispatcher']= localDispatcherId.vName + ' ' + localDispatcherId.vLastname
      except GLUser.DoesNotExist:
         error='^EL DESPACHADOR^ ^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The dispatcher : ' + str(request.GET['dispatcher']) + ' does not exist on system')
         resultJSON['Cancel'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Sending ticket request to server: ' + str(localStationId.vStationWHost) + ':' + localStationId.vStationWPort)

   if not localStationId.vStationWHost or not localStationId.vStationWPort:
         error='^ES NECESARIO^ ^CONFIGURAR SERVIDOR^Y PUERTO DE ESTACION'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The server and port need to be configured properly')
         resultJSON['Cancel'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON


   response = askCancelService(localStationId.vStationWHost, 
                                int(localStationId.vStationWPort), 
                                request.GET['pump'],
                                request.GET['tokenDevice'],
                                request.GET['dispatcher'],
                                "",
                                )


   response=str(response)
   if "CancelOK" in str(response):

      resultJSON['Cancel'] = 'OK'
      resultJSON['PresetMessage'] = 'Se ha cancelado el preset satisfactoriamente'
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Response received by station : ' + response)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Cancel Preset was successfull  ')

   else:
      resultJSON['Cancel'] = 'ERROR'
      resultJSON['ERROR'] = response
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Cancel Preset throws the next error : ' + response)

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END cancel')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#

@json_response
def preset(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')

   global currentTransaction
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START preset')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'New Preset Request ' + VERSION)
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'USER            : [' + request.GET['lsUser']      + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PASS            : [' + request.GET['lsPass']      + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice'] + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'STATIONID       : [' + request.GET['stationId']   + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'DISPATCHER      : [' + request.GET['dispatcher']  + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PUMP            : [' + request.GET['pump']        + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PRODUCT         : [' + request.GET['product']     + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'KIND            : [' + request.GET['kind']        + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'AMOUNT          : [' + request.GET['amount']      + ']')


   currentTransaction+=1

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['Preset'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON

   if len(request.GET['lsUser'])>0:
      try:
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
         localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
      except GLUser.DoesNotExist:
         error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
         resultJSON['Preset'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   localDispatcherId= None
   localDriverId= None

   if len(request.GET['dispatcher'])>0:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating dispatcher in station ' + str(localStationId))
      try:
         localDispatcherId= GLUser.objects.get(vPassAccess=request.GET['dispatcher'], vKind='DESPACHADOR', vStationId= localStationId)
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Dispatcher is OK {' + localDispatcherId.vName + ' ' + localDispatcherId.vLastname + '}' )
         resultJSON['Dispatcher']= localDispatcherId.vName + ' ' + localDispatcherId.vLastname
      except GLUser.DoesNotExist:
         error='^EL DESPACHADOR^ ^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The dispatcher : ' + str(request.GET['dispatcher']) + ' does not exist on system')
         resultJSON['Preset'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Sending ticket request to server: ' + str(localStationId.vStationWHost) + ':' + localStationId.vStationWPort)

   if not localStationId.vStationWHost or not localStationId.vStationWPort:
         error='^ES NECESARIO^ ^CONFIGURAR SERVIDOR^Y PUERTO DE ESTACION'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The server and port need to be configured properly')
         resultJSON['Preset'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON


   response = sendPresetService(localStationId.vStationWHost, 
                                int(localStationId.vStationWPort), 
                                request.GET['pump'],
                                request.GET['tokenDevice'],
                                request.GET['dispatcher'],
                                "",
                                request.GET['product'],
                                request.GET['kind'],
                                request.GET['amount'],
                                )


   response=str(response)
   if "PresetOK" in response:

      resultJSON['Preset'] = 'OK'
      resultJSON['Preset_Pump']    = request.GET['pump']
      resultJSON['Preset_Amount']  = request.GET['amount']
      resultJSON['Preset_Product'] = request.GET['product']
      resultJSON['Preset_Kind']    = request.GET['kind']
      resultJSON['PresetMessage'] = 'Se ha enviado el preset satisfactoriamente'
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Response received by station : ' + response)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Preset was successfull  ')

   else:
      resultJSON['Preset'] = 'ERROR'
      resultJSON['ERROR'] = response
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Preset throws the next error : ' + response)

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END preset')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#



#CRUD

@json_response
def getCustomers(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getCustomers')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GetCustomers ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('userRFC') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER RFC    : [' + request.GET['userRFC']+ ']')

   if request.GET.get('userService') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER SERVICE    : [' + request.GET['userService']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetCustomers'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetCustomers'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Getting all Customers from station  '  + str(request.GET['currentStation']))

   resultJSON['Customers']= commonGetCustomers(request.GET['currentStation'], request.GET['userRFC'])
   resultJSON['GetCustomers'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getCustomers')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def getGroups(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getGroups')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GetGroups ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetGroups'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetGroups'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Getting all Groups  ')

   resultJSON['Groups']= commonGetGroups(None)
   resultJSON['GetGroups'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getGroups')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def getStations(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getStations')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GetStations ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetStations'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetStations'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Getting all Stations  ')

   resultJSON['Stations']= commonGetStations(None)
   resultJSON['GetStations'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getStations')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def getUsers(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getUsers')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GetUsers ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('userRFC') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER RFC    : [' + request.GET['userRFC']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetUsers'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetUsers'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Getting all Users  ')

   resultJSON['Users']= commonGetUsers(request.GET['currentStation'],None,request.GET['userRFC'])
   resultJSON['GetUsers'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getUsers')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def getDevices(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getDevices')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GetDevices ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentUserId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT USER ID : [' + request.GET['currentUserId']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetDevices'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetDevices'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Getting all Devices  ')

   resultJSON['Devices']= commonDevices(request.GET['currentUserId'],None)
   resultJSON['GetDevices'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getDevices')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#




@json_response
def getGroup(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getGroup')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GetGroup ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('groupDesc') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'GROUP DESC      : [' + request.GET['groupDesc']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetGroup'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetGroup'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Getting the  GroupDesc ' +  str(request.GET['groupDesc']))

   resultJSON['Group']= commonGetGroups(request.GET['groupDesc'])
   resultJSON['GetGroup'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getGroup')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def getStation(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getStation')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GetStation ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetStation'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetStation'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Getting all Stations  ')

   resultJSON['Station']= commonGetStations(request.GET['currentStation'])
   resultJSON['GetStation'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getStations')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def getUser(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getUser')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GetUser ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('userId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER ID         : [' + request.GET['userId']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetUsers'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetUsers'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Getting all Users  ')

   resultJSON['User']= commonGetUsers(request.GET['currentStation'], request.GET['userId'],None)
   resultJSON['GetUser'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getUser')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def getDevice(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getDevice')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GetDevice ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentUserId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT USER ID : [' + request.GET['currentUserId']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('deviceName') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE NAME     : [' + request.GET['deviceName']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetDevices'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetDevices'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Getting the Device:' + str(request.GET['deviceName']))

   resultJSON['Device']= commonDevices(None,request.GET['deviceName'],None)
   resultJSON['GetDevice'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getDevice')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#


@json_response
def resend(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START resend')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New Resend ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('customerId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CUSTOMER ID     : [' + request.GET['customerId']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['Resend'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['Resend'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Resending the QR to customer: ' +  str(request.GET['customerId']))


   try:
      currentCustomer = GLCustomer.objects.get(vCustomerId= request.GET['customerId'])
      logger.info('LOG_ID<' + currentTransaction + '> '+'Generating the QR with RFC: ' +  str(currentCustomer.vRFC))
      
      if currentCustomer.vMail:
         sendObj = GLSendQR(currentCustomer.vRFC)
         sendObj.setMail(currentCustomer.vMail)
         sendObj.setBusinessName(currentCustomer.vBusinessName)
         response = sendObj.sendMail()
         if not response:
            error='^NO SE PUDO ENVIAR^CORREO ELECTRONICO^ ^'
            logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The mail could not be sent')
            resultJSON['Resend'] = 'ERROR'
            resultJSON['ErrorMessage'] = error
            return resultJSON
      else:
         error='^NO SE PUEDE^ENVIAR QR^PORQ EL CORREO CONFIGURADO^ ES INVALIDO'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The configured mail is invalid')
         resultJSON['Resend'] = 'ERROR'
         resultJSON['ErrorMessage'] = error
         return resultJSON

   except GLCustomer.DoesNotExist:
      error='^CLIENTE CON ID^' + str(request.GET['customerId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The customer : ' + str(request.GET['customerId']) + ' does not exist on system')
      resultJSON['Resend'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   resultJSON['Resend'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END resend')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def removeGroup(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START removeGroup')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New RemoveGroup ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('groupId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'GROUP ID      : [' + request.GET['groupId']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['RemoveGroup'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['RemoveGroup'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Removing the  groupId ' +  str(request.GET['groupId']))


   try:
      currentGroup = GLStationGroup.objects.get(vStationGroupId= request.GET['groupId'])
      currentGroup.delete()
      logger.info('LOG_ID<' + currentTransaction + '> '+'The group with id : ' + request.GET['groupId'] + ' has been removed successfully')

   except GLStationGroup.DoesNotExist:
      error='^GRUPO CON ID^' + str(request.GET['groupId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The group : ' + str(request.GET['groupId']) + ' does not exist on system')
      resultJSON['RemoveGroup'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   resultJSON['RemoveGroup'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getGroup')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def removeStation(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START removeStation')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New RemoveStation ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('vStationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION ID      : [' + request.GET['vStationId']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['RemoveStation'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['RemoveStation'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Removing the  stationId ' +  str(request.GET['vStationId']))


   try:
      currentStation = GLStation.objects.get(vStationId= request.GET['vStationId'])
      currentStation.delete()
      logger.info('LOG_ID<' + currentTransaction + '> '+'The station with id : ' + request.GET['stationId'] + ' has been removed successfully')

   except GLStation.DoesNotExist:
      error='^ESTACION CON ID^' + str(request.GET['vStationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['vStationId']) + ' does not exist on system')
      resultJSON['RemoveStation'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   resultJSON['RemoveStation'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getStation')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def removeUser(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START removeUser')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New RemoveUser ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('userId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER ID         : [' + request.GET['userId']+ ']')

   if not request.GET.get('userAccess') is None:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER ACCESS     : [' + request.GET['userAccess']+ ']')

   if not request.GET.get('customerRFC') is None:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CUSTOMER RFC    : [' + request.GET['customerRFC']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['RemoveStation'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')

      if len(request.GET['customerRFC'])>0:
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User with RFC with userAccess: ' + str(request.GET['userAccess'])+ ' and station : ' + str(localStationId) + ' and RFC: ' + request.GET['customerRFC']) 
         localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['userAccess'] , vStationId= localStationId, vRFC=request.GET['customerRFC'] )
      else:
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User without RFC')
         localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['RemoveUser'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Removing the userId ' +  str(request.GET['userId']))

   

   try:
      if not request.GET.get('userAccess') is None:
         currentUser = GLUser.objects.get(vUserAccess__iexact= request.GET['userAccess'], vRFC=request.GET['customerRFC'])
      else:
         currentUser = GLUser.objects.get(vUserId= request.GET['userId'])
      
      
      currentUser.delete()
      logger.info('LOG_ID<' + currentTransaction + '> '+'The user with id : ' + request.GET['userId'] + ' has been removed successfully')

   except GLUser.DoesNotExist:
      error='^USUARIO CON ID^' + str(request.GET['userId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['userId']) + ' does not exist on system')
      resultJSON['RemoveUser'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   resultJSON['RemoveUser'] = 'OK'
   resultJSON['Id'] = request.GET['userId']

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getUser')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def removeDevice(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START removeDevice')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New RemoveDevice ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('deviceId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE ID       : [' + request.GET['deviceId']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['RemoveStation'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['RemoveDevice'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Removing the deviceId ' +  str(request.GET['deviceId']))


   try:
      currentDevice = GLDevice.objects.get(vDeviceId= request.GET['deviceId'])
      currentDevice.delete()
      logger.info('LOG_ID<' + currentTransaction + '> '+'The device with id : ' + request.GET['deviceId'] + ' has been removed successfully')

   except GLDevice.DoesNotExist:
      error='^DISPOSITIVO CON ID^' + str(request.GET['deviceId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device : ' + str(request.GET['deviceId']) + ' does not exist on system')
      resultJSON['RemoveDevice'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   resultJSON['RemoveDevice'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getDevice')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#





@json_response
def updateGroup(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START updateGroup')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New UpdateGroup ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('groupId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'GROUP ID      : [' + request.GET['groupId']+ ']')

   if request.GET.get('groupDesc') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'GROUP DESC      : [' + request.GET['groupDesc']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['UpdateGroup'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['UpdateGroup'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Updating the  GroupId ' +  str(request.GET['groupId']))

   try:
      currentGroup= GLStationGroup.objects.get(vStationGroupDesc=request.GET['groupDesc'])
      error='^ERROR, EL GRUPO^ ' + str(request.GET['groupDesc']) + '^YA EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The group : ' + str(request.GET['groupDesc']) + ' is already on system')
      resultJSON['UpdateGroup'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON
   except GLStationGroup.DoesNotExist:
      try:

         currentGroup = GLStationGroup.objects.get(vStationGroupId= request.GET['groupId'])
         currentGroup.vStationGroupDesc= request.GET['groupDesc']

         currentGroup.save()
         logger.info('LOG_ID<' + currentTransaction + '> '+'The group with id : ' + request.GET['groupId'] + ' has been changed successfully to new group :' +  request.GET['groupDesc'])

      except GLStationGroup.DoesNotExist:
         error='^EL GRUPO CON ID^'+ request.GET['groupId']  +'^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The group with id: ' + str(request.GET['groupId']) + ' does not exist on system')
         resultJSON['UpdateGroup'] = 'ERROR'
         resultJSON['ErrorMessage'] = error
         return resultJSON



   resultJSON['Id'] = request.GET['groupId']
   resultJSON['GroupDesc'] = request.GET['groupDesc']
   resultJSON['GroupName'] = currentGroup.vStationName
   resultJSON['UpdateGroup'] = 'OK'



   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END updateGroup')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def updateStation(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START updateStation')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New UpdateStation ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('vStationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'VSTATION ID      : [' + request.GET['vStationId']+ ']')

   if request.GET.get('stationDesc') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION DESC    : [' + request.GET['stationDesc']+ ']')

   if request.GET.get('stationWHost') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION WHOST      : [' + request.GET['stationWHost']+ ']')

   if request.GET.get('stationLHost') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION LHOST      : [' + request.GET['stationLHost']+ ']')

   if request.GET.get('stationWPort') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION WPORT      : [' + request.GET['stationWPort']+ ']')

   if request.GET.get('stationLPort') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION LPORT      : [' + request.GET['stationLPort']+ ']')

   if request.GET.get('requireDispatcher') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'REQUIRE DISPATCHER : [' + request.GET['requireDispatcher']+ ']')

   if request.GET.get('requireDriver') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'REQUIRE DRIVER     : [' + request.GET['requireDriver']+ ']')

   if request.GET.get('requireAuth') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'REQUIRE AUTH       : [' + request.GET['requireAuth']+ ']')

   if request.GET.get('usePoints') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USE POINTS       : [' + request.GET['usePoints']+ ']')

   if request.GET.get('useFleets') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USE FLEETS       : [' + request.GET['useFleets']+ ']')

   if request.GET.get('useTAE') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USE TAE       : [' + request.GET['useTAE']+ ']')

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['UpdateStation'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['UpdateStation'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Updating the  StationId ' +  str(request.GET['stationId']))

   currentStation = GLStation.objects.get(vStationId= request.GET['vStationId'])

   #if len(request.GET['groupId'])>0:
         #   currentGroup= GLStationGroup.objects.get(vStationGroupId= request.GET['groupId'])
         #else:
         #   currentGroup=None

   currentGroup=None
   if len((request.GET['groupId']).strip())>0:
      if not "None" in request.GET['groupId'] and not "null" in request.GET['groupId']:
         currentGroup= GLStationGroup.objects.get(vStationGroupId= request.GET['groupId'])
         currentStation.vStationGroupId= currentGroup
         resultJSON['StationGroupId'] = currentGroup.vStationGroupId
         resultJSON['StationGroupDesc'] = currentGroup.vStationGroupDesc 
      else:
         currentStation.vStationGroupId= currentGroup
         resultJSON['StationGroupId'] = currentStation.vStationGroupId
   
   

   currentStation.vStationWHost= request.GET['stationWHost']
   currentStation.vStationLHost= request.GET['stationLHost']
   currentStation.vStationWPort= request.GET['stationWPort']
   currentStation.vStationLPort= request.GET['stationLPort']

   #Getting boolean values for flags services
   if request.GET['usePoints'] == 'true':
      #currentStation.vUsePoints= request.GET['usePoints']
      currentStation.vUsePoints= True
   else:   
      #currentStation.vUsePoints= ''
      currentStation.vUsePoints= False

   if request.GET['useFleets'] == 'true':
      #currentStation.vUseFleets= request.GET['useFleets']
      currentStation.vUseFleets= True
   else:   
      #currentStation.vUseFleets= ''
      currentStation.vUseFleets= False

   if request.GET['useTAE'] == 'true':
      #currentStation.vUseTAE= request.GET['useTAE']
      currentStation.vUseTAE= True
   else:   
      #currentStation.vUseTAE= ''
      currentStation.vUseTAE= False
   

   if request.GET['requireDispatcher'] == 'true':
      #currentStation.vRequireDispatcher= request.GET['requireDispatcher']
      currentStation.vRequireDispatcher= True
   else:
      currentStation.vRequireDispatcher= False

   if request.GET['requireDriver'] == 'true':
      #currentStation.vRequireDriver= request.GET['requireDriver']
      currentStation.vRequireDriver= True
   else:
      #currentStation.vRequireDriver= ''
      currentStation.vRequireDriver= False

   if request.GET['requireAuth'] == 'true':
      #currentStation.vRequireAuth= request.GET['requireAuth']
      currentStation.vRequireAuth= True
   else:
      #currentStation.vRequireAuth= ''
      currentStation.vRequireAuth= False

   currentStation.save()
   logger.info('LOG_ID<' + currentTransaction + '> '+'The station with id : ' + request.GET['stationId'] + ' has been changed successfully ')

   resultJSON['Id'] = currentStation.vStationId

   resultJSON['StationDesc'] = currentStation.vStationDesc
   resultJSON['StationWHost'] = currentStation.vStationWHost
   resultJSON['StationLHost'] = currentStation.vStationLHost
   resultJSON['StationWPort'] = currentStation.vStationWPort
   resultJSON['StationLPort'] = currentStation.vStationLPort
   resultJSON['RequireDispatcher'] = currentStation.vRequireDispatcher
   resultJSON['RequireDriver'] = currentStation.vRequireDriver
   resultJSON['RequireAuth'] = currentStation.vRequireAuth
   resultJSON['UsePoints'] = currentStation.vUsePoints
   resultJSON['UseFleets'] = currentStation.vUseFleets
   resultJSON['UseTAE'] = currentStation.vUseTAE

   resultJSON['UpdateStation'] = 'OK'



   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END updateStation')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def updateUser(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START updateUser')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New UpdateUser ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('userId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER ID         : [' + request.GET['userId']+ ']')

   if request.GET.get('vStationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'V STATION ID      : [' + request.GET['vStationId']+ ']')

   if request.GET.get('active') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'ACTIVE          : [' + request.GET['active']+ ']')

   if request.GET.get('kind') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'KIND            : [' + request.GET['kind']+ ']')

   if request.GET.get('name') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'NAME            : [' + request.GET['name']+ ']')

   if request.GET.get('lastname') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'LASTNAME        : [' + request.GET['lastname']+ ']')

   if request.GET.get('age') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'AGE             : [' + request.GET['age']+ ']')

   if request.GET.get('mail') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'MAIL            : [' + request.GET['mail']+ ']')

   if request.GET.get('phone') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PHONE           : [' + request.GET['phone']+ ']')

   if request.GET.get('mobilePhone') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'MOBILE PHONE    : [' + request.GET['mobilePhone']+ ']')

   if request.GET.get('userAccess') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER ACCESS      : [' + request.GET['userAccess']+ ']')

   if request.GET.get('passAccess') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS ACCESS      : [' + request.GET['passAccess']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^(1)LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' (1)The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['UpdateUser'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['UpdateUser'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Updating the  UserId ' +  str(request.GET['userId']))

   try:
      currentStation = GLStation.objects.get(vStationDesc= request.GET['vStationId'])
      currentUser= GLUser.objects.get(vStationId=currentStation , vUserAccess__iexact=request.GET['userAccess'])
      logger.info('LOG_ID<' + currentTransaction + '> '+'User found: ' +  str(currentUser.vUserId))
      if int(currentUser.vUserId)!= int(request.GET['userId']):
         error='^ERROR, EL USUARIO^ ' + str(request.GET['userAccess']) + '^YA EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['userAccess']) + ' is already on system')
         resultJSON['UpdateUser'] = 'ERROR'
         resultJSON['ErrorMessage'] = error
         return resultJSON

      logger.info('LOG_ID<' + currentTransaction + '> '+'All user info OK , getting the user object' )
      currentUser = GLUser.objects.get(  vUserId=request.GET['userId'])

      if currentStation:
         currentUser.vStationId= currentStation

      if len(request.GET['active']):
         currentUser.vActive= request.GET['active']
      else:
         currentUser.vActive=''

      currentUser.vKind= request.GET['kind']
      currentUser.vName= request.GET['name']
      currentUser.vLastname= request.GET['lastname']
      if len(request.GET['age'])==0 :
         currentUser.vAge= "0"
      else:
         currentUser.vAge= request.GET['age']
      currentUser.vMail= request.GET['mail']
      currentUser.vPhone= request.GET['phone']
      currentUser.vMobilePhone= request.GET['mobilePhone']
      currentUser.vUserAccess= request.GET['userAccess']
      currentUser.vPassAccess= request.GET['passAccess']


      currentUser.save()
      logger.info('LOG_ID<' + currentTransaction + '> '+'The user with id : ' + request.GET['userId'] + ' has been changed successfully')

   except GLUser.DoesNotExist:
      try:

         logger.info('LOG_ID<' + currentTransaction + '> '+'All user info OK , getting the user object' )
         currentUser = GLUser.objects.get(  vUserId=request.GET['userId'])

         if currentStation:
            currentUser.vStationId= currentStation

         if len(request.GET['active']):
            currentUser.vActive= request.GET['active']
         else:
            currentUser.vActive=''

         currentUser.vKind= request.GET['kind']
         currentUser.vName= request.GET['name']
         currentUser.vLastname= request.GET['lastname']

         if len(request.GET['age'])==0:
            currentUser.vAge= "0"
         else:
            currentUser.vAge= request.GET['age']

         currentUser.vMail= request.GET['mail']
         currentUser.vPhone= request.GET['phone']
         currentUser.vMobilePhone= request.GET['mobilePhone']
         currentUser.vUserAccess= request.GET['userAccess']
         currentUser.vPassAccess= request.GET['passAccess']


         currentUser.save()
         logger.info('LOG_ID<' + currentTransaction + '> '+'The user with id : ' + request.GET['userId'] + ' has been changed successfully')

      except GLUser.DoesNotExist:
         error='^EL USUARIO CON ID^'+ request.GET['userId']  +'^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user with id: ' + str(request.GET['userId']) + ' does not exist on system')
         resultJSON['UpdateUser'] = 'ERROR'
         resultJSON['ErrorMessage'] = error
         return resultJSON
      except GLStation.DoesNotExist:
         error='^LA ESTACION^' + str(request.GET['vStationId']) + '^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+'(2) The station : ' + str(request.GET['vStationId']) + ' does not exist on system')
         resultJSON['UpdateUser'] = 'ERROR'
         resultJSON['ErrorMessage'] = error
         return resultJSON
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['vStationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' (3)The station : ' + str(request.GET['vStationId']) + ' does not exist on system')
      resultJSON['UpdateUser'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON



   resultJSON['Id'] = request.GET['userId']

   resultJSON['StationId'] = str(currentUser.vStationId)
   resultJSON['Active'] = str(currentUser.vActive)
   resultJSON['IsAdmin'] = str(currentUser.vIsAdmin)
   resultJSON['Kind'] = str(currentUser.vKind)
   resultJSON['Name'] = str(currentUser.vName)
   resultJSON['Lastname'] = str(currentUser.vLastname)
   resultJSON['Age'] = str(currentUser.vAge)
   resultJSON['Mail'] = str(currentUser.vMail)
   resultJSON['Phone'] = str(currentUser.vPhone)
   resultJSON['MobilePhone'] = str(currentUser.vMobilePhone)
   resultJSON['UserAccess'] = str(currentUser.vUserAccess)
   resultJSON['PassAccess'] = str(currentUser.vPassAccess)


   resultJSON['UpdateUser'] = 'OK'

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END updateUser')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def updateDevice(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START updateDevice')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New UpdateDevice ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('deviceId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE ID       : [' + request.GET['deviceId']+ ']')

   if request.GET.get('userId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER ID         : [' + request.GET['userId']+ ']')

   if request.GET.get('userAgent') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER AGENT      : [' + request.GET['userAgent']+ ']')

   if request.GET.get('oldUserAgent') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'OLD USER AGENT  : [' + request.GET['oldUserAgent']+ ']')

   if request.GET.get('ipAddress') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'IP ADDRESS     : [' + request.GET['ipAddress']+ ']')

   if request.GET.get('deviceToken') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE TOKEN     : [' + request.GET['deviceToken']+ ']')

   if request.GET.get('isActive') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'ISACTIVE         : [' + request.GET['isActive']+ ']')

   if request.GET.get('printTicket') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PRINT TICKET     : [' + request.GET['printTicket']+ ']')



   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['UpdateDevice'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['UpdateDevice'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Updating the  DeviceId ' +  str(request.GET['deviceId']))

   try:
      currentDevice= GLDevice.objects.get(vDeviceName=request.GET['deviceName'])
      error='^ERROR, EL DISPOSITIVO^ ' + str(request.GET['deviceName']) + '^YA EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device : ' + str(request.GET['deviceName']) + ' is already on system')
      resultJSON['UpdateDevice'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON
   except GLDevice.DoesNotExist:
      try:

         currentUser = GLUser.objects.get(vUserId= request.GET['userId'])
         currentDevice = GLDevice.objects.get(vDeviceId= request.GET['deviceId'])
         if currentUser:
            currentUser.vUserId= currentUser

         currentDevice.vUserAgent    = request.GET['userAgent']
         currentDevice.vOldUserAgent = request.GET['oldUserAgent']
         currentDevice.vIPAddress    = request.GET['ipAddress']
         currentDevice.vDeviceToken  = request.GET['deviceToken']
         currentDevice.vIsActive     = request.GET['isActive']
         currentDevice.vPrintTicket  = request.GET['printTicket']
         currentDevice.vPrintLocal   = True

         currentDevice.save()
         logger.info('LOG_ID<' + currentTransaction + '> '+'The device with id : ' + request.GET['deviceId'] + ' has been changed')

      except GLDevice.DoesNotExist:
         error='^EL DISPOSITIVO CON ID^'+ request.GET['deviceId']  +'^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device with id: ' + str(request.GET['deviceId']) + ' does not exist on system')
         resultJSON['UpdateDevice'] = 'ERROR'
         resultJSON['ErrorMessage'] = error
         return resultJSON
      except GLUser.DoesNotExist:
         error='^EL USUARIO CON ID^'+ request.GET['userId']  +'^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user with id: ' + str(request.GET['userId']) + ' does not exist on system')
         resultJSON['UpdateDevice'] = 'ERROR'
         resultJSON['ErrorMessage'] = error
         return resultJSON



   resultJSON['Id'] = request.GET['deviceId']

   resultJSON['UserId'] = currentDevice.vUserId
   resultJSON['DeviceName'] = currentDevice.vDeviceName
   resultJSON['UserAgent'] = currentDevice.vUserAgent
   resultJSON['OldUserAgent'] = currentDevice.vOldUserAgent
   resultJSON['IPAddress'] = currentDevice.vIPAddress
   resultJSON['DeviceToken'] = currentDevice.vDeviceToken
   resultJSON['IsActive'] = currentDevice.vIsActive
   resultJSON['PrintTicket'] = currentDevice.vPrintTicket

   resultJSON['UpdateDevice'] = 'OK'



   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END updateDevice')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#




@json_response
def addCustomer(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START addCustomer')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New AddCustomer ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('vStationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'V STATION ID      : [' + request.GET['vStationId']+ ']')

   if request.GET.get('businessName') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'BUSINESS NAME      : [' + request.GET['businessName']+ ']')

   if request.GET.get('commercialName') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'COMMERCIAL NAME      : [' + request.GET['commercialName']+ ']')

   if request.GET.get('rfc') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'RFC      : [' + request.GET['rfc']+ ']')

   if request.GET.get('status') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATUS      : [' + request.GET['status']+ ']')

   if request.GET.get('mail') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'MAIL      : [' + request.GET['mail']+ ']')

   if request.GET.get('accountBank') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'ACCOUNT BANK      : [' + request.GET['accountBank']+ ']')

   if request.GET.get('bank') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'BANK      : [' + request.GET['bank']+ ']')

   if request.GET.get('street') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STREET      : [' + request.GET['street']+ ']')

   if request.GET.get('externalNumber') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'EXTERNAL NUMBER      : [' + request.GET['externalNumber']+ ']')

   if request.GET.get('internalNumber') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'INTERNAL NUMBER      : [' + request.GET['internalNumber']+ ']')

   if request.GET.get('colony') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'COLONY      : [' + request.GET['colony']+ ']')

   if request.GET.get('location') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'LOCATION      : [' + request.GET['location']+ ']')

   if request.GET.get('reference') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'REFERENCE      : [' + request.GET['reference']+ ']')

   if request.GET.get('town') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOWN      : [' + request.GET['town']+ ']')

   if request.GET.get('state') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATE      : [' + request.GET['state']+ ']')

   if request.GET.get('cp') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CP      : [' + request.GET['cp']+ ']')

   if request.GET.get('phone') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PHONE      : [' + request.GET['phone']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['AddCustomer'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['AddCustomer'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Creating the  Customer ')

   try:
      currentCustomer= GLCustomer.objects.get(vRFC=request.GET['rfc'])
      error='^ERROR, EL CLIENTE^ ' + str(request.GET['rfc']) + '^YA EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The customer : ' + str(request.GET['rfc']) + ' is already on system')
      resultJSON['AddCustomer'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   except GLCustomer.DoesNotExist:

      currentCustomer = GLCustomer()

      currentStation = GLStation.objects.get(vStationDesc= request.GET['vStationId'])

      currentCustomer.vStationId = currentStation
      currentCustomer.vBusinessName = request.GET['businessName']
      currentCustomer.vCommercialName = request.GET['commercialName']
      currentCustomer.vRFC = request.GET['rfc']
      currentCustomer.vCreationDate = datetime.datetime.now()
      if len(request.GET['status'])>0:
         currentCustomer.vStatus = True
      else:
         currentCustomer.vStatus= False
      currentCustomer.vKind = 'CONTADO'
      currentCustomer.vMail =str(request.GET['mail'])
      currentCustomer.vAccountBank = str(request.GET['accountBank'])
      currentCustomer.vBank = str(request.GET['bank'])
      currentCustomer.vStreet = str(request.GET['street'])
      currentCustomer.vExternalNumber = str(request.GET['externalNumber'])
      currentCustomer.vInternalNumber = str(request.GET['internalNumber'])
      currentCustomer.vColony = str(request.GET['colony'])
      currentCustomer.vLocation = str(request.GET['location'])
      currentCustomer.vReference = str(request.GET['reference'])
      currentCustomer.vTown = str(request.GET['town'])
      currentCustomer.vState = str(request.GET['state'])
      currentCustomer.vCountry = str('Mexico')
      currentCustomer.vCP = str(request.GET['cp'])
      currentCustomer.vPhone = str(request.GET['phone'])

      currentCustomer.save()

      logger.info('LOG_ID<' + currentTransaction + '> '+'The customer with id : ' + str(currentCustomer.vCustomerId) + ' has been created successfully')



   resultJSON['Id'] = currentCustomer.vCustomerId

   resultJSON['StationId']= str(currentCustomer.vStationId.vStationDesc)
   resultJSON['BusinessName']= str(currentCustomer.vBusinessName)
   resultJSON['CommercialName']= str(currentCustomer.vCommercialName)
   resultJSON['RFC']= str(currentCustomer.vRFC)
   resultJSON['CreationDate']= str(currentCustomer.vCreationDate.strftime('%d/%m/%Y %H:%M:%S'))
   resultJSON['Status']= str(currentCustomer.vStatus)
   resultJSON['Kind']= str(currentCustomer.vKind)
   resultJSON['Mail']= str(currentCustomer.vMail)
   resultJSON['AccountBank']= str(currentCustomer.vAccountBank)
   resultJSON['Bank']= str(currentCustomer.vBank)
   resultJSON['Street']= str(currentCustomer.vStreet)
   resultJSON['ExternalNumber']= str(currentCustomer.vExternalNumber)
   resultJSON['InternalNumber']= str(currentCustomer.vInternalNumber)
   resultJSON['Colony']= str(currentCustomer.vColony)
   resultJSON['Location']= str(currentCustomer.vLocation)
   resultJSON['Reference']= str(currentCustomer.vReference)
   resultJSON['Town']= str(currentCustomer.vTown)
   resultJSON['State']= str(currentCustomer.vState)
   resultJSON['Country']= str(currentCustomer.vCountry)
   resultJSON['CP']= str(currentCustomer.vCP)
   resultJSON['Phone']= str(currentCustomer.vPhone)

   resultJSON['AddCustomer'] = 'OK'



   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END addCustomer')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def addGroup(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START addGroup')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New AddGroup ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('groupName') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'GROUP NAME      : [' + request.GET['groupName']+ ']')

   if request.GET.get('groupDesc') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'GROUP DESC      : [' + request.GET['groupDesc']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['AddGroup'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['AddGroup'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Creating the  GroupName ' +  str(request.GET['groupName']))

   try:
      currentGroup= GLStationGroup.objects.get(vStationName=request.GET['groupName'])
      error='^ERROR, EL GRUPO^ ' + str(request.GET['groupName']) + '^YA EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The group : ' + str(request.GET['groupDesc']) + ' is already on system')
      resultJSON['AddGroup'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   except GLStationGroup.DoesNotExist:

      currentGroup = GLStationGroup()
      currentGroup.vStationName= request.GET['groupName']
      currentGroup.vStationGroupDesc= request.GET['groupDesc']

      currentGroup.save()
      logger.info('LOG_ID<' + currentTransaction + '> '+'The group with id : ' + str(currentGroup.vStationGroupId) + ' has been created successfully')



   resultJSON['Id'] = currentGroup.vStationGroupId
   resultJSON['Group'] = currentGroup.vStationName
   resultJSON['AddGroup'] = 'OK'



   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END addGroup')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def addStation(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START addStation')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New AddStation ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('stationDesc') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION DESC    : [' + request.GET['stationDesc']+ ']')

   if request.GET.get('stationWHost') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION WHOST      : [' + request.GET['stationWHost']+ ']')

   if request.GET.get('stationLHost') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION LHOST      : [' + request.GET['stationLHost']+ ']')

   if request.GET.get('stationWPort') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION WPORT      : [' + request.GET['stationWPort']+ ']')

   if request.GET.get('stationLPort') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION LPORT      : [' + request.GET['stationLPort']+ ']')

   if request.GET.get('requireDispatcher') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'REQUIRE DISPATCHER : [' + request.GET['requireDispatcher']+ ']')

   if request.GET.get('requireDriver') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'REQUIRE DRIVER     : [' + request.GET['requireDriver']+ ']')

   if request.GET.get('requireAuth') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'REQUIRE AUTH       : [' + request.GET['requireAuth']+ ']')

   if request.GET.get('usePoints') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USE POINTS       : [' + request.GET['usePoints']+ ']')

   if request.GET.get('useFleets') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USE FLEETS       : [' + request.GET['useFleets']+ ']')

   if request.GET.get('useTAE') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USE TAE       : [' + request.GET['useTAE']+ ']')   

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['AddStation'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['AddStation'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Updating the  StationId ' +  str(request.GET['stationId']))

   try:
      currentStation= GLStation.objects.get(vStationDesc=request.GET['stationDesc'])
      error='^ERROR, LA ESTACION^ ' + str(request.GET['stationDesc']) + '^YA EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationDesc']) + ' is already on system')
      resultJSON['AddStation'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON
   except GLStation.DoesNotExist:
      try:

         currentStation = GLStation()

         currentGroup=None
         if len((request.GET['groupId']).strip())>0:
            if not "None" in request.GET['groupId'] and not "null" in request.GET['groupId']:
               currentGroup= GLStationGroup.objects.get(vStationGroupId= request.GET['groupId'])

         #if len(request.GET['groupId'])>0:
         #   currentGroup= GLStationGroup.objects.get(vStationGroupId= request.GET['groupId'])
         #else:
         #   currentGroup=None

         currentStation.vStationGroupId= currentGroup

         currentStation.vStationDesc = request.GET['stationDesc']

         currentStation.vStationWHost= request.GET['stationWHost']
         currentStation.vStationLHost= request.GET['stationLHost']
         currentStation.vStationWPort= request.GET['stationWPort']
         currentStation.vStationLPort= request.GET['stationLPort']

         #Getting boolean values for flags services
         if request.GET['usePoints'] == 'true':
            #currentStation.vUsePoints= request.GET['usePoints']
            currentStation.vUsePoints= True
         else:   
            #currentStation.vUsePoints= ''
            currentStation.vUsePoints= False

         if request.GET['useFleets'] == 'true':
            #currentStation.vUseFleets= request.GET['useFleets']
            currentStation.vUseFleets= True
         else:   
            #currentStation.vUseFleets= ''
            currentStation.vUseFleets= False

         if request.GET['useTAE'] == 'true':
            #currentStation.vUseTAE= request.GET['useTAE']
            currentStation.vUseTAE= True
         else:   
            #currentStation.vUseTAE= ''
            currentStation.vUseTAE= False
         

         if request.GET['requireDispatcher'] == 'true':
            #currentStation.vRequireDispatcher= request.GET['requireDispatcher']
            currentStation.vRequireDispatcher= True
         else:
            currentStation.vRequireDispatcher= False

         if request.GET['requireDriver'] == 'true':
            #currentStation.vRequireDriver= request.GET['requireDriver']
            currentStation.vRequireDriver= True
         else:
            #currentStation.vRequireDriver= ''
            currentStation.vRequireDriver= False

         if request.GET['requireAuth'] == 'true':
            #currentStation.vRequireAuth= request.GET['requireAuth']
            currentStation.vRequireAuth= True
         else:
            #currentStation.vRequireAuth= ''
            currentStation.vRequireAuth= False

         try:
            currentStation.save()
         except ValueError as e:
            logger.error('LOG_ID<' + currentTransaction + '> '+'It seems to be a bug')
            error='Error guardando la estacion, revisar el modulo ' + str(e)
            resultJSON['AddStation'] = 'ERROR'
            resultJSON['ErrorMessage'] = error
            return resultJSON
         logger.info('LOG_ID<' + currentTransaction + '> '+'The station with id : ' + str(currentStation.vStationId) + ' has been created successfully ')

      except GLStationGroup.DoesNotExist:
         error='^EL GRUPO CON ID^'+ request.GET['groupId']  +'^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The group with id: ' + str(request.GET['groupId']) + ' does not exist on system')
         resultJSON['AddStation'] = 'ERROR'
         resultJSON['ErrorMessage'] = error
         return resultJSON


   resultJSON['Id'] = str(currentStation.vStationId)
   resultJSON['AddStation'] = 'OK'



   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END addStation')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def addUser(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START addUser')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New AddUser ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('vStationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'V STATION ID      : [' + request.GET['vStationId']+ ']')

   if request.GET.get('active') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'ACTIVE          : [' + request.GET['active']+ ']')

   if request.GET.get('kind') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'KIND            : [' + request.GET['kind']+ ']')

   if request.GET.get('name') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'NAME            : [' + request.GET['name']+ ']')

   if request.GET.get('lastname') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'LASTNAME        : [' + request.GET['lastname']+ ']')

   if request.GET.get('age') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'AGE             : [' + request.GET['age']+ ']')

   if request.GET.get('mail') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'MAIL            : [' + request.GET['mail']+ ']')

   if request.GET.get('phone') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PHONE           : [' + request.GET['phone']+ ']')

   if request.GET.get('mobilePhone') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'MOBILE PHONE    : [' + request.GET['mobilePhone']+ ']')

   if request.GET.get('userAccess') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER ACCESS      : [' + request.GET['userAccess']+ ']')

   if request.GET.get('passAccess') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS ACCESS      : [' + request.GET['passAccess']+ ']')

   if request.GET.get('rfc') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'RFC      : [' + request.GET['rfc']+ ']')

   if request.GET.get('isAdmin') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'IS ADMIN         : [' + request.GET['isAdmin']+ ']')


   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['AddUser'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   #try:
   #   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
   #   localUserId= GLUser.objects.get(vUserAccess=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
   #   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   #except GLUser.DoesNotExist:
   #   error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
   #   logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
   #   resultJSON['AddUser'] = 'ERROR'
   #   resultJSON['ErrorMessage'] = error
   #   return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Creating new user ')

   try:
      currentStation = GLStation.objects.get(vStationDesc= request.GET['vStationId'])
      currentUser= GLUser.objects.get(vStationId=currentStation , vUserAccess__iexact=request.GET['userAccess'])
      error='^ERROR, EL USUARIO^ ' + str(request.GET['userAccess']) + '^YA EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['userAccess']) + ' is already on system')
      resultJSON['AddUser'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   except GLUser.DoesNotExist:
      try:

         currentUser= GLUser.objects.filter(vStationId=currentStation , vPassAccess=request.GET['passAccess'])
         if currentUser:
            currentUser= currentUser[0]
            error='^ERROR, EL PASSWORD^ ' + str(request.GET['passAccess']) + '^YA EXISTE^EN EL SISTEMA'
            logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The password : ' + str(request.GET['passAccess']) + ' is already on system')
            resultJSON['AddUser'] = 'ERROR'
            resultJSON['ErrorMessage'] = error
            return resultJSON

         currentUser = GLUser()

         if currentStation:
            currentUser.vStationId= currentStation

         if len(request.GET['active']):
            currentUser.vActive= request.GET['active']
         else:
            currentUser.vActive=''

         currentUser.vKind= request.GET['kind']
         currentUser.vName= request.GET['name']
         currentUser.vLastname= request.GET['lastname']
         if len(request.GET['age'])==0:
            currentUser.vAge= "0"
         else:
            currentUser.vAge= request.GET['age']
         currentUser.vMail= request.GET['mail']
         currentUser.vPhone= request.GET['phone']
         currentUser.vMobilePhone= request.GET['mobilePhone']
         currentUser.vUserAccess= request.GET['userAccess']
         currentUser.vPassAccess= request.GET['passAccess']
         currentUser.vRFC= request.GET['rfc']


         if len(request.GET['isAdmin']):
            currentUser.vIsAdmin= request.GET['isAdmin']
         else:
            currentUser.vIsAdmin= ''

         try:
            currentUser.save()
         except ValueError as e:
            logger.error('LOG_ID<' + currentTransaction + '> '+'It seems to be a bug')
            error='Error guardando el usuario, revisar el modulo ' + str(e)
            resultJSON['AddUser'] = 'ERROR'
            resultJSON['ErrorMessage'] = error
            return resultJSON


         logger.info('LOG_ID<' + currentTransaction + '> '+'The user with id : ' + str(currentUser.vUserId) + ' has been changed successfully')

      except GLStation.DoesNotExist:
         error='^LA ESTACION^' + str(request.GET['vStationId']) + '^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['vStationId']) + ' does not exist on system')
         resultJSON['AddUser'] = 'ERROR'
         resultJSON['ErrorMessage'] = error
         return resultJSON



   resultJSON['Id'] = currentUser.vUserId
   resultJSON['User'] = str(currentUser.vUserAccess)

   resultJSON['StationId'] =  str(currentUser.vStationId)
   resultJSON['Name'] =  str(currentUser.vName)
   resultJSON['Lastname'] =  str(currentUser.vLastname)
   resultJSON['Age'] =  str(currentUser.vAge)
   resultJSON['Kind'] =  str(currentUser.vKind)
   resultJSON['Mail'] =  str(currentUser.vMail)
   resultJSON['Phone'] =  str(currentUser.vPhone)
   resultJSON['MobilePhone'] =  str(currentUser.vMobilePhone)
   resultJSON['UserAccess'] =  str(currentUser.vUserAccess)
   resultJSON['PassAccess'] =  str(currentUser.vPassAccess)
   resultJSON['Active'] =  str(currentUser.vActive)
   resultJSON['IsAdmin'] =  str(currentUser.vIsAdmin)

   resultJSON['AddUser'] = 'OK'


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END AddUser')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def addDevice(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START addDevice')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New AddDevice ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('currentStation') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CURRENT STATION : [' + request.GET['currentStation']+ ']')

   if request.GET.get('device') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE          : [' + request.GET['device']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('userId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER ID         : [' + request.GET['userId']+ ']')

   if request.GET.get('userAgent') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER AGENT      : [' + request.GET['userAgent']+ ']')

   if request.GET.get('oldUserAgent') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'OLD USER AGENT  : [' + request.GET['oldUserAgent']+ ']')

   if request.GET.get('ipAddress') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'IP ADDRESS     : [' + request.GET['ipAddress']+ ']')

   if request.GET.get('deviceName') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE NAME     : [' + request.GET['deviceName']+ ']')

   if request.GET.get('deviceToken') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'DEVICE TOKEN     : [' + request.GET['deviceToken']+ ']')

   if request.GET.get('isActive') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'ISACTIVE         : [' + request.GET['isActive']+ ']')

   if request.GET.get('printTicket') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PRINT TICKET     : [' + request.GET['printTicket']+ ']')



   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['AddDevice'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   #The user and pass must be on the system as Web User
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['AddDevice'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + currentTransaction + '> '+'Creating a new device 1' )

   try:
      logger.info('LOG_ID<' + currentTransaction + '> '+'Creating a new device 2' )
      currentDevice= GLDevice.objects.get(vDeviceName=request.GET['deviceName'])
      error='^ERROR, EL DISPOSITIVO^ ' + str(request.GET['deviceName']) + '^YA EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device : ' + str(request.GET['deviceName']) + ' is already on system')
      resultJSON['AddDevice'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON
   except GLDevice.DoesNotExist:
      try:

         logger.info('LOG_ID<' + currentTransaction + '> '+'Creating a new device 3' )
         currentUser = GLUser.objects.get(vUserId=request.GET['userId'])
         logger.info('LOG_ID<' + currentTransaction + '> '+'Creating a new device 4' )
         if currentUser:
            currentUser.vUserId= currentUser

         logger.info('LOG_ID<' + currentTransaction + '> '+'Creating a new device 5' )
         currentDevice = GLDevice(
         vDeviceName    = str(request.GET['deviceName']),
         vUserAgent    = str(request.GET['userAgent']),
         vOldUserAgent = str(request.GET['oldUserAgent']),
         vIPAddress    = str(request.GET['ipAddress']),
         vDeviceToken  = str(request.GET['deviceToken']),
         vIsActive     = bool(request.GET['isActive']),
         vPrintTicket  = bool(request.GET['printTicket']))

         logger.info('LOG_ID<' + currentTransaction + '> '+'Creating a new device 6' )
         try:
            currentDevice.save()
         except ValueError as e:
            logger.error('LOG_ID<' + currentTransaction + '> '+'It seems to be a bug')
            error='Error guardando el dispositivo, revisar el modulo ' + str(e)
            resultJSON['AddDevice'] = 'ERROR'
            resultJSON['ErrorMessage'] = error
            return resultJSON
         logger.info('LOG_ID<' + currentTransaction + '> '+'The device with id : ' + str(currentDevice.vDeviceId) + ' has been created')

      except GLUser.DoesNotExist:
         error='^EL USUARIO CON ID^'+ request.GET['userId']  +'^NO EXISTE^EN EL SISTEMA'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user with id: ' + str(request.GET['userId']) + ' does not exist on system')
         resultJSON['AddDevice'] = 'ERROR'
         resultJSON['ErrorMessage'] = error
         return resultJSON



   resultJSON['Id'] = currentDevice.vDeviceId
   resultJSON['Device'] = currentDevice.vDeviceName
   resultJSON['AddDevice'] = 'OK'


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END addDevice')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def validateRFC(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START validateRFC')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New Validate RFC ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')



   if request.GET.get('rfc') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'RFC            : [' + request.GET['rfc']+ ']')

   try:
      currentCustomer = GLCustomer.objects.get(vRFC=request.GET['rfc'])
      resultJSON['ValidateRFC'] = 'OK'
      resultJSON['RFC'] = request.GET['rfc']
      resultJSON['SocialName'] = str(currentCustomer.vBusinessName)
      resultJSON['Mail'] = str(currentCustomer.vMail)
   except GLCustomer.DoesNotExist:
      error='NO EXISTE EL RFC:'+ str(request.GET['rfc'])
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The rfc: ' + str(request.GET['rfc']) + ' does not exist on system')
      resultJSON['ValidateRFC'] = 'DOES_NOT_EXIST'
      resultJSON['RFC'] = request.GET['rfc']
      resultJSON['ErrorMessage'] = error
      return resultJSON

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END validateRFC')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def addWebCustomer(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START addWebCustomer')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New AddWebCustomer ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'USER_AGENT      : [' + request.META['HTTP_USER_AGENT']+ ']') 
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('businessName') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'BUSINESS NAME      : [' + request.GET['businessName']+ ']')

   if request.GET.get('rfc') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'RFC      : [' + request.GET['rfc']+ ']')

   if request.GET.get('mail') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'MAIL      : [' + request.GET['mail']+ ']')

   if request.GET.get('street') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STREET      : [' + request.GET['street']+ ']')

   if request.GET.get('externalNumber') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'EXTERNAL NUMBER      : [' + request.GET['externalNumber']+ ']')

   if request.GET.get('internalNumber') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'INTERNAL NUMBER      : [' + request.GET['internalNumber']+ ']')

   if request.GET.get('colony') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'COLONY      : [' + request.GET['colony']+ ']')

   if request.GET.get('location') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'LOCATION      : [' + request.GET['location']+ ']')

   if request.GET.get('reference') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'REFERENCE      : [' + request.GET['reference']+ ']')

   if request.GET.get('town') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOWN      : [' + request.GET['town']+ ']')

   if request.GET.get('state') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATE      : [' + request.GET['state']+ ']')

   if request.GET.get('cp') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'CP      : [' + request.GET['cp']+ ']')

   if request.GET.get('phone') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PHONE      : [' + request.GET['phone']+ ']')


   logger.info('LOG_ID<' + currentTransaction + '> '+'Creating the  Customer ')

   try:
      currentCustomer= GLCustomer.objects.get(vRFC=request.GET['rfc'])
      error='^ERROR, EL CLIENTE^ ' + str(request.GET['rfc']) + '^YA EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The customer : ' + str(request.GET['rfc']) + ' is already on system')
      resultJSON['AddWebCustomer'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   except GLCustomer.DoesNotExist:

      currentCustomer = GLCustomer()

      currentCustomer.vBusinessName = request.GET['businessName']
      currentCustomer.vCommercialName = request.GET['businessName']
      currentCustomer.vRFC = request.GET['rfc']
      currentCustomer.vCreationDate = datetime.datetime.now()
      currentCustomer.vStatus = True
      currentCustomer.vKind = 'CONTADO'
      currentCustomer.vMail =str(request.GET['mail'])
      currentCustomer.vAccountBank = ""
      currentCustomer.vBank = ""
      currentCustomer.vStreet = str(request.GET['street'])
      currentCustomer.vExternalNumber = str(request.GET['externalNumber'])
      currentCustomer.vInternalNumber = str(request.GET['internalNumber'])
      currentCustomer.vColony = str(request.GET['colony'])
      currentCustomer.vLocation = str(request.GET['location'])
      currentCustomer.vReference = str(request.GET['reference'])
      currentCustomer.vTown = str(request.GET['town'])
      currentCustomer.vState = str(request.GET['state'])
      currentCustomer.vCountry = str('Mexico')
      currentCustomer.vCP = str(request.GET['cp'])
      currentCustomer.vPhone = str(request.GET['phone'])

      currentCustomer.save()

      logger.info('LOG_ID<' + currentTransaction + '> '+'The customer with id : ' + str(currentCustomer.vCustomerId) + ' has been created successfully')



   resultJSON['Id'] = currentCustomer.vCustomerId

   resultJSON['BusinessName']= str(currentCustomer.vBusinessName)
   resultJSON['RFC']= str(currentCustomer.vRFC)
   resultJSON['AddWebCustomer'] = 'OK'



   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END addWebCustomer')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def billingFromWeb(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')

   global currentTransaction
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START billingFromWeb')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'New Billing From Web Request ' + VERSION)
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'STATIONID       : [' + request.GET['stationId']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'RFC             : [' + request.GET['rfc']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'EMAIL           : [' + request.GET['email']+ ']')

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'SALE ID         : [' + request.GET['saleId']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'AMOUNT          : [' + request.GET['amount']+ ']')

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PAYMENT KIND    : [' + request.GET['paymentKind']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'CFDI USE        : [' + request.GET['cfdiUse']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'PROOF KIND      : [' + request.GET['proofKind']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'BANK            : [' + request.GET['bank']+ ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'ACCOUNT         : [' + request.GET['account']+ ']')


   currentTransaction+=1

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['BillingFromWeb'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Sending billing request to server: ' + str(localStationId.vStationWHost) + ':' + localStationId.vStationWPort)


   if not localStationId.vStationWHost or not localStationId.vStationWPort:
         error='^ES NECESARIO^ ^CONFIGURAR SERVIDOR^Y PUERTO DE ESTACION'
         logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The server and port need to be configured properly')
         resultJSON['BillingFromWeb'] = 'ERROR'
         resultJSON['ERROR'] = error
         return resultJSON


   if localStationId.vSimulatePort:
      
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'This station ' + str(localStationId)+ ' will simulate the port using the database')
      newCommand = GLWebCommand()
      newCommand.vStationId=localStationId
      newCommand.vCommandKind="FACTURA WEB"
      newCommand.vCommandInfo+= request.GET['rfc'] + '|' 
      newCommand.vCommandInfo+= request.GET['email'] + '|' 
      newCommand.vCommandInfo+= request.GET['saleId'] + '|' 
      newCommand.vCommandInfo+= request.GET['amount'] + '|' 
      newCommand.vCommandInfo+= request.GET['paymentKind'] + '|' 
      newCommand.vCommandInfo+= request.GET['cfdiUse'] + '|' 
      newCommand.vCommandInfo+= request.GET['proofKind'] + '|' 
      newCommand.vCommandInfo+= request.GET['bank'] + '|' 
      newCommand.vCommandInfo+= request.GET['account'] 
      newCommand.vStartDate= datetime.datetime.now()
      newCommand.save()

      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'The new web command has been saved with id:'+ str(newCommand.vWebCommandId))

      resultJSON['BillingFromWeb'] = 'OK_WAIT'
      resultJSON['CommandId'] = str(newCommand.vWebCommandId)


   else:


       response = askBillingWebService(localStationId.vStationWHost, 
                                    int(localStationId.vStationWPort), 
                                    request.GET['saleId'],
                                    request.GET['amount'],
                                    request.GET['rfc'],
                                    request.GET['paymentKind'],
                                    request.GET['cfdiUse'],
                                    request.GET['proofKind'],
                                    request.GET['bank'],
                                    request.GET['account']
                                    )


       response=str(response)
       if "BillingOK" in response:

          billingId = response.split("_")[1]
          resultJSON['BillingFromWeb'] = 'OK'
          resultJSON['BillingId'] = billingId
          resultJSON['Mail'] = request.GET['email']
          logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Response received by station : ' + response)
          logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Billing was successfull  ')

       else:
          resultJSON['BillingFromWeb'] = 'ERROR'
          resultJSON['ErrorMessage'] = response
          logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The Billing throws the next error : ' + response)

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END billing')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#

def askPricesService(ipAddress, #{{{#
                      port):

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        clientsocket.connect((ipAddress , port))
        clientsocket.send( (GET_PRICES_COMMAND).encode()
                          )
        #time.sleep(0.1)
        time.sleep(1)

        clientsocket.settimeout(90)
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


    return msg
#}}}#

def sendMail(subject, mail, body):

   logger.info('Sending  mail to ' +  str(mail))

   email = GLEmail()
   response = email.send(
      subject,
      mail,
      body,
      "")
   logger.info( 'Mail response:'  + str(response))
   return response


@json_response
def getProductPrices(request):#{{{#

   resultJSON = {}
   resultHTML=''
   logger.info('')
   logger.info('')

   global currentTransaction
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getProductPrices')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'New Get Product Prices Request ' + VERSION)
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'REQUEST METHOD  : [' + request.method+ ']')



   allStations= GLStation.objects.filter(vBilling=True)

   stationsDict=[]
   for currentStation in allStations:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Getting prices from station ' + str(currentStation) + ' on host: ' +  str(currentStation.vStationWHost) + ' and port : ' + str(currentStation.vStationWPort))
      currentObject = {}
      
      currentPrices = askPricesService(currentStation.vStationWHost, 
                                   int(currentStation.vStationWPort)
                                   )
      currentObject['StationId']= str(currentStation.vStationDesc)
      
      resultHTML += 'Estacion : ' +  str(currentStation.vStationDesc) + '<br/>'
      resultHTML +=  str(currentPrices) + '<br/>'
      resultHTML += '<br/>'

      currentObject['Products']= str(currentPrices)
      stationsDict.append(currentObject)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Current Prices on station : '+ str(currentStation)+ ' -> ' + str(currentPrices))


   resultJSON['GetProductPrices'] = 'OK'
   resultJSON['Prices'] = stationsDict
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The GetProductPrices was successfull  ')


   text_file = open("glFTP/prices.txt", "w")
   text_file.write(str(json.dumps(resultJSON)))
   text_file.write("\n")
   text_file.close()

   ftpConn = VoissFTPPutFiles()
   ftpConn.setServerName("www.cmgas.com.mx")
   ftpConn.setServerPort(21)
   ftpConn.setLocalDir('prices')
   ftpConn.setRemoteDir("public_html/prices/")
   ftpConn.setUser("voiss@cmgas.com.mx")
   ftpConn.setPassword("i8vuiZM245")
   ftpConn.uploadFiles()

   logger.info('LOG_ID<' + str(currentTransaction) + '> '+' The file prices.txt has been uploaded to www.cmgas.com.mx/prices/  ')


   sendMail('PRECIOS GRUPO MARIN','lalberto.ralbino@gmail.com',str(resultHTML))
   sendMail('PRECIOS GRUPO MARIN','villaro70@hotmail.com',str(resultHTML))
   sendMail('PRECIOS GRUPO MARIN','cm_gas@hotmail.com',str(resultHTML))


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getProductPrices')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')

   return resultJSON
#}}}#

@json_response
def getWebCommand(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getWebCommand')
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   #logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   #logger.info('LOG_ID<' + currentTransaction + '> '+'New GetWebCommand ' + VERSION)
   #logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   #logger.info('')
   #logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   #logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   #else:
   #   logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   #else:
   #   logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   #else:
   #   logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   #else:
   #   logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['GetWebCommand'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   try:
      #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['GetWebCommand'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   allCommands = GLWebCommand.objects.filter(vStationId= localStationId, vIsActive=True, vCommandStatus="ESPERA").order_by("vWebCommandId")

   if allCommands:
      #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'  allCommands:' + str(allCommands))
      for currentCommand in allCommands:
          logger.info('LOG_ID<' + str(currentTransaction) + '> '+'  Command found:' + str(currentCommand.vWebCommandId))
          if "FACTURA WEB" in currentCommand.vCommandKind:
              commandInfo = currentCommand.vCommandInfo.split('|')
              commandData=''

              currentCommand.vCommandStatus="EN PROCESO"
              currentCommand.save()

              rfc         = commandInfo[0] 
              mail        = commandInfo[1] 
              saleId      = commandInfo[2] 
              amount      = commandInfo[3] 
              paymentKind = commandInfo[4] 
              cfdiUse     = commandInfo[5] 
              proofKind   = commandInfo[6] 
              bank        = commandInfo[7] 
              account     = commandInfo[8] 

              commandData+= str(BILLING_WEB_COMMAND)
              commandData+= saleId.rjust(15)[:15] 
              commandData+= amount.rjust(10)[:10] 
              commandData+= rfc.rjust(15)[:15] 
              commandData+= bank.rjust(50)[:50] 
              commandData+= account.rjust(10)[:10] 
              commandData+= paymentKind.rjust(3)[:8] 
              commandData+= cfdiUse.rjust(3)[:8] 
              commandData+= proofKind.rjust(3)[:3] 

              resultJSON['CommandData'] = commandData
              resultJSON['CommandId'] = str(currentCommand.vWebCommandId)
          break
   else:
      resultJSON['CommandData'] = ''
      resultJSON['CommandId'] = ''


   resultJSON['GetWebCommand']= 'OK'
   resultJSON['CommandInfo']= 'INFO'


   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getWebCommand')
   #logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   #logger.info('')
   #logger.info('')
   
   return resultJSON
#}}}#

@json_response
def responseWebCommand(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START responseWebCommand')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New ResponseWebCommand ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('commandId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'COMMAND ID      : [' + request.GET['commandId']+ ']')

   if request.GET.get('response') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'RESPONSE        : [' + request.GET['response']+ ']')

   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['ResponseWebCommand'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId, vKind='WEB')
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['ResponseWebCommand'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON

   try:

       currentWebCommand  = GLWebCommand.objects.get(vWebCommandId= request.GET['commandId'])
       currentWebCommand.vCommandStatus= "FINALIZO"
       currentWebCommand.vStatusResponse= request.GET['response']
       currentWebCommand.save()

   except GLWebCommand.DoesNotExist:
      error='^EL ID COMANDO NO EXISTE EN EL SISTEMAA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The commandId : ' + str(request.GET['commandId']) + ' does not exist on system')
      resultJSON['ResponseWebCommand'] = 'ERROR'
      resultJSON['ErrorMessage'] = error
      return resultJSON


   resultJSON['ResponseWebCommand']= 'OK'


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END responseWebCommand')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

@json_response
def getCommandResponse(request):#{{{#

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START getCommandResponse')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New GetCommandResponse ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'COMMAND ID      : [' + request.GET['commandId']+ ']')


   currentCommand= GLWebCommand.objects.filter(vWebCommandId= request.GET['commandId'], vCommandStatus="FINALIZO")

   if currentCommand:
       logger.info('LOG_ID<' + currentTransaction + '> '+'The response is ready :'+ str(currentCommand[0].vStatusResponse)) 
       currentCommand[0].vIsActive=False
       resultJSON['ResponseReady']= 'OK'
       resultJSON['Message']= str(currentCommand[0].vStatusResponse)
       currentCommand[0].save()
   else:
       resultJSON['ResponseReady']= 'NO'


   resultJSON['GetCommandResponse']= 'OK'


   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END getCommandResponse')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON
#}}}#

def askCheckCardService(ipAddress, #{{{#
                      port,
                      operation,
                      data,
                      idCard,
                      pump
                      ):

   
   clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   msg = ''
   if operation == '1':
      
      try:
         clientsocket.connect((ipAddress,port))
         logger.info('LOG_ID<' + str(currentTransaction) + '> '+ "Query Values: code[" + CODE_QUERY.rjust(2) + "] idCard[" + idCard +"] pump[" + pump +"]")
         clientsocket.send((CODE_QUERY.rjust(2) 
                        + idCard.rjust(25) + pump.rjust(2)).encode())
         time.sleep(1)

         clientsocket.settimeout(90)
         while True:

            try:

               msg = clientsocket.recv(4096)
            except socket.error as e:

               err = e.args[0]
               if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                  sleep(1)
                  continue
               else:
                  msg = "ERROR :"+err
                  break
            else:
               logger.info('LOG_ID<' + str(currentTransaction) + '> '+ "Query successfull")
               break

         clientsocket.close()
      except socket.error as msg:
         return 'No se pudo conectar a servidor <' + str(msg) + '>'



   #Hace el insert en el servicio fleets
   elif operation == '2':
      data_insert = getValueCard(data)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+ "Insert Values: " + data_insert)

      try:
         clientsocket.connect((ipAddress,port))
         clientsocket.send((CODE_INSERT.rjust(2) 
                              + data_insert).encode())
         time.sleep(1)

         clientsocket.settimeout(90)
         while True:

            try:
                  
               msg = clientsocket.recv(4096)
               
            except socket.error as e:

               err = e.args[0]
               if err == errno.EAGAIN or err == errno.EWOULDBLOCK:

                  sleep(1)
                  continue
               else:
                  msg = "ERROR :"+err
                  break
            else:
               logger.info('LOG_ID<' + str(currentTransaction) + '> '+ "Insert successfull")   
               break

         clientsocket.close()
      except socket.error as msg:

         return 'No se pudo conectar a servidor <' + str(msg) + '>'

   
   return msg     

def itsUndefined(value,str_values,key):
   
   if value != 'undefined':
      
      if key == 'pump':
         str_values = str_values + value.rjust(2) + '|'
      if key == 'idCard':
         str_values = str_values + value.rjust(25) + '|'
      if key == 'Producto':
         str_values = str_values + value.rjust(3) + '|'
      if key == 'Odometro':
         str_values = str_values + value.rjust(10) + '|'
      if key == 'Tipo':
         str_values = str_values + value.rjust(1) + '|'
      if key == 'Cantidad':
         str_values = str_values + value.rjust(10) + '|'
      if key == 'NIP':
         str_values = str_values + value.rjust(10) + '|'
   else:
      empty = ''
      if key == 'NIP':
         str_values = str_values + empty.rjust(10) + '|'
      if key == 'Aux':
         str_values = str_values + empty.rjust(20) + '|'
      if key == 'Odometro':
         str_values = str_values + empty.rjust(10) + '|'
      if key == 'Cantidad':
         str_values = str_values + empty.rjust(10) + '|'
      if key == 'Producto':
         str_values = str_values + empty.rjust(3) + '|'
      if key == 'idCard':
         str_values = str_values + empty.rjust(25) + '|'
      if key == 'pump':
         str_values = str_values + empty.rjust(2) + '|'

   return str_values


def getValueCard(values):
   str_values = ''
  
   logger.info('LOG_ID< > '+ "pump     : " + str(values['pump']) )
   logger.info('LOG_ID< > '+ "idCard   : " + str(values['idCard']) )
   logger.info('LOG_ID< > '+ "Producto : " + str(values['Producto']) )
   logger.info('LOG_ID< > '+ "Odometro : " + str(values['Odometro']) )
   logger.info('LOG_ID< > '+ "Tipo     : " + str(values['Tipo']) )
   logger.info('LOG_ID< > '+ "Cantidad : " + str(values['Cantidad']) )
   logger.info('LOG_ID< > '+ "NIP      : " + str(values['NIP']) )
   logger.info('LOG_ID< > '+ "Aux      : " + str(values['Aux']) )

   str_values = itsUndefined(values['pump'],str_values,'pump')
   str_values = itsUndefined(values['idCard'],str_values,'idCard')
   str_values = itsUndefined(values['Producto'],str_values,'Producto')
   str_values = itsUndefined(values['Odometro'],str_values,'Odometro')
   str_values = itsUndefined(values['Tipo'],str_values,'Tipo')
   str_values = itsUndefined(values['Cantidad'],str_values,'Cantidad')
   str_values = itsUndefined(values['NIP'],str_values,'NIP')
   str_values = itsUndefined(values['Aux'],str_values,'Aux')

   return str_values

def itsTrue(val,str_values):
   if val:
      str_values = str_values + '1'
   else:
      str_values = str_values + '0'

   return str_values

def variablesToShow(currentStation):

   str_values = ''

   str_values = itsTrue(currentStation.vShowProductId,str_values)
   str_values = itsTrue(currentStation.vShowMaxAmount,str_values)
   str_values = itsTrue(currentStation.vShowMaxVolume,str_values)
   str_values = itsTrue(currentStation.vShowDesc,str_values)
   str_values = itsTrue(currentStation.vShowBrand,str_values)
   str_values = itsTrue(currentStation.vShowModel,str_values)
   str_values = itsTrue(currentStation.vShowPlate,str_values)
   str_values = itsTrue(currentStation.vShowEnumber,str_values)
   str_values = itsTrue(currentStation.vShowBalance,str_values)

   return str_values


@json_response
def checkCard(request):

   resultJSON = {}
   logger.info('')
   logger.info('')
   if not cache.get('current_transaction'):
      cache.set('current_transaction',0)

   cache.incr('current_transaction')
   currentTransaction = str(cache.get('current_transaction'))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'START checkCard')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('LOG_ID<' + currentTransaction + '> '+'New checkCard ' + VERSION)
   logger.info('LOG_ID<' + currentTransaction + '> '+'------------------------------------------------------------')
   logger.info('')
   logger.info('LOG_ID<' + currentTransaction + '> '+'QUERY_STRING    : [' + request.META['QUERY_STRING'] + ']')
   logger.info('LOG_ID<' + currentTransaction + '> '+'REQUEST METHOD  : [' + request.method+ ']')


   #Verifica que se le hayan pasado cada uno de los parametros necesarios para hacer validaciones
   if request.GET.get('lsUser') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'USER            : [' + request.GET['lsUser']+ ']')

   if request.GET.get('lsPass') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PASS            : [' + request.GET['lsPass']+ ']')

   if request.GET.get('stationId') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'STATION         : [' + request.GET['stationId']+ ']')

   if request.GET.get('tokenDevice') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'TOKEN DEVICE    : [' + request.GET['tokenDevice']+ ']')

   if request.GET.get('pump') is None:
      return resultJSON
   else:
      logger.info('LOG_ID<' + currentTransaction + '> '+'PUMP    : [' + request.GET['pump']+ ']')

   #Realiza las validaciones
   
   #Validando estación
   try:
      localStationId= GLStation.objects.get(vStationDesc=request.GET['stationId'])
   except GLStation.DoesNotExist:
      error='^LA ESTACION^' + str(request.GET['stationId']) + '^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The station : ' + str(request.GET['stationId']) + ' does not exist on system')
      resultJSON['checkCard'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON

   #validando usuario   
   try:
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'Validating User')
      localUserId= GLUser.objects.get(vUserAccess__iexact=request.GET['lsUser'] ,  vPassAccess=request.GET['lsPass'], vStationId= localStationId)
      logger.info('LOG_ID<' + str(currentTransaction) + '> '+'User is OK')
   except GLUser.DoesNotExist:
      error='^EL USUARIO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The user : ' + str(request.GET['lsUser']) + ' does not exist on system')
      resultJSON['checkCard'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON

   #validando dispositivo   
   try:
      logger.info('LOG_ID<'+str(currentTransaction)+'> '+'Validating Device')
      localDeviceId = GLDevice.objects.get(vDeviceToken=request.GET['tokenDevice'])
      logger.info('LOG_ID<'+str(currentTransaction)+'> '+'Device Ok')
   except GLDevice.DoesNotExist:
      error = '^EL DISPOSITIVO^ ^NO EXISTE^EN EL SISTEMA'
      logger.error('LOG_ID<' + str(currentTransaction) + '> '+' The device with token : ' + str(request.GET['tokenDevice']) + ' does not exist on system')
      resultJSON['checkCard'] = 'ERROR'
      resultJSON['ERROR'] = error
      return resultJSON      

   #Pide los valores de la tarjeta al servicio
   if request.GET['operation'] == '1':
      msg = askCheckCardService(localStationId.vStationWHost,int(localStationId.vStationWPort),"1",None,request.GET['idCard'],request.GET['pump'])

   
   #Hace el insert en el servicio fleets
   elif request.GET['operation'] == '2':
      msg = askCheckCardService(localStationId.vStationWHost,int(localStationId.vStationWPort),"2",request.GET,None,None)
   elif request.GET['operation'] == '3':
      msg = "OKCard0|1|1|1|0|0|0|000|997471.22|999.999|PRUEBAS PRESET|VOLVO|2020|XXBB673|34|-2528.78|".encode()


   if "ERROR" not in str(msg) and "No se pudo conectar a servidor" not in str(msg):

      if len(msg.decode()[6:].split('|'))>6:
         if len(msg.decode()[6:].split('|')[7]) == 3: #Si recibe los 3 digitos de producto id la tarjeta no es válida.
            resultJSON['checkCard']= 'OK'
            resultJSON['cardValues'] = msg.decode()[6:]
            resultJSON['FleetsInfo'] = variablesToShow(localStationId)
         else:
            resultJSON['checkCard']= 'ERROR'
            resultJSON['ERROR'] = 'Tarjeta no valida'
            return resultJSON
      else:
         resultJSON['checkCard']= 'ERROR'
         resultJSON['ERROR'] = 'Tarjeta no valida'
         return resultJSON
   else:

      #Si no encontro el código de error lo manda como tal
      if DICT_ERRORS_FLEETS.get(msg.decode()[6:len(msg.decode())-1]) is None:
         resultJSON['checkCard'] = msg.decode()[6:len(msg.decode())-1]

      #Si lo encontro manda la descripción   
      else:
         resultJSON['checkCard'] = DICT_ERRORS_FLEETS[msg.decode()[6:len(msg.decode())-1]]

      return resultJSON
      
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+' Response received from server: ' + str(msg))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+ str(resultJSON))
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'END checkCard')
   logger.info('LOG_ID<' + str(currentTransaction) + '> '+'******************************')
   logger.info('')
   logger.info('')
   
   return resultJSON

#"00105Tiket 0000000009478 1000^0100COMPUMAR DEMO^0100 Pemex ES 5189^0000R.F.C. VIEE7001301U3^0000PERMISO CRE: PL/22638/EXP/ES/2019^0   SERVICIO SUGASTI XALAPA^0000 00106Tiket 0000000009478 1000^0000*************************************^0100  CONTADO ORIGINAL^0000*************************************^0000 00106Tiket 0000000009478 1000^0000     Cliente:  Publico en General^0000 Fecha Venta: 2020/07/30 19:33:32^0000 Fecha Impre: 2020/07/30 19:33:38^0000       Turno: 2020072201^0000 00106Tiket 0000000009478 1000^0101Transaccion^01013015^0000^0000       Venta: 9478^0000      Web Id: t00100000301502^0000        Isla: 1^0000       Bomba: 1^0000    Manguera: 1 00106Tiket 0000000009478 1000^0000    Forma Pago: ^0000^0000Producto  Cantidad Precio  Total ^0000-----------------------------------^0000Magna  0.815    81.40    14.80^0000 00106Tiket 0000000009478 1000^0000    Subtotal: 12.77^0000         IVA: 2.03^0000       Total: 14.80^0000^0000CATORCE PESOS CON 80/100 M.N. 00106Tiket 0000000009478 1000^0000-----------------------------------^BARQ0518902t0010000030150200014.8202007301933^0   ESTE TICKET ES FACTURABLE SOLO^0   EL DIA DE SU CONSUMO 00107Tiket 0000000009478 1000^0   FACTURACION EN LINEA:^0   gl-operacion.com.mx"
