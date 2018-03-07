from boa.interop.Neo.Runtime import CheckWitness, Notify
from boa.interop.Neo.Action import RegisterAction
from boa.interop.Neo.Storage import *
from boa.builtins import concat

from nex.token import *


OnTransfer = RegisterAction('transfer', 'addr_from', 'addr_to', 'amount')
OnApprove = RegisterAction('approve', 'addr_from', 'addr_to', 'amount')


def handle_nep51(ctx, operation, args):

    if operation == 'name':
        return TOKEN_NAME

    elif operation == 'decimals':
        return TOKEN_DECIMALS

    elif operation == 'symbol':
        return TOKEN_SYMBOL

    elif operation == 'totalSupply':
        return Get(ctx, TOKEN_CIRC_KEY)

    elif operation == 'balanceOf':
        if len(args) == 1:
            return Get(ctx, args[0])

    elif operation == 'transfer':
        if len(args) == 3:
            return do_transfer(ctx, args[0], args[1], args[2])

    elif operation == 'transferFrom':
        if len(args) == 3:
            return do_transfer_from(ctx, args[0], args[1], args[2])

    elif operation == 'approve':
        if len(args) == 3:
            return do_approve(ctx, args[0], args[1], args[2])

    elif operation == 'allowance':
        if len(args) == 2:
            return do_allowance(ctx, args[0], args[1])

    elif operation == 'reward':
        if len(args) == 2:
            return reward(ctx, args[0], args[1])

    elif operation == 'create_survey':
        if len(args) == 2:
            return reward(ctx, args[0], args[1])
    return False

def do_transfer(ctx, t_from, t_to, amount):

    if amount <= 0:
        return False

    if len(t_to) != 20:
        return False

    if CheckWitness(t_from):

        if t_from == t_to:
            print("transfer to self!")
            return True

        from_val = Get(ctx, t_from)

        if from_val < amount:
            print("insufficient funds")
            return False

        if from_val == amount:
            Delete(ctx, t_from)

        else:
            difference = from_val - amount
            Put(ctx, t_from, difference)

        to_value = Get(ctx, t_to)

        to_total = to_value + amount

        Put(ctx, t_to, to_total)

        OnTransfer(t_from, t_to, amount)

        return True
    else:
        print("from address is not the tx sender")

    return False

def owner_transfer(ctx, t_from, t_to, amount):
    """
    Transfer tokens from the owner to the person who submits the survey
    TODO: Move the logic to SC. SC should be holding the tokens

    :param storage:StorageAPI A StorageAPI object for storage interaction
    :param t_from Address of owner
    :param t_to  Address of the surveyer
    :param amount Amount that should be sent to the surveyer

    """
    if amount <= 0:
        return False

    if len(t_to) != 20:
        return False

    if t_from == t_to:
        print("transfer to self!")
        return True

    from_val = Get(ctx, t_from)
    msg = ["msg", from_val]
    Notify(msg)

    if from_val < amount:
        print("insufficient funds")
        return False

    if from_val == amount:
        Delete(ctx, t_from)

    else:
        difference = from_val - amount
        Put(ctx, t_from, difference)

    to_value = Get(ctx, t_to)

    to_total = to_value + amount

    Put(ctx, t_to, to_total)

    OnTransfer(t_from, t_to, amount)
    print("transfer complete")

    return True

def do_transfer_from(ctx, t_from, t_to, amount):

    if amount <= 0:
        return False

    available_key = concat(t_from, t_to)

    if len(available_key) != 40:
        return False

    available_to_to_addr = Get(ctx, available_key)

    if available_to_to_addr < amount:
        print("Insufficient funds approved")
        return False

    from_balance = Get(ctx, t_from)

    if from_balance < amount:
        print("Insufficient tokens in from balance")
        return False

    to_balance = Get(ctx, t_to)

    new_from_balance = from_balance - amount

    new_to_balance = to_balance + amount

    Put(ctx, t_to, new_to_balance)
    Put(ctx, t_from, new_from_balance)

    print("transfer complete")

    new_allowance = available_to_to_addr - amount

    if new_allowance == 0:
        print("removing all balance")
        Delete(ctx, available_key)
    else:
        print("updating allowance to new allowance")
        Put(ctx, available_key, new_allowance)

    OnTransfer(t_from, t_to, amount)

    return True

def do_approve(ctx, t_owner, t_spender, amount):

    if not CheckWitness(t_owner):
        return False

    if amount < 0:
        return False

    # cannot approve an amount that is
    # currently greater than the from balance
    if Get(ctx, t_owner) >= amount:

        approval_key = concat(t_owner, t_spender)

        if amount == 0:
            Delete(ctx, approval_key)
        else:
            Put(ctx, approval_key, amount)

        OnApprove(t_owner, t_spender, amount)

        return True

    return False

def do_allowance(ctx, t_owner, t_spender):

    return Get(ctx, concat(t_owner, t_spender))



def reward(ctx, surveyid, surveyer_address):
    total_tokens_key = concat(surveyid, "total_tokens")
    number_of_surveyers_key = concat(surveyid, "no")
    tokens = Get(ctx, total_tokens_key)
    number_of_surveyers = Get(ctx, number_of_surveyers_key)
    token_per_person = tokens / number_of_surveyers
    token_per_person_unit = token_per_person / 100000000
    if token_per_person_unit == 0:
        print("Tokens for the survey are over")
        return False
    Notify(token_per_person_unit)
    if not owner_transfer(ctx, TOKEN_OWNER, surveyer_address, token_per_person_unit):
        print("Token transfer didnt go through")
        return False
    new_tokens_total = tokens - token_per_person_unit
    new_surveyer_number = number_of_surveyers - 1
    Put(ctx, total_tokens_key, new_tokens_total)
    Put(ctx, number_of_surveyers_key, new_surveyer_number)
    print("Reward successful")
    return True

def create_survey(ctx, surveyid, number_of_surveyers):
    """
    The set of questions which are part of the survey are submitted to MongoDB.
    As part of the next step (this function) we take in the survey id and
    the number of surveyers the lister wants to distribute the money to

    :param args  Argument send to the smart contract. arg[0] -> SurveyId arg[1] -> number of surveyers.
    :param token:Token Token object
    """
    attachments = get_asset_attachments()
    tokens = attachments[3] * TOKENS_PER_GAS / 100000000
    if tokens == 0:
        print("No tokens submitted to distribute")
        return False

    if Get(ctx, surveyid):
        print("Survey already added")
        return False
    if number_of_surveyers < 1:
        return False
    total_tokens_key = concat(surveyid, "total_tokens")
    number_of_surveyers_key = concat(surveyid, "no")
    Put(ctx, total_tokens_key, tokens)
    Put(ctx, number_of_surveyers_key,  number_of_surveyers)
    return True