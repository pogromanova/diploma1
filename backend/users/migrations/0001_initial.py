from django.db import migrations, models
import django.contrib.auth.models
import django.contrib.auth.validators
from django.utils import timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, verbose_name='superuser status')),
                ('username', models.CharField(
                    error_messages={'unique': 'A user with that username already exists.'},
                    max_length=150,
                    unique=True,
                    validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                    verbose_name='username',
                    help_text='Введите имя пользователя'
                )),
                ('first_name', models.CharField(max_length=150, verbose_name='first name', help_text='Введите имя')),
                ('last_name', models.CharField(max_length=150, verbose_name='last name', help_text='Введите фамилию')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address', help_text='Введите адрес электронной почты')),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('date_joined', models.DateTimeField(default=timezone.now, verbose_name='date joined')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='users/images/', verbose_name='Аватар', help_text='Загрузите аватар')),
                ('groups', models.ManyToManyField(
                    blank=True,
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.Group',
                    verbose_name='groups'
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True,
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.Permission',
                    verbose_name='user permissions'
                )),
            ],
            options={
                'verbose_name': 'Пользователь',
                'verbose_name_plural': 'Пользователи',
                'ordering': ['id'],
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]