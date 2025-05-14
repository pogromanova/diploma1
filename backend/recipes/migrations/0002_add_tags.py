from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Название')),
                ('color', models.CharField(max_length=7, unique=True, verbose_name='Цветовой HEX-код')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='Уникальный слаг')),
            ],
            options={
                'verbose_name': 'Тег',
                'verbose_name_plural': 'Теги',
                'ordering': ['name'],
            },
        ),
        migrations.AlterField(
            model_name='recipe',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Название рецепта'),
        ),
        migrations.AddField(
            model_name='recipe',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='recipes', to='recipes.Tag', verbose_name='Теги'),
        ),
    ]