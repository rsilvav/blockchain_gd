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

Gestores_source_code = '''
pragma solidity ^0.4.24;

//import "./Owned.sol";

contract Gestores{

  struct Manager {
    uint Price;
    uint index;
  }
  
  mapping(address => Manager) private Managers;
  address[] private ManagerIndex;
  
  mapping(address => int) private Scores;
  mapping(address => mapping(address => bool)) canRate;

  event LogNewManager   (address indexed userAddress, uint index, uint maxPrice);
  event LogUpdateManager(address indexed userAddress, uint index, uint maxPrice);
  event LogDeleteManager(address indexed userAddress, uint index);
  event LogNewRate(address indexed Rated, int Score);
  
  function isManager(address userAddress)
    public 
    constant
    returns(bool isIndeed) 
  {
    if(ManagerIndex.length == 0) return false;
    return (ManagerIndex[Managers[userAddress].index] == userAddress);
  }

  function newManager(
    uint    Price) 
    public
    returns(uint index)
  {
    if(isManager(msg.sender)) revert(); 
    Managers[msg.sender].Price   = Price;
    Managers[msg.sender].index     = ManagerIndex.push(msg.sender)-1;
    emit 
        LogNewManager(
        msg.sender, 
        Managers[msg.sender].index, 
        Price);
    return ManagerIndex.length-1;
  }

  function deleteManager(address userAddress) 
    public
    returns(uint index)
  {
    if(!isManager(userAddress)) revert(); 
    uint rowToDelete = Managers[userAddress].index;
    address keyToMove = ManagerIndex[ManagerIndex.length-1];
    ManagerIndex[rowToDelete] = keyToMove;
    Managers[keyToMove].index = rowToDelete; 
    ManagerIndex.length--;
    Managers[userAddress].index = 0;
    emit
    LogDeleteManager(
        userAddress, 
        rowToDelete);
    emit
    LogUpdateManager(
        keyToMove, 
        rowToDelete, 
        Managers[keyToMove].Price);
    return rowToDelete;
  }
  
  function getManager(address userAddress)
    public 
    constant
    returns(uint Price)
  {
    if(!isManager(userAddress)) revert(); 
    return(
      Managers[userAddress].Price); 
      //Managers[userAddresngth;
  }

  function getManagerAtIndex(uint index)
    public
    constant
    returns(address userAddress)
  {
    return ManagerIndex[index];
  }

  function getScore(address manager)
    public
    constant
    returns(int score)
  {
    return Scores[manager];
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

Gestores_compiled_sol = compile_source(Gestores_source_code,  import_remappings=['='+os.getcwd(),'=./', '-']) # Compiled source code
#Gestores_compiled_sol = Gestores_source(Gestores_source_code,  import_remappings=['=./', '-']) # Compiled source code
Gestores_interface = Gestores_compiled_sol['<stdin>:Gestores']

gestores = w3.eth.contract(
    address = '0x23215E9FFaE52Eaf79c861d4F620A9748f3652C1',
    abi = Gestores_interface['abi'],
)

i_first = 1
i_last = 5
i_demands = i_last - i_first + 1

reference_price = int(2190000*0.5)
min_price = int(reference_price*0.1)

#create offers
for i in range(i_first,i_last+1):
    acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    i_price_m = random.randint(min_price,reference_price)
    print('NewManager('+str(i_price_m)+')')
    construct_txn = gestores.functions.newManager(i_price_m).buildTransaction({
        'from': acct.address,
        'nonce': w3.eth.getTransactionCount(acct.address),
        'gasPrice': w3.toWei('1', 'gwei')})

    signed = acct.signTransaction(construct_txn)

    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

    # Wait for the transaction to be mined, and get the transaction receipt
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print('Gas used by New Manager = '+str(tx_receipt.gasUsed))

i_maxsteps = 9
i_step = 1
i_matched = 0

#behaviour
while ((i_matched < i_demands) and (i_step <= i_maxsteps)):
    print('step '+str(i_step))
    i_matched = 0
    for i in range(i_first,i_last+1):
        b_matched = gestores.call().isManager(public_keys[i])
        if b_matched == False:
            i_matched += 1
        elif ((b_matched == True) and ((i_step % 25) == 0)):
            #print('*Update Demand*')
            acct = w3.eth.account.privateKeyToAccount(private_keys[i])
            i_price_m = random.randint(min_price,reference_price)
            construct_txn = gestores.functions.updatePrice(i_price_m).buildTransaction({
                'from': acct.address,
                'nonce': w3.eth.getTransactionCount(acct.address),
                'gasPrice': w3.toWei('1', 'gwei')})
            signed = acct.signTransaction(construct_txn)
            tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
            tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print(i_matched)
    i_step += 1


#tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

#clear demands
for i in range(i_first,i_last+1):
    acct = w3.eth.account.privateKeyToAccount(private_keys[i])
    construct_txn = gestores.functions.deleteManager(acct.address).buildTransaction({
        'from': acct.address,
        'nonce': w3.eth.getTransactionCount(acct.address),
        'gasPrice': w3.toWei('1', 'gwei')})
    signed = acct.signTransaction(construct_txn)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print('Gas used by Delete Manager = '+str(tx_receipt.gasUsed))
        

