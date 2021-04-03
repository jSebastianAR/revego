# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('pumpsModule', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='glstation',
            name='vPrintBoth',
            field=models.BooleanField(verbose_name='¿Original y copia en primer impresion?', default=False),
        ),
        migrations.AlterField(
            model_name='glcustomer',
            name='vCreationDate',
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 21, 18, 18, 18, 578454)),
        ),
        migrations.AlterField(
            model_name='glpartialdelivery',
            name='vDate',
            field=models.DateTimeField(verbose_name='Fecha', default=datetime.datetime(2020, 6, 21, 18, 18, 18, 580378)),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vFooter1',
            field=models.CharField(verbose_name='Footer 1', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vFooter2',
            field=models.CharField(verbose_name='Footer 2', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vFooter3',
            field=models.CharField(verbose_name='Footer 3', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vFooter4',
            field=models.CharField(verbose_name='Footer 4', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vFooter5',
            field=models.CharField(verbose_name='Footer 5', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vFooter6',
            field=models.CharField(verbose_name='Footer 6', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vFooter7',
            field=models.CharField(verbose_name='Footer 7', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vFooter8',
            field=models.CharField(verbose_name='Footer 8', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vHeader1',
            field=models.CharField(verbose_name='Header 1', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vHeader2',
            field=models.CharField(verbose_name='Header 2', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vHeader3',
            field=models.CharField(verbose_name='Header 3', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vHeader4',
            field=models.CharField(verbose_name='Header 4', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vHeader5',
            field=models.CharField(verbose_name='Header 5', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vHeader6',
            field=models.CharField(verbose_name='Header 6', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vHeader7',
            field=models.CharField(verbose_name='Header 7', max_length=80, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glstation',
            name='vHeader8',
            field=models.CharField(verbose_name='Header 8', max_length=80, blank=True, null=True),
        ),
    ]
