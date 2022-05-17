import pytest
from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)


def test_get_entrance_fee():
    #  becasue it unit test, so we wamnt only doi it in local dev
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    #  Arrenge deployment
    lottery = deploy_lottery()
    # Act
    #  If 2000 eth/usd
    #  Fees are = 50 usd
    #  2000/1 == 50/x >> x= 50/2000 >> x = 0.025 >> this what we expect
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    entrance_fee = lottery.getEntranceFee()

    #  Test: assert
    assert entrance_fee == expected_entrance_fee


def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip
    lottery = deploy_lottery()

    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    assert lottery.players(0) == account


def test_can_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    #  to end we need to fund the lottery contract
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    # Lottery_State has 0,1,2
    assert lottery.lottery_state() == 2


#  we need to test if the all thing is doing correctly
#  Open, Choose the winner, pay the winner and close
#  we need to test the choose the winner
def test_can_pick_winner_correctly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    #  to choose the winner the endLottery() calls:
    # >> fullFillRand >> calls callBackWithRandomnes
    # >> calls  v.rawFulfillRandomness.selector
    # >> calls FullFillRandomenss function
    # BUT  callBackWithRandomnes is entry point
    # So to act as Chainlink node we need to provide callBackWithRandomnes args + deta from fnction
    # the endLottery is nor retornig anything
    #  what we wnat is that when we get in the calc Winner state, we call
    # emitting and events
    # events: piece of data executed and stored in the blockchain BUT not accessable by SC
    # you can see events from contracts in events tab in etherscan
    # We need to rebuild these events in Lottery Contract
    trasaction = lottery.endLottery({"from": account})
    request_Id = trasaction.events["RequestedRandomness"]["requestId"]
    #  NOW we have the request ID from event
    # so we can pretend to be chnLink node, to dummy getting a random numner from the node
    #  we can use the callBackRandomens() that passes requestId, random numb,
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_Id, STATIC_RNG, lottery.address, {"from": account}
    )
    #  The above is MOCK RESPONSE for tests
    # The result of the from random to index winner

    starting_balance_of_accounts = account.balance()
    balance_of_lottery = lottery.balance()

    #  777/3 = 259 with 0 reminder >> 777 % 3 == 0
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_accounts + balance_of_lottery

