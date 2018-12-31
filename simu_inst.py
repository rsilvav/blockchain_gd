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
Instaladores_source_code = '''

pragma solidity ^0.4.24;

//import "./Owned.sol";

contract Instaladores{

  struct Installer {
    uint Price;
    uint index;
  }
  
  mapping(address => Installer) private Installers;
  address[] private InstallerIndex;

  mapping(address => int) private Scores;
  mapping(address => mapping(address => bool)) canRate;
  
  event LogNewInstaller   (address indexed userAddress, uint index, uint maxPrice);
  event LogUpdateInstaller(address indexed userAddress, uint index, uint maxPrice);
  event LogDeleteInstaller(address indexed userAddress, uint index);
  event LogNewRate(address indexed Rated, int Score);
  
  function isInstaller(address userAddress)
    public 
    constant
    returns(bool isIndeed) 
  {
    if(InstallerIndex.length == 0) return false;
    return (InstallerIndex[Installers[userAddress].index] == userAddress);
  }

  function newInstaller(
    uint    Price) 
    public
    returns(uint index)
  {
    if(isInstaller(msg.sender)) revert(); 
    Installers[msg.sender].Price   = Price;
    Installers[msg.sender].index     = InstallerIndex.push(msg.sender)-1;
    emit 
        LogNewInstaller(
        msg.sender, 
        Installers[msg.sender].index, 
        Price);
    return InstallerIndex.length-1;
  }

  function deleteInstaller(address userAddress) 
    public
    returns(uint index)
  {
    if(!isInstaller(userAddress)) revert(); 
    uint rowToDelete = Installers[userAddress].index;
    address keyToMove = InstallerIndex[InstallerIndex.length-1];
    InstallerIndex[rowToDelete] = keyToMove;
    Installers[keyToMove].index = rowToDelete; 
    InstallerIndex.length--;
    emit
    LogDeleteInstaller(
        userAddress, 
        rowToDelete);
    emit
    LogUpdateInstaller(
        keyToMove, 
        rowToDelete, 
        Installers[keyToMove].Price);
    return rowToDelete;
  }
  
  function getInstaller(address userAddress)
    public 
    constant
    returns(uint maxPrice)
  {
    if(!isInstaller(userAddress)) revert(); 
    return(Installers[userAddress].Price);
      //Installers[userAddress].index);
  } 
  
  function updatePrice(uint newPrice) 
    public
    returns(bool success) 
  {
    if(!isInstaller(msg.sender)) revert(); 
    Installers[msg.sender].Price = newPrice;
    emit
    LogUpdateInstaller(
      msg.sender, 
      Installers[msg.sender].index,
      newPrice);
    return true;
  }

  function getInstallersCount() 
    public
    constant
    returns(uint count)
  {
    return InstallerIndex.length;
  }

  function getInstallerAtIndex(uint index)
    public
    constant
    returns(address userAddress)
  {
    return InstallerIndex[index];
  }

  function getScore(address installer)
    public
    constant
    returns(int score)
  {
    return Scores[installer];
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

Instaladores_compiled_sol = compile_source(Instaladores_source_code,  import_remappings=['=./', '-']) # Compiled source code
Instaladores_interface = Instaladores_compiled_sol['<stdin>:Instaladores']

instaladores = w3.eth.contract(
    address = '0x023C8ca441e2366d17D94255A37e1bB4b782e56e',
    abi = Instaladores_interface['abi'],
)

i_first = 1
i_last = 5
i_demands = i_last - i_first + 1

reference_price = int(2190000*0.8)
min_price = int(reference_price*0.1)

#create offers
for i in range(i_first,i_last+1):
    acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    i_price_i = random.randint(min_price,reference_price)
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

i_maxsteps = 100
i_step = 1
i_matched = 0

#behaviour
while ((i_matched < i_demands) and (i_step <= i_maxsteps)):
    print('step '+str(i_step))
    i_matched = 0
    for i in range(i_first,i_last+1):
        b_matched = instaladores.call().isInstaller(public_keys[i])
        if b_matched == False:
            i_matched += 1
        elif ((b_matched == True) and ((i_step % 10) == 0)):
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
    print(i_matched)
    i_step += 1


tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

#clear demands
for i in range(i_first,i_last+1):
    acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    construct_txn = instaladores.functions.deleteInstaller(acct.address).buildTransaction({
        'from': acct.address,
        'nonce': w3.eth.getTransactionCount(acct.address),
        'gasPrice': w3.toWei('1', 'gwei')})
    signed = acct.signTransaction(construct_txn)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print('Gas used by Delete Installer = '+str(tx_receipt.gasUsed))

        

