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
