# Generated by Django 5.1.1 on 2024-11-20 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0003_leaderboard_status_alter_leaderboard_category_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='name',
            field=models.CharField(max_length=250, unique=True),
        ),
    ]
