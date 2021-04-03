# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('pumpsModule', '0004_auto_20200731_1635'),
    ]

    operations = [
        migrations.AlterField(
            model_name='glcustomer',
            name='vCreationDate',
            field=models.DateTimeField(default=datetime.datetime(2020, 8, 4, 8, 50, 39, 966329)),
        ),
        migrations.AlterField(
            model_name='glpartialdelivery',
            name='vDate',
            field=models.DateTimeField(verbose_name='Fecha', default=datetime.datetime(2020, 8, 4, 8, 50, 39, 969233)),
        ),
    ]
