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

## Coops

Coops_abi = open("../abi/Coops.json", "r")
c_values = json.load(Coops_abi)
Coops_abi.close()
coops = w3.eth.contract(
    address = '0x2c66b176962911D2ce40f5809cD52C73c8E78356',
    abi = c_values,
)


## CF

CF_abi = open("../abi/CF.json", "r")
cf_values = json.load(CF_abi)
CF_abi.close()
cf = w3.eth.contract(
    address = '0x4Bac31B5056b1975D286d552F64F7962b8f2b2cc',
    abi = cf_values
)

i_first = 97
i_last = 120

hostname = "google.com" #example


#behaviour

for i in range(i_first,i_last+1):
	acct = w3.eth.account.privateKeyToAccount(private_keys[i])
	response = os.system("ping -c 1 " + hostname)
	while response != 0:
	    #print('No Internet Connection')
	    response = os.system("ping -c 1 " + hostname)
	while cf.call().crowdsaleClosed() == True:
	    response = os.system("ping -c 1 " + hostname)
	    while response != 0:
	        #print('No Internet Connection')
	        response = os.system("ping -c 1 " + hostname)

	fundingGoal = cf.call().fundingGoal()
	construct_txn = coops.functions.Fund(cf.address,fundingGoal).buildTransaction({
	    'from': acct.address,
	    'nonce': w3.eth.getTransactionCount(acct.address),
	    'gas': 3000000,
	    'gasPrice': w3.toWei('1', 'gwei')})

	signed = acct.signTransaction(construct_txn)

	tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

	# Wait for the transaction to be mined, and get the transaction receipt
	tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

	print('Gas used by Fund = '+str(tx_receipt.gasUsed))
	while cf.call().crowdsaleClosed() == False:
            pass



