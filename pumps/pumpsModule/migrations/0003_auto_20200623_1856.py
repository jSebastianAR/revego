# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('pumpsModule', '0002_auto_20200621_1818'),
    ]

    operations = [
        migrations.AlterField(
            model_name='glcustomer',
            name='vCreationDate',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 23, 18, 56, 55, 155199)),
        ),
        migrations.AlterField(
            model_name='glpartialdelivery',
            name='vDate',
            field=models.DateTimeField(verbose_name='Fecha', default=datetime.datetime(2020, 6, 23, 18, 56, 55, 157258)),
        ),
    ]
