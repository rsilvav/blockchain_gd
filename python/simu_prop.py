import json
import web3
import ipdb
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

## Propietarios

Propietarios_abi = open("../abi/Propietarios.json", "r")
o_values = json.load(Propietarios_abi)
Propietarios_abi.close()
propietarios = w3.eth.contract(
    address = '0xD5fbF619121824aCB4e7aAf66A1d86947CE87f1B',
    abi = o_values,
)

## CF

CF_abi = open("../abi/CF.json", "r")
cf_values = json.load(CF_abi)
CF_abi.close()
cf = w3.eth.contract(
    address = '0x4Bac31B5056b1975D286d552F64F7962b8f2b2cc',
    abi = cf_values
)

i_first = 1
i_last = 24
i_demands = i_last - i_first + 1

reference_price = 2190000
min_price = int(reference_price*0.4)

#create offers
for i in range(i_first,i_last+1):
    acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    b_funding = bool(random.getrandbits(1))
    i_MaxPrice = random.randint(min_price,reference_price)
    response = os.system("ping -c 1 " + hostname)
    while response != 0:
        print('No Internet Connection')
        response = os.system("ping -c 1 " + hostname)
    if propietarios.call().isDemand(public_keys[i]) == False:
        print('NewDemand('+str(b_funding)+', '+str(i_MaxPrice)+')')
        construct_txn = propietarios.functions.newDemand(b_funding,i_MaxPrice).buildTransaction({
            'from': acct.address,
            'nonce': w3.eth.getTransactionCount(acct.address),
            'gasPrice': w3.toWei('1', 'gwei')})

        signed = acct.signTransaction(construct_txn)

        tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

        # Wait for the transaction to be mined, and get the transaction receipt
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        print('Gas used by New Demand = '+str(tx_receipt.gasUsed))

i_maxsteps = 10000
i_step = 1
i_matched = 0
i_checkedgas = []
i_withdrawgas = []
#behaviour
while ((i_matched < i_demands) and (i_step <= i_maxsteps)):
    print('step '+str(i_step))
    i_matched = 0
    for i in range(i_first,i_last+1):
        #print(public_keys[i])
        response = os.system("ping -c 1 " + hostname)
        while response != 0:
            print('No Internet Connection')
            response = os.system("ping -c 1 " + hostname)
        b_matched = propietarios.call().isDemand(public_keys[i])
        if b_matched == False:
            i_matched += 1
        elif b_matched == True:
            b_funding = propietarios.call().getFunding(public_keys[i]) 
            #cf.call().crowdsaleClosed()
            if  b_funding == True and cf.call().beneficiary() == public_keys[i]: 
                acct = w3.eth.account.privateKeyToAccount(private_keys[i])
                
                construct_txn = cf.functions.checkGoalReached().buildTransaction({
                    'from': acct.address,
                    'nonce': w3.eth.getTransactionCount(acct.address),
                    'gas': 3000000,
                    'gasPrice': w3.toWei('1', 'gwei')})
                
                signed = acct.signTransaction(construct_txn)
                tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
                tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)            
                i_checkedgas.append(tx_receipt.gasUsed)
            
                if cf.call().crowdsaleClosed(): 
                    print('$$$$')
                    construct_txn = cf.functions.safeWithdrawal().buildTransaction({
                        'from': acct.address,
                        'nonce': w3.eth.getTransactionCount(acct.address),
                        'gasPrice': w3.toWei('1', 'gwei')})
                    signed = acct.signTransaction(construct_txn)
                    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
                    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
                    i_withdrawgas.append(tx_receipt.gasUsed) 
            elif ((b_matched == True) and ((i_step % 100000) == 0)):
                #print('*Update Demand*')
                acct = w3.eth.account.privateKeyToAccount(private_keys[i])
                i_MaxPrice = random.randint(min_price,reference_price)
                b_funding = bool(random.getrandbits(1))
                construct_txn = propietarios.functions.updatemaxPrice(i_MaxPrice).buildTransaction({
                    'from': acct.address,
                    'nonce': w3.eth.getTransactionCount(acct.address),
                    'gasPrice': w3.toWei('1', 'gwei')})
                signed = acct.signTransaction(construct_txn)
                tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
                tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

                construct_txn = propietarios.functions.updateFunding(b_funding).buildTransaction({
                    'from': acct.address,
                    'nonce': w3.eth.getTransactionCount(acct.address),
                    'gasPrice': w3.toWei('1', 'gwei')})
                signed = acct.signTransaction(construct_txn)
                tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
                tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

    print(i_matched)
    i_step += 1


tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

#clear demands

for i in range(1,len(public_keys)):
    address = public_keys[i]
    #acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    if propietarios.call().isDemand(public_keys[i]) == True:
        acct = w3.eth.account.privateKeyToAccount(private_keys[i])
        construct_txn = propietarios.functions.deleteDemand(acct.address).buildTransaction({
            'from': acct.address,
            'nonce': w3.eth.getTransactionCount(acct.address),
            'gasPrice': w3.toWei('1', 'gwei')})
        signed = acct.signTransaction(construct_txn)
        tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        print('Gas used by Delete Demand = '+str(tx_receipt.gasUsed))

print('Check = '+str(i_checkedgas))
print('Withdraw = '+str(withdrawgas))
