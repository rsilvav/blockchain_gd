pragma solidity ^0.4.24;

    //import "./Owned.sol";
    import "./Coops.sol";
    import "./Propietarios.sol";
    import "./Proveedores.sol";
    import "./Instaladores.sol"; 
    import "./Gestores.sol";
    //import "./CrowdFunding.sol";


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
    uint public numProjects = 0;
    uint public interest_rate = 5;
    
    address Ccontract = 0x3F5C926EC1BbDBD6C54DBdAAde5573D8e0205121;
    address Ocontract = 0xB1bE2Ba214d35Bcc8a52D1c0eE45C1be47AEb477;
    address Vcontract = 0x88679873522CEEADC39A00187634B657625caF0e;
    address Icontract = 0x023C8ca441e2366d17D94255A37e1bB4b782e56e;
    address Mcontract = 0xe67Cc0C35E461Ad649859738f50598Bd6eb11595;
    address Fcontract = 0x72875926B2403882946D2cB63b2a000A4f949bac;

    
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
        
        uint maxPrice = O.getDemand(holder);
        bool funding = O.getFunding(holder);
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
        if (funding == false){
            Projects[numProjects].funders.push(holder);
            //Projects[numProjects].funders.push(owner);
            Projects[numProjects].amounts.push(prevCost);
            //Projects[numProjects].amounts.push(fee);
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
