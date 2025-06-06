# Generated by Django 5.2 on 2025-05-13 12:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=42, unique=True)),
                ('type', models.CharField(choices=[('ERC20', 'ERC-20 Token')], default='ERC20', max_length=10)),
                ('is_active', models.BooleanField(default=True)),
                ('decimals', models.PositiveIntegerField(default=18)),
            ],
        ),
        migrations.CreateModel(
            name='AccountBalance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_balance', models.BigIntegerField(default=0)),
                ('locked_amount', models.BigIntegerField(default=0)),
                ('free_amount', models.BigIntegerField(default=0)),
                ('is_locked', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accountbalanceuser', to=settings.AUTH_USER_MODEL)),
                ('token', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accaountbalancetoken', to='tokensbalances.token')),
            ],
            options={
                'unique_together': {('user', 'token')},
            },
        ),
    ]
