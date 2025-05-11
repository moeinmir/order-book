from bip_utils import Bip39MnemonicGenerator, Bip39WordsNum

# Generate a valid 12-word mnemonic
mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
print(mnemonic)
