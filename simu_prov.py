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

data = pd.read_csv("Llaves.csv") 

public_keys = data['Llave Publica']
private_keys = data['Llave Privada']

w3 = Web3(HTTPProvider("https://rinkeby.infura.io/v3/4c0ec7f1412a489d91e1934c66ebf5b1"))

# Solidity source code
Proveedores_source_code = '''

pragma solidity ^0.4.24;

//import "./Owned.sol";

contract Proveedores{

  struct Provider {
    uint Price;
    uint index;
  }

  mapping(address => Provider) private Providers;
  address[] private ProviderIndex;

  mapping(address => int) private Scores;
  mapping(address => mapping(address => bool)) canRate;

  event LogNewProvider   (address indexed userAddress, uint index, uint maxPrice);
  event LogUpdateProvider(address indexed userAddress, uint index, uint maxPrice);
  event LogDeleteProvider(address indexed userAddress, uint index);
  event LogNewRate(address indexed Rated, int Score);

  function isProvider(address userAddress)
    public
    constant
    returns(bool isIndeed)
  {
    if(ProviderIndex.length == 0) return false;
    return (ProviderIndex[Providers[userAddress].index] == userAddress);
  }

  function newProvider(uint Price)
    public
    returns(uint index)
  {
    if(isProvider(msg.sender)) revert();
    Providers[msg.sender].Price   = Price;
    Providers[msg.sender].index     = ProviderIndex.push(msg.sender)-1;
    emit
        LogNewProvider(
        msg.sender,
        Providers[msg.sender].index,
        Price);
    return ProviderIndex.length-1;
  }

  function deleteProvider(address userAddress)
    public
    returns(uint index)
  {
    if(!isProvider(userAddress)) revert();
    uint rowToDelete = Providers[userAddress].index;
    address keyToMove = ProviderIndex[ProviderIndex.length-1];
    ProviderIndex[rowToDelete] = keyToMove;
    Providers[keyToMove].index = rowToDelete;
    ProviderIndex.length--;
    emit
    LogDeleteProvider(
        userAddress,
        rowToDelete);
    emit
    LogUpdateProvider(
        keyToMove,
        rowToDelete,
        Providers[keyToMove].Price);
    return rowToDelete;
  }

  function getProvider(address userAddress)
    public
    constant
    returns(uint maxPrice)
  {
    if(!isProvider(userAddress)) revert();
    return(
      Providers[userAddress].Price);
      //Providers[userAddress].index);
  }

  function updatePrice(uint newPrice)
    public
    returns(bool success)
  {
    if(!isProvider(msg.sender)) revert();
    Providers[msg.sender].Price = newPrice;
    emit
    LogUpdateProvider(
      msg.sender,
      Providers[msg.sender].index,
      newPrice);
    return true;
  }

  function getProvidersCount()
    public
    constant
    returns(uint count)
  {
    return ProviderIndex.length;
  }

  function getProviderAtIndex(uint index)
    public
    constant
    returns(address userAddress)
  {
    return ProviderIndex[index];
  }

  function getScore(address vendor)
    public
    constant
    returns(int score)
  {
    return Scores[vendor];
  }

  function allowRating(
    address    rater,
    address    rated)
    public
    returns(bool success)
  {
    canRate[rater][rated] = true;
    return true;
  }

  function Rate(
    address    rated,
    int       score)
    public
    returns(bool success)
  {
    if (!canRate[msg.sender][rated]) revert();
    if (score < -1) revert();
    if (score > 1) revert();
    Scores[rated] += score;
    canRate[msg.sender][rated] = false;
    emit
        LogNewRate(
        rated,
        score);
    return true;
  }

}
'''


Proveedores_compiled_sol = compile_source(Proveedores_source_code,  import_remappings=['=./', '-']) # Compiled source code
Proveedores_interface = Proveedores_compiled_sol['<stdin>:Proveedores']

proveedores = w3.eth.contract(
    address = '0x88679873522CEEADC39A00187634B657625caF0e',
    abi = Proveedores_interface['abi'],
)

i_first = 11
i_last = 15
i_demands = i_last - i_first + 1

reference_price = 2190000
min_price = int(reference_price*0.1)

#create offers
for i in range(i_first,i_last+1):
    acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    i_price_v = random.randint(min_price,reference_price)
    print('NewProvider('+str(i_price_v)+')')
    construct_txn = proveedores.functions.newProvider(i_price_v).buildTransaction({
        'from': acct.address,
        'nonce': w3.eth.getTransactionCount(acct.address),
        'gasPrice': w3.toWei('1', 'gwei')})

    signed = acct.signTransaction(construct_txn)

    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

    # Wait for the transaction to be mined, and get the transaction receipt
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print('Gas used by New Vendor = '+str(tx_receipt.gasUsed))

i_maxsteps = 100
i_step = 1
i_matched = 0

#behaviour
while ((i_matched < i_demands) and (i_step <= i_maxsteps)):
    print('step '+str(i_step))
    i_matched = 0
    for i in range(i_first,i_last+1):
        b_matched = proveedores.call().isProvider(public_keys[i])
        if b_matched == False:
            i_matched += 1
        elif ((b_matched == True) and ((i_step % 10) == 0)):
            #print('*Update Demand*')
            acct = w3.eth.account.privateKeyToAccount(private_keys[i])
            i_price_v = random.randint(min_price,reference_price)
            construct_txn = proveedores.functions.updatePrice(i_price_v).buildTransaction({
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
for i in range(i_first,i_last+1):
    acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    construct_txn = proveedores.functions.deleteProvider(acct.address).buildTransaction({
        'from': acct.address,
        'nonce': w3.eth.getTransactionCount(acct.address),
        'gasPrice': w3.toWei('1', 'gwei')})
    signed = acct.signTransaction(construct_txn)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print('Gas used by Delete Demand = '+str(tx_receipt.gasUsed))

        

