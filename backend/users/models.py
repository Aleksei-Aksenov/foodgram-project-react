from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.db import models
from django.db.models import UniqueConstraint


class User(AbstractUser):
    """Кастомная модель пользователя"""
    username_validator = ASCIIUsernameValidator()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]
    username = models.CharField(
        max_length=150,
        unique=True,
    )
    email = models.EmailField(
        verbose_name="Электронная почта",
        max_length=254,
        unique=True,
    )
    first_name = models.CharField(
        verbose_name="Имя пользователя",
        max_length=150,
    )
    last_name = models.CharField(
        verbose_name="Фамилия пользователя",
        max_length=150,
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписки на авторов"""
    user = models.ForeignKey(
        User,
        related_name='follower',
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('id',)
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
                )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'