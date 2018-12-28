pragma solidity ^0.4.24;

    //import "./Owned.sol";
    import "./Coops.sol";
    import "./Propietarios.sol";
    import "./Proveedores.sol";
    import "./Instaladores.sol"; 
    import "./Gestores.sol";
    //import "./CrowdFunding.sol";

// ----------------------------------------------------------------------------
// Owned contract
// ----------------------------------------------------------------------------
contract Owned {
    address public owner;
    address public newOwner;

    event OwnershipTransferred(address indexed _from, address indexed _to);

    constructor() public {
        owner = msg.sender;
    }

    modifier onlyOwner {
        require(msg.sender == owner);
        _;
    }

    function transferOwnership(address _newOwner) public onlyOwner {
        newOwner = _newOwner;
    }
    function acceptOwnership() public {
        require(msg.sender == newOwner);
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
        newOwner = address(0);
    }
}

    contract Proyectos is Owned{

    struct Project{
        address holder; 
        address vendor; 
        address installer;
        address manager;
        address[] funders;
        uint[] amounts;
        uint price;
    }
    
    //address creator = 0xdD870fA1b7C4700F2BD7f44238821C26f7392148;
    //address owner = 0xdD870fA1b7C4700F2BD7f44238821C26f7392148;
    uint numProjects = 0;
    uint interest_rate = 5;
    
    address Ccontract = 0xa77dfC2c9dD9e641529E6408151831AF3aE116C8;
    address Ocontract = 0x91e0f81bfEd93063b901ec0D5Ec8DD7f4f33c770;
    address Vcontract = 0x6dF74C11E78bCC3C89b4239534FBFe049cDb693b;
    address Icontract = 0xC561270C6fF5286dc845d2e97F8bf3E53Af9c2FC;
    address Mcontract = 0xbDE5dD103E14AC3b62FD97255111ae7a5Ed1a5Ef;
    address Fcontract = 0x9368c3622133c91f7138B66e9589F6456B70928c;

    
    Coops C = Coops(Ccontract);
    Propietarios O = Propietarios(Ocontract);
    Proveedores V = Proveedores(Vcontract);
    Instaladores I = Instaladores(Icontract);
    Gestores M = Gestores(Mcontract);
    CrowdFunding F = CrowdFunding(Fcontract);
    
    
    mapping(uint => Project) private Projects;
    
    event LogNewProject(address holder, address vendor, address installer, address manager, uint price);
    event LogUpdateInterest(uint indexed newrate);

  function getProject(uint ID)
    public 
    constant
    returns(address holder, address vendor, address installer, address manager, uint price)
  {
    //if(!isProvider(userAddress)) revert(); 
    return(
      Projects[ID].holder, 
      Projects[ID].vendor,
      Projects[ID].installer,
      Projects[ID].manager,
      Projects[ID].price);
  } 

    function updateInterest(uint newrate) 
      public
      returns(bool success) 
    {
      //if(!isProvider(msg.sender)) revert(); 
      interest_rate = newrate;
      emit
    LogUpdateInterest(newrate);
    return true;
  }

  function getInterest() 
    public
    constant
    returns(uint count)
  {
    return interest_rate;
  }

    function Matching (address holder, address vendor, address installer, address manager)
        public
        returns(bool success)
    {
        
        if(!O.isDemand(holder)) revert(); 
        if(!V.isProvider(vendor)) revert(); 
        if(!I.isInstaller(installer)) revert(); 
        if(!M.isManager(manager)) revert();
        
        (bool funding, uint maxPrice) = O.getDemand(holder);
        uint vendorPrice = V.getProvider(vendor);
        uint installerPrice = I.getInstaller(installer);
        uint managerPrice = M.getManager(manager);
        
        uint prevCost = vendorPrice + installerPrice + managerPrice;
        uint fee = prevCost * interest_rate / 100;
        uint totalCost = prevCost + fee;
        
        
        if(maxPrice <= totalCost) revert();
        
        //Manage Debt
        C.addDebt(holder, vendor, vendorPrice);
        C.addDebt(holder, installer, installerPrice);
        C.addDebt(holder, manager, managerPrice);
        C.addDebt(holder, owner, fee);

        //Create Project
        Projects[numProjects].holder = holder;
        Projects[numProjects].vendor = vendor;
        Projects[numProjects].installer = installer;
        Projects[numProjects].manager = manager;
        Projects[numProjects].price = totalCost;

        //Funding
        if (funding == true){
            F.Crowdsale(holder, totalCost, 1);
        }else if (funding == false){
            Projects[numProjects].funders.push(holder);
            Projects[numProjects].funders.push(owner);
            Projects[numProjects].amounts.push(prevCost);
            Projects[numProjects].amounts.push(fee);
            C.NewProject(holder,
            Projects[numProjects].funders, 
            Projects[numProjects].amounts, 
            totalCost);
        }
        
        numProjects += 1;
        
        //Allow Rating
        O.allowRating(vendor, holder);
        O.allowRating(installer, holder);
        O.allowRating(manager, holder);
        V.allowRating(holder, vendor);
        V.allowRating(installer, vendor);
        V.allowRating(manager, vendor);
        I.allowRating(holder, installer);
        I.allowRating(vendor, installer);
        I.allowRating(manager, installer);
        M.allowRating(holder, manager);
        M.allowRating(vendor, manager);
        M.allowRating(installer, manager);
        
        //Delete Offer and Demand
        O.deleteDemand(holder);
        V.deleteProvider(vendor);
        I.deleteInstaller(installer);
        M.deleteManager(manager);        
        
        emit 
        LogNewProject(
        holder, 
        vendor, 
        installer, 
        manager,
        totalCost);
        return true;
    }
}
