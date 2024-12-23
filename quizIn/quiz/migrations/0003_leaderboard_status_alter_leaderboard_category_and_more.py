# Generated by Django 5.1.1 on 2024-11-19 15:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0002_remove_status_question_difficulty_levels'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaderboard',
            name='status',
            field=models.ForeignKey(blank=True, help_text="User's current status.", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leaderboards', to='quiz.status'),
        ),
        migrations.AlterField(
            model_name='leaderboard',
            name='category',
            field=models.ForeignKey(blank=True, help_text='Associated category.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='leaderboards', to='quiz.category'),
        ),
        migrations.AlterField(
            model_name='leaderboard',
            name='event',
            field=models.ForeignKey(blank=True, help_text='Associated event.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='leaderboards', to='quiz.event'),
        ),
    ]
