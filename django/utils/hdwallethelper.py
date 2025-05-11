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
