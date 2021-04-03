

from django.conf.urls import patterns, url

from pumpsModule import views
from pumpsModule.views import initServer

urlpatterns = patterns('',
    url(r'^Login/', views.loginUser, name='loginUser'),
    url(r'^Register/', views.registerDevice, name='registerDevice'),
    url(r'^ActivateDevice/', views.activateDevice, name='activateDevice'),

    url(r'^ValidateUser/', views.validateUser, name='validateUser'),

    url(r'^Ticket/', views.ticket, name='ticket'),
    url(r'^Delivery/', views.delivery, name='delivery'),
    url(r'^Inventory/', views.inventory, name='inventory'),
    url(r'^Billing/', views.billing, name='billing'),
    url(r'^Preset/', views.preset, name='preset'),
    url(r'^Cancel/', views.cancel, name='cancel'),

    url(r'^GenerateCustomers/', views.generateCustomers, name='generateCustomers'),
    url(r'^GetShiftsAndDispatchers/', views.getShiftsAndDispatchers, name='getShiftsAndDispatchers'),

    url(r'^GetDeliveryReport/', views.getDeliveryReport, name='getDeliveryReport'),

    url(r'^DownloadReport/', views.downloadReport, name='downloadReport'),

    url(r'^PrintDelivery/', views.printDelivery, name='printDelivery'),
    url(r'^PrintBilling/', views.printBilling, name='printBilling'),


    url(r'^GetCustomers/', views.getCustomers, name='getCustomers'),
    url(r'^GetGroups/', views.getGroups, name='getGroups'),
    url(r'^GetStations/', views.getStations, name='getStations'),
    url(r'^GetUsers/', views.getUsers, name='getUsers'),
    url(r'^GetDevices/', views.getDevices, name='getDevices'),
    url(r'^Resend/', views.resend, name='resend'),

    url(r'^GetGroup/', views.getGroup, name='getGroup'),
    url(r'^GetStation/', views.getStation, name='getStation'),
    url(r'^GetUser/', views.getUser, name='getUser'),
    url(r'^GetDevice/', views.getDevice, name='getDevice'),

    url(r'^RemoveGroup/', views.removeGroup, name='removeGroup'),
    url(r'^RemoveStation/', views.removeStation, name='removeStation'),
    url(r'^RemoveUser/', views.removeUser, name='removeUser'),
    url(r'^RemoveDevice/', views.removeDevice, name='removeDevice'),

    url(r'^UpdateGroup/', views.updateGroup, name='updateGroup'),
    url(r'^UpdateStation/', views.updateStation, name='updateStation'),
    url(r'^UpdateUser/', views.updateUser, name='updateUser'),
    url(r'^UpdateDevice/', views.updateDevice, name='updateDevice'),

    url(r'^AddGroup/', views.addGroup, name='addGroup'),
    url(r'^AddCustomer/', views.addCustomer, name='addCustomer'),
    url(r'^AddStation/', views.addStation, name='addStation'),
    url(r'^AddUser/', views.addUser, name='addUser'),
    url(r'^AddDevice/', views.addDevice, name='addDevice'),

    url(r'^ValidateRFC/', views.validateRFC, name='validateRFC'),
    url(r'^AddWebCustomer/', views.addWebCustomer, name='addWebCustomer'),
    url(r'^BillingFromWeb/', views.billingFromWeb, name='billingFromWeb'),

    url(r'^GetProductPrices/', views.getProductPrices, name='getProductPrices'),
    url(r'^GetWebCommand/', views.getWebCommand, name='getWebCommand'),
    url(r'^GetCommandResponse/', views.getCommandResponse, name='getCommandResponse'),
    url(r'^ResponseWebCommand/', views.responseWebCommand, name='responseWebCommand'),
    url(r'^checkCard/',views.checkCard, name='checkCard'),
    url(r'^askKindTicket/',views.askKindTicket, name='askKindTicket'),
   
)

initServer()
