
from rest_framework import serializers
from .models import CustomUser
from django.db import models
from django.conf import settings
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes


def derive_eth_address(user_index: int) -> dict:
    mnemonic = settings.APP_MNEMONIC
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    
    bip44_acc = (
        bip44_mst
        .Purpose()
        .Coin()
        .Account(0)
        .Change(Bip44Changes.CHAIN_EXT) 
        .AddressIndex(user_index)
    )
    return {
        "address": bip44_acc.PublicKey().ToAddress(), 
        "private_key": bip44_acc.PrivateKey().Raw().ToHex()
    }


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)
    eth_address = serializers.CharField(read_only=True)
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'eth_address']

    def create(self, validated_data):
        next_index = (CustomUser.objects.aggregate(models.Max('eth_index'))['eth_index__max'] or 0) + 1
        keys = derive_eth_address(next_index)

        validated_data['eth_address'] = keys['address']
        validated_data['eth_index'] = next_index

        user = CustomUser.objects.create_user(**validated_data)
        return user        