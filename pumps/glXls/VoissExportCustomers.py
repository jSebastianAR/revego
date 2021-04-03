
from __future__ import print_function
from os.path import join, dirname, abspath
import xlrd
import time
import datetime
import logging
import unicodedata



from pumpsModule.models import GLStation
from pumpsModule.models import GLCustomer

logger = logging.getLogger(__name__)

CUSTOMER_ID_COLUMN=0
CUSTOMER_BUSINESS_NAME_COLUMN=1
CUSTOMER_COMMERCIAL_NAME_COLUMN=2
CUSTOMER_RFC_COLUMN=3
CUSTOMER_CREATION_DATE_COLUMN=4
CUSTOMER_ACTIVE_COLUMN=5
CUSTOMER_KIND_COLUMN=6
CUSTOMER_BALANCE_COLUMN=10
CUSTOMER_STREET_COLUMN=28
CUSTOMER_COLONY_COLUMN=29
CUSTOMER_CP_COLUMN=30
CUSTOMER_TOWN_COLUMN=31
CUSTOMER_PHONE_COLUMN=35
CUSTOMER_MAIL_COLUMN=37
CUSTOMER_EXTERNALNUMBER_COLUMN=38
CUSTOMER_INTERNALNUMBER_COLUMN=39
CUSTOMER_REFERENCE_COLUMN=40
CUSTOMER_STATE_COLUMN=43
CUSTOMER_COUNTRY_COLUMN=45
CUSTOMER_STATION_COLUMN=46


CUSTOMER_DEBIT = 0
CUSTOMER_CREDIT = 1
CUSTOMER_CASH = 2


class VoissExportCustomers():

   def __init__(self):
      self.fileName = ""

   def setFileName(self,fileName):
      self.fileName= fileName

   def remove_accents(self,input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii

   def createCustomers(self):

      fname = join(dirname(dirname(abspath(__file__))), 'glXls', self.fileName)

      # Open the workbook
      xl_workbook = xlrd.open_workbook(fname)

      # List sheet names, and pull a sheet by name
      #
      sheet_names = xl_workbook.sheet_names()

      xl_sheet = xl_workbook.sheet_by_name(sheet_names[0])

      # Or grab the first sheet by index 
      #  (sheets are zero-indexed)
      #
      xl_sheet = xl_workbook.sheet_by_index(0)

      # Pull the first row by index
      #  (rows/columns are also zero-indexed)
      #
      row = xl_sheet.row(0)  # 1st row

      # Print 1st row values and types
      #
      from xlrd.sheet import ctype_text   
      #for idx, cell_obj in enumerate(row):
      #   cell_type_str = ctype_text.get(cell_obj.ctype, 'unknown type')

      # Print all values, iterating through rows and columns
      #
      num_cols = xl_sheet.ncols   # Number of columns
      for row_idx in range(1, xl_sheet.nrows):    # Iterate through rows
            #print ('Row: %s' % row_idx)   # Print row number
            print ("Station: " + str(int(xl_sheet.cell(row_idx, CUSTOMER_STATION_COLUMN).value)))
            print ("Customer Id: " + str(int(xl_sheet.cell(row_idx, CUSTOMER_ID_COLUMN).value)))
            print ("Business Name: " + self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_BUSINESS_NAME_COLUMN ).value)))
            print ("Commercial Name: " + self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_COMMERCIAL_NAME_COLUMN).value)))
            print ("RFC: " + str(xl_sheet.cell(row_idx, CUSTOMER_RFC_COLUMN).value))
            print ("Creation Date: " + str(xlrd.xldate.xldate_as_datetime(xl_sheet.cell(row_idx, CUSTOMER_CREATION_DATE_COLUMN).value, xl_workbook.datemode)))
            print ("Street: " + self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_STREET_COLUMN).value)))
            print ("Ext Number: " + self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_EXTERNALNUMBER_COLUMN).value)))
            print ("Int Number: " + self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_INTERNALNUMBER_COLUMN).value)))
            print ("Colony: " + self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_COLONY_COLUMN).value)))
            print ("Reference: " + self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_REFERENCE_COLUMN).value)))
            print ("Town: " + self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_TOWN_COLUMN).value)))
            print ("State: " + self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_STATE_COLUMN).value)))
            print ("Country: " + unicode(xl_sheet.cell(row_idx, CUSTOMER_COUNTRY_COLUMN).value))
            print ("CP: " + self.remove_accents(unicode(str(xl_sheet.cell(row_idx, CUSTOMER_CP_COLUMN).value))))
            print ("Phone: " + self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_PHONE_COLUMN).value)))
            print ("Mail: " + str(xl_sheet.cell(row_idx, CUSTOMER_MAIL_COLUMN).value))
            print ("Balance: " + str(xl_sheet.cell(row_idx, CUSTOMER_BALANCE_COLUMN).value))
            print ("Kind: " + str(str(xl_sheet.cell(row_idx, CUSTOMER_KIND_COLUMN).value)))
            print ("Active: " + str(int(xl_sheet.cell(row_idx, CUSTOMER_ACTIVE_COLUMN).value)))


            try:
               currentStation = GLStation.objects.get(vStationDesc=str(int(xl_sheet.cell(row_idx, CUSTOMER_STATION_COLUMN).value)))
               currentCustomer = GLCustomer(
                                             vCustomerId= int(xl_sheet.cell(row_idx, CUSTOMER_ID_COLUMN).value),
                                             vStationId= currentStation,
                                             vStatus = bool(str(int(xl_sheet.cell(row_idx, CUSTOMER_ACTIVE_COLUMN).value))),
                                             vMail="" if ("NULL" in   str(xl_sheet.cell(row_idx, CUSTOMER_MAIL_COLUMN).value)) else str(xl_sheet.cell(row_idx, CUSTOMER_MAIL_COLUMN).value),
                                             vKind="CONTADO",
                                             vBusinessName="" if ("NULL" in   self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_BUSINESS_NAME_COLUMN ).value))) else self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_BUSINESS_NAME_COLUMN ).value)),
                                             vCommercialName="" if ("NULL" in   self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_COMMERCIAL_NAME_COLUMN).value))) else self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_COMMERCIAL_NAME_COLUMN).value)),
                                             vRFC=str(xl_sheet.cell(row_idx, CUSTOMER_RFC_COLUMN).value),
                                             vCreationDate=str(xlrd.xldate.xldate_as_datetime(xl_sheet.cell(row_idx, CUSTOMER_CREATION_DATE_COLUMN).value, xl_workbook.datemode)),
                                             vAccountBank="",
                                             vBank="",
                                             vStreet="" if ("NULL" in   self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_STREET_COLUMN).value))) else self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_STREET_COLUMN).value)),
                                             vExternalNumber="0" if ("NULL" in   self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_EXTERNALNUMBER_COLUMN).value))) else self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_EXTERNALNUMBER_COLUMN).value)),
                                             vInternalNumber="0" if ("NULL" in   self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_INTERNALNUMBER_COLUMN).value))) else self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_INTERNALNUMBER_COLUMN).value)),
                                             vColony="" if ("NULL" in   self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_COLONY_COLUMN).value))) else self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_COLONY_COLUMN).value)),
                                             vLocation="",
                                             vReference=  "" if ("NULL" in self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_REFERENCE_COLUMN).value))) else self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_REFERENCE_COLUMN).value)),
                                             vTown="" if ("NULL" in   self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_TOWN_COLUMN).value))) else self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_TOWN_COLUMN).value)),
                                             vState="" if ("NULL" in   self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_STATE_COLUMN).value))) else self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_STATE_COLUMN).value)),
                                             vCountry="" if ("NULL" in   unicode(xl_sheet.cell(row_idx, CUSTOMER_COUNTRY_COLUMN).value)) else unicode(xl_sheet.cell(row_idx, CUSTOMER_COUNTRY_COLUMN).value) ,
                                                vCP="" if ("NULL" in   str(str(xl_sheet.cell(row_idx, CUSTOMER_CP_COLUMN).value))[0:5]) else str(str(xl_sheet.cell(row_idx, CUSTOMER_CP_COLUMN).value))[0:5]  ,
                                             vPhone= "" if ("NULL" in  self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_PHONE_COLUMN).value))) else self.remove_accents(unicode(xl_sheet.cell(row_idx, CUSTOMER_PHONE_COLUMN).value))
                                           )
               currentCustomer.save()
               print ('The customer with id :' + str(currentCustomer.vCustomerId)  +  ' has been generated on system')
            except GLStation.DoesNotExist:
               print ('The station ' +  str(str(int(xl_sheet.cell(row_idx, CUSTOMER_STATION_COLUMN).value)) +  ' does not exist on system'))
      print ('A'*200)

