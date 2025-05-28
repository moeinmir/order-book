"""Example of keys derivation using BIP84."""

from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip39WordsNum, Bip44Changes, Bip84, Bip84Coins


ADDR_NUM: int = 5

# Generate random mnemonic
mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24)
print(f"Mnemonic string: {mnemonic}")