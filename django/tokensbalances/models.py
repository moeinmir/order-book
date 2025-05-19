from django.db import models
from accounts.models import CustomUser

class Token(models.Model):
    class TokenType(models.TextChoices):
        ERC20 = "ERC20"

    address = models.CharField(max_length=42, unique=True)  # Ethereum address length
    type = models.CharField(max_length=10, choices=TokenType.choices, default=TokenType.ERC20)
    is_active = models.BooleanField(default=True)
    decimals = models.PositiveIntegerField(default=18)

    def __str__(self):
        return f"{self.get_type_display()} Token @ {self.address}"

class AccountBalance(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='accountbalanceuser')
    token = models.ForeignKey(Token, on_delete=models.CASCADE, related_name='accaountbalancetoken')
    hd_wallet_balance = models.BigIntegerField(default=0)
    locked_amount = models.BigIntegerField(default=0)
    free_amount = models.BigIntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    
    def lock_if_not(self):
        if self.is_locked:
            return False
        else:
            self.save()
            self.is_locked = True
            return True

    def unlock_and_save(self):
        self.is_locked = False
        self.save()

    class Meta:
        unique_together = ('user', 'token')

    def __str__(self):
        return f"{self.user.username} - {self.token.address} Balance"


