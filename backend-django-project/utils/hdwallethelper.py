from django.conf import settings
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
import logging

logger = logging.getLogger(__name__)


def derive_eth_address(user_index: int) -> dict:
    logger.info('driving eth address')    
    mnemonic = settings.APP_MNEMONIC
    logger.info(f'mnemonic:{mnemonic}')
    logger.info(f'user_index:{user_index}')
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    logger.info(f'seed_bytes:{seed_bytes}')
    bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    logger.info(f'bip44_mst:{bip44_mst}')    
    bip44_acc = (
        bip44_mst
        .Purpose()
        .Coin()
        .Account(0)
        .Change(Bip44Changes.CHAIN_EXT) 
        .AddressIndex(user_index)
    )
    logger.info(f'bip44_acc:{bip44_acc}')   
    return {
        "address": bip44_acc.PublicKey().ToAddress(), 
        "private_key": bip44_acc.PrivateKey().Raw().ToHex()
    }
