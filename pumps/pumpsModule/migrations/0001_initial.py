# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GLAudit',
            fields=[
                ('vAuditId', models.AutoField(primary_key=True, serialize=False)),
                ('vAuditAction', models.CharField(verbose_name='Accion', max_length=50)),
                ('vAuditDescription', models.CharField(verbose_name='Descripcion', max_length=200)),
                ('vAuditDate', models.DateTimeField(verbose_name='Fecha', auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Auditoria',
                'verbose_name_plural': 'Auditorias',
            },
        ),
        migrations.CreateModel(
            name='GLCustomer',
            fields=[
                ('vCustomerId', models.AutoField(primary_key=True, serialize=False)),
                ('vBusinessName', models.CharField(verbose_name='Razón Social', max_length=100, null=True, default=None)),
                ('vCommercialName', models.CharField(verbose_name='Nombre Comercial', max_length=100, default=None)),
                ('vRFC', models.CharField(verbose_name='RFC', max_length=20)),
                ('vCreationDate', models.DateTimeField(default=datetime.datetime(2020, 3, 17, 14, 5, 36, 807437))),
                ('vStatus', models.BooleanField(verbose_name='¿Activo?', default=True)),
                ('vKind', models.CharField(verbose_name='Tipo', max_length=11, default='CONTADO', choices=[('CONTADO', 'Contado')])),
                ('vMail', models.CharField(verbose_name='Correo', max_length=100)),
                ('vAccountBank', models.CharField(verbose_name='No. de Cuenta', max_length=100, blank=True, null=True, default=None)),
                ('vBank', models.CharField(verbose_name='Banco', max_length=100, blank=True, null=True, default=None)),
                ('vStreet', models.CharField(verbose_name='Calle', max_length=255, default=None)),
                ('vExternalNumber', models.CharField(verbose_name='Número Exterior', max_length=255, default=None)),
                ('vInternalNumber', models.CharField(verbose_name='Número Interior', max_length=255, default=None)),
                ('vColony', models.CharField(verbose_name='Colonia', max_length=100, default=None)),
                ('vLocation', models.CharField(verbose_name='Localidad', max_length=200, default=None)),
                ('vReference', models.CharField(verbose_name='Referencia', max_length=255, default=None)),
                ('vTown', models.CharField(verbose_name='Municipio', max_length=200, default=None)),
                ('vState', models.CharField(verbose_name='Estado', max_length=31, default='AGUASCALIENTES', choices=[('AGUASCALIENTES', 'Aguascalientes'), ('BAJA CALIFORNIA', 'Baja California'), ('BAJA CALIFORNIA SUR', 'Baja California Sur'), ('CAMPECHE', 'Campeche'), ('CHIAPAS', 'Chiapas'), ('CHIHUAHUA', 'Chihuahua'), ('COAHUILA', 'Coahuila'), ('COLIMA', 'Colima'), ('CIUDAD DE MEXICO', 'Ciudad de México'), ('DURANGO', 'Durango'), ('GUANAJUATO', 'Guanajuato'), ('GUERRERO', 'Guerrero'), ('HIDALGO', 'Hidalgo'), ('JALISCO', 'Jalisco'), ('MEXICO', 'México'), ('MICHOACAN', 'Michoacán'), ('MORELOS', 'Morelos'), ('NAYARIT', 'Nayarit'), ('NUEVO LEON', 'Nuevo León'), ('OAXACA', 'Oaxaca'), ('PUEBLA', 'Puebla'), ('QUERETARO', 'Querétaro'), ('QUINTANA ROO', 'Quintana Roo'), ('SAN LUIS POTOSI', 'San Luis Potosí'), ('SINALOA', 'Sinaloa'), ('SONORA', 'Sonora'), ('TABASCO', 'Tabasco'), ('TAMAULIPAS', 'Tamaulipas'), ('TLAXCALA', 'Tlaxcala'), ('VERACRUZ', 'Veracruz'), ('YUCATAN', 'Yucatán'), ('ZACATECAS', 'Zacatecas')])),
                ('vCountry', models.CharField(verbose_name='País', max_length=6, default='MEXICO', choices=[('MEXICO', 'México')])),
                ('vCP', models.CharField(verbose_name='Codigo Postal', max_length=6, default=None)),
                ('vPhone', models.CharField(verbose_name='Telefono', max_length=50, blank=True, null=True)),
                ('vSendQR', models.BooleanField(verbose_name='¿Enviar QR a correo?', default=False)),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
            },
        ),
        migrations.CreateModel(
            name='GLDevice',
            fields=[
                ('vDeviceId', models.AutoField(primary_key=True, serialize=False)),
                ('vDeviceName', models.CharField(verbose_name='Nombre de Dispositivo', max_length=50, unique=True)),
                ('vUserAgent', models.CharField(verbose_name='UserAgent', max_length=200)),
                ('vOldUserAgent', models.CharField(verbose_name='Browser hash', max_length=200, blank=True, null=True)),
                ('vIPAddress', models.CharField(verbose_name='Direccion IP', max_length=50)),
                ('vDeviceToken', models.CharField(verbose_name='Token', max_length=40)),
                ('vIsActive', models.BooleanField(verbose_name='¿Esta Activo?', default=False)),
                ('vPrintTicket', models.BooleanField(verbose_name='¿Imprimir Ticket?', default=False)),
                ('vLogoutInactivity', models.BooleanField(verbose_name='¿Salir por inactividad?', default=False)),
                ('vTimeout', models.IntegerField(verbose_name='Minutos de inactividad', blank=True, null=True, default=1)),
                ('vVirtualKeyboard', models.BooleanField(verbose_name='¿Teclado Virtual?', default=False)),
                ('vResetStation', models.BooleanField(verbose_name='¿Resetear estacion?', default=False)),
                ('vResetAuth', models.BooleanField(verbose_name='¿Resetear autorizacion?', default=False)),
                ('vPrintLocal', models.BooleanField(verbose_name='¿Impresion en terminal?', default=False)),
            ],
            options={
                'verbose_name': 'Dispositivo',
                'verbose_name_plural': 'Dispositivos',
            },
        ),
        migrations.CreateModel(
            name='GLFunctions',
            fields=[
                ('vFunctionsId', models.AutoField(primary_key=True, serialize=False)),
                ('vFunctionName', models.CharField(verbose_name='Nombre de la función', max_length=50)),
                ('vFunctionDesc', models.CharField(verbose_name='Descripción de la función', max_length=100, blank=True, null=True)),
                ('vOrder', models.IntegerField(verbose_name='Orden', default=0)),
            ],
            options={
                'verbose_name': 'Funcion',
                'verbose_name_plural': 'Funciones',
            },
        ),
        migrations.CreateModel(
            name='GLPartialDelivery',
            fields=[
                ('vPartialDeliveryId', models.AutoField(primary_key=True, serialize=False)),
                ('vDate', models.DateTimeField(verbose_name='Fecha', default=datetime.datetime(2020, 3, 17, 14, 5, 36, 808983))),
                ('vCashAmount', models.CharField(verbose_name='Total Efectivo', max_length=10)),
                ('vVoucherAmountC', models.CharField(verbose_name='Total Tarjeta Crédito', max_length=10)),
                ('vVoucherAmountD', models.CharField(verbose_name='Total Tarjeta Débito', max_length=10)),
                ('vOthersAmount', models.CharField(verbose_name='Total Otros', max_length=10, default='')),
                ('vOthersDesc', models.CharField(verbose_name='Desc Otros', max_length=70, default='')),
                ('vIsland', models.IntegerField(verbose_name='Isla', default=1)),
            ],
            options={
                'verbose_name': 'Entrega',
                'verbose_name_plural': 'Entregas',
            },
        ),
        migrations.CreateModel(
            name='GLShift',
            fields=[
                ('vShiftId', models.AutoField(verbose_name='Id', primary_key=True, serialize=False)),
                ('vShift', models.CharField(verbose_name='Turno', max_length=10, default='')),
            ],
            options={
                'verbose_name': 'Turno',
                'verbose_name_plural': 'Turnos',
            },
        ),
        migrations.CreateModel(
            name='GLStation',
            fields=[
                ('vStationId', models.AutoField(primary_key=True, serialize=False)),
                ('vStationDesc', models.CharField(verbose_name='Descripcion de la Estacion', max_length=100, unique=True)),
                ('vStationWHost', models.CharField(verbose_name='Dominio Remoto de la Estación', max_length=100, blank=True, null=True)),
                ('vStationLHost', models.CharField(verbose_name='Dominio Local de la Estación', max_length=100, blank=True, null=True)),
                ('vStationWPort', models.CharField(verbose_name='Puerto Web', max_length=10, blank=True, null=True)),
                ('vStationLPort', models.CharField(verbose_name='Puerto Local', max_length=10, blank=True, null=True)),
                ('vHeader', models.CharField(verbose_name='Encabezado de Ticket', max_length=500, blank=True, null=True, editable=False)),
                ('vFooter', models.CharField(verbose_name='Pie de Ticket', max_length=500, blank=True, null=True, editable=False)),
                ('vRequireDispatcher', models.BooleanField(verbose_name='¿Requiere Despachador?', default=False)),
                ('vRequireDriver', models.BooleanField(verbose_name='¿Requiere Conductor?', default=False)),
                ('vRequireAuth', models.BooleanField(verbose_name='¿Liberar vales desde App?', default=False)),
                ('vSignDispatchers', models.BooleanField(verbose_name='¿Firmar Despachadores en Isla?', default=False)),
                ('vMinAmount', models.FloatField(verbose_name='Monto Minimo', default=0)),
                ('vPaymentDays', models.IntegerField(verbose_name='Días Pago entre Estaciones', blank=True, null=True, default=15)),
                ('vBilling', models.BooleanField(verbose_name='¿Facturar desde Web?', default=True)),
                ('vPrintTime', models.CharField(verbose_name='Tiempo Max. Impresion', max_length=3, default=1)),
                ('vSimulatePort', models.BooleanField(verbose_name='¿Modo simulación puerto?', default=False)),
                ('vHeader1', models.CharField(verbose_name='Header 1', max_length=36, blank=True, null=True)),
                ('vHeader2', models.CharField(verbose_name='Header 2', max_length=36, blank=True, null=True)),
                ('vHeader3', models.CharField(verbose_name='Header 3', max_length=36, blank=True, null=True)),
                ('vHeader4', models.CharField(verbose_name='Header 4', max_length=36, blank=True, null=True)),
                ('vHeader5', models.CharField(verbose_name='Header 5', max_length=36, blank=True, null=True)),
                ('vHeader6', models.CharField(verbose_name='Header 6', max_length=36, blank=True, null=True)),
                ('vHeader7', models.CharField(verbose_name='Header 7', max_length=36, blank=True, null=True)),
                ('vHeader8', models.CharField(verbose_name='Header 8', max_length=36, blank=True, null=True)),
                ('vFooter1', models.CharField(verbose_name='Footer 1', max_length=36, blank=True, null=True)),
                ('vFooter2', models.CharField(verbose_name='Footer 2', max_length=36, blank=True, null=True)),
                ('vFooter3', models.CharField(verbose_name='Footer 3', max_length=36, blank=True, null=True)),
                ('vFooter4', models.CharField(verbose_name='Footer 4', max_length=36, blank=True, null=True)),
                ('vFooter5', models.CharField(verbose_name='Footer 5', max_length=36, blank=True, null=True)),
                ('vFooter6', models.CharField(verbose_name='Footer 6', max_length=36, blank=True, null=True)),
                ('vFooter7', models.CharField(verbose_name='Footer 7', max_length=36, blank=True, null=True)),
                ('vFooter8', models.CharField(verbose_name='Footer 8', max_length=36, blank=True, null=True)),
                ('vUsePoints', models.BooleanField(verbose_name='¿Modulo Puntos?', default=False)),
                ('vUseTAE', models.BooleanField(verbose_name='¿Modulo TAE?', default=False)),
                ('vUseFleets', models.BooleanField(verbose_name='¿Modulo Flotillas?', default=False)),
                ('vShowProductId', models.BooleanField(verbose_name='¿Mostrar Producto Id?', default=False)),
                ('vShowMaxAmount', models.BooleanField(verbose_name='¿Mostrar Monto Máximo?', default=False)),
                ('vShowMaxVolume', models.BooleanField(verbose_name='¿Mostrar Volumen Máximo?', default=False)),
                ('vShowDesc', models.BooleanField(verbose_name='¿Mostrar Descripcion?', default=False)),
                ('vShowBrand', models.BooleanField(verbose_name='¿Mostrar Marca de Auto?', default=False)),
                ('vShowModel', models.BooleanField(verbose_name='¿Mostrar Modelo de Auto?', default=False)),
                ('vShowPlate', models.BooleanField(verbose_name='¿Mostrar Placa de Auto?', default=False)),
                ('vShowEnumber', models.BooleanField(verbose_name='¿Mostrar Número Economico?', default=False)),
                ('vShowBalance', models.BooleanField(verbose_name='¿Mostrar Saldo?', default=False)),
            ],
            options={
                'verbose_name': 'Estacion',
                'verbose_name_plural': 'Estaciones',
            },
        ),
        migrations.CreateModel(
            name='GLStationGroup',
            fields=[
                ('vStationGroupId', models.AutoField(primary_key=True, serialize=False)),
                ('vStationName', models.CharField(verbose_name='Nombre del Grupo', max_length=80, unique=True)),
                ('vStationGroupDesc', models.CharField(verbose_name='Descripcion', max_length=100, blank=True, null=True, default=None)),
            ],
            options={
                'verbose_name': 'Grupo',
                'verbose_name_plural': 'Grupos',
            },
        ),
        migrations.CreateModel(
            name='GLSubfunctions',
            fields=[
                ('vSubfunctionsId', models.AutoField(primary_key=True, serialize=False)),
                ('vSubfunctionName', models.CharField(verbose_name='Nombre de la función', max_length=50)),
                ('vSubfunctionDesc', models.CharField(verbose_name='Descripción de la función', max_length=100, blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Subfuncion',
                'verbose_name_plural': 'Subfunciones',
            },
        ),
        migrations.CreateModel(
            name='GLUser',
            fields=[
                ('vUserId', models.AutoField(primary_key=True, serialize=False, db_column='vUserId')),
                ('vActive', models.BooleanField(verbose_name='¿Esta activo?', default=True)),
                ('vMulti', models.BooleanField(verbose_name='¿Multi estacion?', default=False)),
                ('vKind', models.CharField(verbose_name='Tipo', max_length=11, default='WEB', choices=[('WEB', 'WEB'), ('CONDUCTOR', 'CONDUCTOR'), ('DESPACHADOR', 'DESPACHADOR'), ('SUPERVISOR', 'SUPERVISOR'), ('OFICINA', 'OFICINA')])),
                ('vName', models.CharField(verbose_name='Nombre', max_length=50)),
                ('vLastname', models.CharField(verbose_name='Apellidos', max_length=50)),
                ('vAge', models.IntegerField(verbose_name='Edad', blank=True, null=True)),
                ('vMail', models.CharField(verbose_name='Correo', max_length=50, blank=True, null=True)),
                ('vPhone', models.CharField(verbose_name='Telefono', max_length=20, blank=True, null=True)),
                ('vMobilePhone', models.CharField(verbose_name='Celular', max_length=20, blank=True, null=True)),
                ('vUserAccess', models.CharField(verbose_name='Usuario', max_length=100)),
                ('vPassAccess', models.CharField(verbose_name='Password', max_length=100)),
                ('vService', models.CharField(verbose_name='Acceso a servicio de', max_length=9, blank=True, null=True, choices=[('FLOTILLAS', 'Flotillas'), ('VALES', 'Vales'), ('PUNTOS', 'Puntos'), ('TAE', 'Tae')])),
                ('vRFC', models.CharField(verbose_name='RFC', max_length=14, blank=True, null=True)),
                ('vIsAdmin', models.BooleanField(verbose_name='¿Permisos Admin?', default=False)),
                ('vIsKiosk', models.BooleanField(verbose_name='¿Modo Kiosco?', default=False)),
                ('vStationId', models.ForeignKey(verbose_name='Estacion', blank=True, null=True, default='', db_column='vStationId', on_delete=django.db.models.deletion.SET_NULL, to='pumpsModule.GLStation')),
            ],
            options={
                'verbose_name': 'Usuario',
                'verbose_name_plural': 'Usuarios',
            },
        ),
        migrations.CreateModel(
            name='GLUserFunction',
            fields=[
                ('vUserFunctionId', models.AutoField(primary_key=True, serialize=False)),
                ('vFunctionsId', models.ForeignKey(verbose_name='Funcion', default=None, db_column='vFunctionsId', to='pumpsModule.GLFunctions')),
                ('vUserId', models.ForeignKey(verbose_name='Usuario', blank=True, null=True, to='pumpsModule.GLUser')),
            ],
        ),
        migrations.CreateModel(
            name='GLWebCommand',
            fields=[
                ('vWebCommandId', models.AutoField(primary_key=True, serialize=False)),
                ('vCommandKind', models.CharField(verbose_name='Tipo de Comando', max_length=20, default='FACTURA WEB', choices=[('NINGUNO', 'NINGUNO'), ('FACTURA ISLA', 'FACTURA ISLA'), ('FACTURA WEB', 'FACTURA WEB'), ('TICKET', 'TICKET')])),
                ('vCommandInfo', models.CharField(verbose_name='Información de Comando', max_length=3000)),
                ('vIsActive', models.BooleanField(verbose_name='¿Esta Activo?', default=True)),
                ('vCommandStatus', models.CharField(verbose_name='Estado', max_length=25, default='ESPERA', choices=[('ESPERA', 'Espera'), ('EN PROCESO', 'En Proceso'), ('FINALIZO', 'Finalizo')])),
                ('vStartDate', models.DateTimeField(verbose_name='Hora de inicio ejecución', auto_now_add=True)),
                ('vEndDate', models.DateTimeField(verbose_name='Hora de fin ejecución', auto_now_add=True)),
                ('vStatusResponse', models.CharField(verbose_name='Respuesta', max_length=200, blank=True, null=True, default=None)),
                ('vStationId', models.ForeignKey(verbose_name='Estacion', blank=True, null=True, db_column='vStationId', to='pumpsModule.GLStation')),
                ('vUserId', models.ForeignKey(verbose_name='Usuario', null=True, db_column='vUserId', on_delete=django.db.models.deletion.SET_NULL, to='pumpsModule.GLUser')),
            ],
            options={
                'verbose_name': 'Comando de Web',
                'verbose_name_plural': 'Comandos de Web',
            },
        ),
        migrations.AddField(
            model_name='glstation',
            name='vStationGroupId',
            field=models.ForeignKey(verbose_name='Grupo de la Estacion', blank=True, null=True, db_column='vStationGroupId', on_delete=django.db.models.deletion.SET_NULL, to='pumpsModule.GLStationGroup'),
        ),
        migrations.AddField(
            model_name='glshift',
            name='vStationId',
            field=models.ForeignKey(verbose_name='Estacion', null=True, default='', db_column='vStationId', on_delete=django.db.models.deletion.SET_NULL, to='pumpsModule.GLStation'),
        ),
        migrations.AddField(
            model_name='glpartialdelivery',
            name='vShiftId',
            field=models.ForeignKey(verbose_name='Turno', null=True, db_column='vShiftId', on_delete=django.db.models.deletion.SET_NULL, to='pumpsModule.GLShift'),
        ),
        migrations.AddField(
            model_name='glpartialdelivery',
            name='vUserId',
            field=models.ForeignKey(verbose_name='Despachador', null=True, db_column='vUserId', on_delete=django.db.models.deletion.SET_NULL, to='pumpsModule.GLUser'),
        ),
        migrations.AddField(
            model_name='gldevice',
            name='vStationId',
            field=models.ForeignKey(verbose_name='Estacion', blank=True, null=True, db_column='vStationId', to='pumpsModule.GLStation'),
        ),
        migrations.AddField(
            model_name='gldevice',
            name='vUserId',
            field=models.ForeignKey(verbose_name='Usuario', null=True, db_column='vUserId', on_delete=django.db.models.deletion.SET_NULL, to='pumpsModule.GLUser'),
        ),
        migrations.AddField(
            model_name='glcustomer',
            name='vStationId',
            field=models.ForeignKey(verbose_name='Estacion', null=True, default='', db_column='vStationId1', on_delete=django.db.models.deletion.SET_NULL, to='pumpsModule.GLStation'),
        ),
        migrations.AddField(
            model_name='glaudit',
            name='vAuditUser',
            field=models.ForeignKey(verbose_name='Usuario', null=True, db_column='vUserId', on_delete=django.db.models.deletion.SET_NULL, to='pumpsModule.GLUser'),
        ),
        migrations.AlterUniqueTogether(
            name='gluser',
            unique_together=set([('vStationId', 'vUserAccess')]),
        ),
    ]
