from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0006_subscription'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipe',
            options={
                'ordering': ['-pub_date'], 
                'verbose_name': 'Рецепт', 
                'verbose_name_plural': 'Рецепты'
            },
        ),
    ]