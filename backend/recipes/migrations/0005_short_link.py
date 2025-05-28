from django.db import migrations, models
import django.db.models.deletion
import hashlib
import random
import string


class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0004_shopping_cart'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShortLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_id', models.CharField(db_index=True, max_length=10, unique=True, verbose_name='Короткий идентификатор')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='short_links', to='recipes.Recipe', verbose_name='Рецепт')),
            ],
            options={
                'verbose_name': 'Короткая ссылка',
                'verbose_name_plural': 'Короткие ссылки',
            },
        ),
    ]