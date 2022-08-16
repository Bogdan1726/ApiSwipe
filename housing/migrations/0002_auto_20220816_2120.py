# Generated by Django 3.2.14 on 2022-08-16 18:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('housing', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='residentialcomplex',
            old_name='district',
            new_name='address',
        ),
        migrations.RemoveField(
            model_name='residentialcomplex',
            name='microdistrict',
        ),
        migrations.RemoveField(
            model_name='residentialcomplex',
            name='street',
        ),
    ]
