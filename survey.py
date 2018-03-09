

"""
NEX ICO Template
===================================
Author: Thomas Saunders
Email: tom@neonexchange.org
Date: Dec 11 2017
"""
from nex.txio import get_asset_attachments
from nex.token import *
from nex.crowdsale import *
from nex.nep5 import *
from boa.interop.Neo.Runtime import GetTrigger, CheckWitness
from boa.interop.Neo.TriggerType import Application, Verification
from boa.interop.Neo.Storage import *

ctx = GetContext()
NEP5_METHODS = ['name', 'symbol', 'decimals', 'totalSupply', 'balanceOf', 'transfer', 'transferFrom', 'approve', 'allowance']


def Main(operation, args):
    """
    :param operation: str The name of the operation to perform
    :param args: list A list of arguments along with the operation
    :return:
        bytearray: The result of the operation
    """

    trigger = GetTrigger()

    # This is used in the Verification portion of the contract
    # To determine whether a transfer of system assets ( NEO/Gas) involving
    # This contract's address can proceed
    if trigger == Verification():

        # check if the invoker is the owner of this contract
        is_owner = CheckWitness(TOKEN_OWNER)

        # If owner, proceed
        if is_owner:

            return True

        # Otherwise, we need to lookup the assets and determine
        # If attachments of assets is ok
        attachments = get_asset_attachments()
        return can_exchange(ctx,attachments, True)

    elif trigger == Application():

        for op in NEP5_METHODS:
            if operation == op:
                return handle_nep51(ctx, operation, args)

        if operation == 'deploy':
            return deploy()

        elif operation == 'circulation':
            return get_circulation(ctx)

        # the following are handled by crowdsale

        elif operation == 'mintTokens':
            return perform_exchange(ctx)

        elif operation == 'crowdsale_register':
            return kyc_register(ctx, args)

        elif operation == 'crowdsale_status':
            return kyc_status(ctx, args)

        elif operation == 'crowdsale_available':
            return crowdsale_available_amount(ctx)

        elif operation == 'get_attachments':
            return get_asset_attachments()

        elif operation == 'reward':
            if len(args) == 2:
                return reward(ctx, args[0], args[1])

        elif operation == 'create_survey':
            if len(args) == 2:
                return create_survey(ctx, args[0], args[1])

        return 'unknown operation'

    return False


def deploy():
    """
    :param token: Token The token to deploy
    :return:
        bool: Whether the operation was successful
    """
    if not CheckWitness(TOKEN_OWNER):
        print("Must be owner to deploy")
        return False

    if not Get(ctx, 'initialized'):
        # do deploy logic
        Put(ctx, 'initialized', 1)
        Put(ctx, TOKEN_OWNER, TOKEN_INITIAL_AMOUNT)
        return add_to_circulation(ctx, TOKEN_INITIAL_AMOUNT)

    return False

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
    # if not do_approve(ctx, TOKEN_OWNER, surveyer_address, token_per_person_unit):
    #     print("Not approved by the owner")
    #     return False
    # if not do_transfer_from(ctx, TOKEN_OWNER, surveyer_address, token_per_person_unit):
    #     print("Token transfer didnt go through")
    #     return False
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

    # if Get(ctx, surveyid):
    #     print("Survey already added")
    #     return False
    if number_of_surveyers < 1:
        return False
    total_tokens_key = concat(surveyid, "total_tokens")
    number_of_surveyers_key = concat(surveyid, "no")
    Put(ctx, total_tokens_key, tokens)
    Put(ctx, number_of_surveyers_key,  number_of_surveyers)
    return True