from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=254, verbose_name="Email адрес")
    avatar = models.ImageField(upload_to="users/avatars/", blank=True, null=True, verbose_name="Аватарка")
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["email"]

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name="following", on_delete=models.CASCADE, verbose_name="Подписчик")
    following = models.ForeignKey(User, related_name="followers", on_delete=models.CASCADE, verbose_name="Автор")

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ["follower"]
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="unique_follow"),
            models.CheckConstraint(check=~models.Q(follower=models.F("following")), name="prevent_self_follow")
        ]

    def __str__(self):
        return f"{self.follower} follows {self.following}"

    def is_following(self, user1, user2):
        return Follow.objects.filter(follower=user1, following=user2).exists()