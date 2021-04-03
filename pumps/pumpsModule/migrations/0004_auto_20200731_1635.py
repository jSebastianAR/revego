# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('pumpsModule', '0003_auto_20200623_1856'),
    ]

    operations = [
        migrations.AlterField(
            model_name='glcustomer',
            name='vCreationDate',
            field=models.DateTimeField(default=datetime.datetime(2020, 7, 31, 16, 35, 5, 135703)),
        ),
        migrations.AlterField(
            model_name='glpartialdelivery',
            name='vDate',
            field=models.DateTimeField(verbose_name='Fecha', default=datetime.datetime(2020, 7, 31, 16, 35, 5, 139021)),
        ),
    ]
