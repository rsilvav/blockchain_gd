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

