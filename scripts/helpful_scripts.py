from brownie import (
    network,
    accounts,
    config,
    MockV3Aggregator,
    VRFCoordinatorMock,
    LinkToken,
    Contract,
    interface,
)

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]


def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]

    return accounts.add(config["wallets"]["from_key"])


# Mapping to get contract type
contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    """This function will grab the contracts addresses from brownie config if defined,
    otherwise will deploy the moc version of that contract  and return that mock contract
    The Args will change:
        Args:
            contract_name (string) //pricefeed
        Returns:
            brownie.network.contract.ProjectCOntract: The most recently deployed
                version of this contract >>> MockV3Aggregator[-1]    
    """
    contract_type = contract_to_mock[contract_name]
    # IF LOCAL >>> DEPLOY MOCK
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # Deploy the contract:
        # check if done already
        # same as say len(MockV3... <= 0)
        if len(contract_type) <= 0:
            deploy_mocks()
        #  we now get the contract
        contract = contract_type[-1]
        #  abovem same as say MockV3Agg[-1]
    # IF NET-TEST GET THE CONTRACT
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        # Notice contract name is eth_usd_price_feed, we get that from >> dictionary contract_to_mock
        # To get it we need contract:
        # 1. address: we just defined it
        # 2. ABI: this in MockV3Aggregator
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
        # NOTICE: ._name, .abi are attribut of the contract
        # MockV3Aggregator._name, MockV3Aggregato.abi
    return contract


DECIMALS = 8
INITIAL_VALUE = 200000000000


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_VALUE):
    account = get_account()
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, ({"from": account}))
    print("Mock deployed")


# Contract Address = Lottery.sol address
def fund_with_link(
    contract_address, account=None, link_token=None, amount=100000000000000000
):
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    #  TWO way to do it: 1- transfer functionality or 2- use interfaces
    #  1- Transfer
    tx = link_token.transfer(contract_address, amount, {"from": account})
    #  2- Interface:
    # link_token_contract = interface.LinkTokenInterface(link_token.address)
    # tx = link_token_contract.tramsfer(contract_address, amount, {"from": account})
    tx.wait(1)
    print("Fund contract!!")
    return tx
