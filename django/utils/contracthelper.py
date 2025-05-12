import json
import os
from web3 import Web3
from django.conf import settings
from .hdwallethelper import derive_eth_address
w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))
import logging

logger = logging.getLogger(__name__)

def get_token_contract(token_address: str, token_type: str):
    abi_path = os.path.join(settings.BASE_DIR, 'abis', f'{token_type}.json')
    with open(abi_path, 'r') as abi_file:
        abi = json.load(abi_file)
    return w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=abi)

def transfer_token(from_address, to_address: str, amount: int, token_address: str,token_type:str,user_index:str) -> str:
    logger.info('transfer token inputs')
    logger.info([from_address,to_address,amount,token_address,token_type])
    keys = derive_eth_address(user_index)
    logger.info(f'keys:{keys}')
    private_key = keys['private_key']
    logger.info(f'private_key:{private_key}')
    from_address = Web3.to_checksum_address(from_address)
    logger.info(f'from_address:{from_address}')
    to_address = Web3.to_checksum_address(to_address)
    logger.info(f'to_address:{to_address}')
    contract = get_token_contract(token_address,token_type)
    logger.info(f'contract:{contract}')
    nonce = w3.eth.get_transaction_count(from_address)
    logger.info(f'nonce:{nonce}')
    tx = contract.functions.transfer(to_address, amount).build_transaction({
        'chainId': 11155111,
        'gas': 1000000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return tx_hash.hex()











