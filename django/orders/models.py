from django.db import models
from accounts.models import CustomUser 
from tokensbalances.models import Token

class TokenPair(models.Model):
    base_token = models.ForeignKey(Token, on_delete=models.CASCADE, related_name='tokenpairbasetoken')
    pair_token = models.ForeignKey(Token, on_delete=models.CASCADE, related_name='tokenpairpairtoken')
    exchange_rate: int
    class Meta:
        unique_together = ('base_token', 'pair_token')

class OrderQuerySet(models.QuerySet):
    def active_unlocked_sell_market(self, token_pair_id):
        return self.filter(
            status='active',
            direction='sell',
            type = 'market',
            locked=False,
            token_pair = token_pair_id
        )

    def active_unlocked_buy_limit(self,token_pair_id):
            return self.filter(
                status='active',
                direction='sell',
                type = 'market',
                locked=False,
                token_pair = token_pair_id
            )

    def active_unlocked_buy_market(self, token_pair_id):
            return self.filter(
                status='active',
                direction='sell',
                type = 'market',
                locked=False,
                token_pair = token_pair_id
            )

class Order(models.Model):
    class OrderType(models.TextChoices):
        LIMIT = "LIMIT", "limit"
        MARKET = "MARKET", "market"


    class OrderStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'active'
        WAITING_FOR_SETTLEMENT = 'WAITING_FOR_SETTLEMENT', 'waiting_for_settlement'
        SETTLED = 'SETTLED','settled'
        CANCELED = 'CANCELED', 'canceled'

    class OrderDirection(models.TextChoices):
        BUY = 'BUY', 'buy'
        SELL = 'SELL', 'sell'

    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='orderuser')
    status = models.CharField(choices=OrderStatus.choices, default=OrderStatus.ACTIVE)
    token_pair = models.ForeignKey(TokenPair,on_delete=models.CASCADE,related_name='ordertokenpair')
    type = models.CharField(choices=OrderType.choices) 
    amount = models.BigIntegerField()
    remaining_amount = models.BigIntegerField(default=0)
    filled_amount = models.BigIntegerField(default=0)
    filled_amount = models.BigIntegerField(default=0)
    partially_filled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    locked = models.BooleanField(default=False)
    direction = models.CharField(choices=OrderDirection.choices)
    limit_price = models.IntegerField(default=0)
    stop_price = models.IntegerField(default=0)

    def lock_if_not(self):
        if(self.locked):
            return False
        else:
            self.locked = True
            self.save()

    objects = OrderQuerySet.as_manager() 
  
    