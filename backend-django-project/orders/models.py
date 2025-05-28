from django.db import models
from accounts.models import CustomUser 
from tokensbalances.models import Token, AccountBalance
from django.db import transaction





class TokenPair(models.Model):
    base_token = models.ForeignKey(Token, on_delete=models.CASCADE, related_name='tokenpairbasetoken')
    pair_token = models.ForeignKey(Token, on_delete=models.CASCADE, related_name='tokenpairpairtoken')
    exchange_rate: int
    class Meta:
        unique_together = ('base_token', 'pair_token')

class OrderQuerySet(models.QuerySet):
    def get_active_unlocked(self, token_pair_id):
        return self.filter(
            status='ACTIVE',
            locked=False,
            token_pair = token_pair_id
        )


class Order(models.Model):
    class OrderType(models.TextChoices):            
        LIMIT = "LIMIT"
        MARKET = "MARKET"


    class OrderStatus(models.TextChoices):
        ACTIVE = 'ACTIVE'
        WAITING_FOR_EXECUTION = 'WAITING_FOR_EXECUTION'
        COMPLETED = 'COMPLETED'
        CANCELED = 'CANCELED'

    class OrderDirection(models.TextChoices):
        BUY = 'BUY'
        SELL = 'SELL'

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
    required_token_account_balance = models.ForeignKey(AccountBalance,on_delete=models.CASCADE,related_name='orderrequiredtokenaccountbalance',default=None)
    other_token_account_balance = models.ForeignKey(AccountBalance,on_delete=models.CASCADE,related_name='orderothertokenaccountbalance',default=None)

    def atomic_change_status_active_to_waiting_for_execution(self):
        if self.status != Order.OrderStatus.ACTIVE:
            raise Exception
        self.status = Order.OrderStatus.WAITING_FOR_EXECUTION
        self.save()

    def lock_if_not(self):
        if(self.locked):
            return False
        else:
            self.locked = True
            self.save()

    def see_if_it_is_complete_and_save(self):
        if(self.remaining_amount==0):
             self.status = Order.OrderStatus.COMPLETED
        else:
            self.status = Order.OrderStatus.ACTIVE     
        self.save()
    objects = OrderQuerySet.as_manager() 
  
    