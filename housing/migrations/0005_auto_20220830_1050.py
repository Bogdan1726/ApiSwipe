# Generated by Django 3.2.14 on 2022-08-30 07:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('housing', '0004_galleryresidentialcomplex_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='galleryresidentialcomplex',
            options={'ordering': ('order',)},
        ),
        migrations.AlterField(
            model_name='residentialcomplex',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_residential_complex', to=settings.AUTH_USER_MODEL, unique=True),
        ),
        migrations.DeleteModel(
            name='Apartment',
        ),
    ]
