import json
import web3
import pdb
import os

#from web3 import Web3
from web3 import Web3, HTTPProvider
from solc import compile_source
from web3.contract import ConciseContract

import pandas as pd
import time
import random

data = pd.read_csv("../Llaves.csv") 

public_keys = data['Llave Publica']
private_keys = data['Llave Privada']

w3 = Web3(HTTPProvider("https://rinkeby.infura.io/v3/4c0ec7f1412a489d91e1934c66ebf5b1"))
hostname = "google.com" #example

## Instaladores

Instaladores_abi = open("../abi/Instaladores.json", "r")
i_values = json.load(Instaladores_abi)
Instaladores_abi.close()
instaladores = w3.eth.contract(
    address = '0xC0ed1D311963EFc99418C0C84Ff2661CF199f9b0',
    abi = i_values
)

## CF

CF_abi = open("../abi/CF.json", "r")
cf_values = json.load(CF_abi)
CF_abi.close()
cf = w3.eth.contract(
    address = '0x4Bac31B5056b1975D286d552F64F7962b8f2b2cc',
    abi = cf_values
)

i_first = 45
i_last = 64
i_demands = i_last - i_first + 1

reference_price = int(2190000*0.5)
min_price = int(reference_price*0.2)

#create offers
for i in range(i_first,i_last+1):
    acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    i_price_i = random.randint(min_price,reference_price)
    response = os.system("ping -c 1 " + hostname)
    while response != 0:
        print('No Internet Connection')
        response = os.system("ping -c 1 " + hostname)
    if instaladores.call().isInstaller(public_keys[i]) == False:
        print('NewInstaller('+str(i_price_i)+')')
        construct_txn = instaladores.functions.newInstaller(i_price_i).buildTransaction({
            'from': acct.address,
            'nonce': w3.eth.getTransactionCount(acct.address),
            'gasPrice': w3.toWei('1', 'gwei')})
        signed = acct.signTransaction(construct_txn)
        tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
        # Wait for the transaction to be mined, and get the transaction receipt
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        print('Gas used by New Installer = '+str(tx_receipt.gasUsed))

i_maxsteps = 10000
i_step = 1
i_matched = 0
i_checkgas = []

#behaviour
while ((i_matched < i_demands) and (i_step <= i_maxsteps)):
    print('step '+str(i_step))
    i_matched = 0
    for i in range(i_first,i_last+1):
        response = os.system("ping -c 1 " + hostname)
        while response != 0:
            print('No Internet Connection')
            response = os.system("ping -c 1 " + hostname)
        b_matched = instaladores.call().isInstaller(public_keys[i])
        if b_matched == False:
            i_matched += 1
        elif public_keys[i] == cf.call().installer():
            pass
        elif ((b_matched == True) and ((i_step % 200) == 0)):
            #print('*Update Demand*')
            acct = w3.eth.account.privateKeyToAccount(private_keys[i])
            i_price_i = random.randint(min_price,reference_price)
            construct_txn = instaladores.functions.updatePrice(i_price_i).buildTransaction({
                'from': acct.address,
                'nonce': w3.eth.getTransactionCount(acct.address),
                'gasPrice': w3.toWei('1', 'gwei')})
            signed = acct.signTransaction(construct_txn)
            tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
            tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
            i_checkgas.append(tx_receipt.gasUsed)
    print(i_matched)
    i_step += 1


tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)



#clear demands

for i in range(1,len(public_keys)):
    address = public_keys[i]
    #acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    if instaladores.call().isInstaller(public_keys[i]) == True:
        acct = w3.eth.account.privateKeyToAccount(private_keys[i])
        construct_txn = instaladores.functions.deleteInstaller(acct.address).buildTransaction({
            'from': acct.address,
            'nonce': w3.eth.getTransactionCount(acct.address),
            'gasPrice': w3.toWei('1', 'gwei')})
        signed = acct.signTransaction(construct_txn)
        tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        print('Gas used by Delete Demand = '+str(tx_receipt.gasUsed))


print(i_checkgas)
        

