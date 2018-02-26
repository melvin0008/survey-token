"""
NEX ICO Template
===================================
Author: Thomas Saunders
Email: tom@neonexchange.org
Date: Dec 11 2017
"""

from boa.blockchain.vm.Neo.Runtime import GetTrigger, CheckWitness, Notify
from boa.blockchain.vm.Neo.TriggerType import Application, Verification
from nex.common.storage import StorageAPI
from nex.common.txio import Attachments,get_asset_attachments
from nex.token.mytoken import Token
from nex.token.nep5 import NEP5Handler
from nex.token.crowdsale import Crowdsale


def Main(operation, args):
    """
    :param operation: str The name of the operation to perform
    :param args: list A list of arguments along with the operation
    :return:
        bytearray: The result of the operation
    """

    trigger = GetTrigger()
    token = Token()

    #print("Executing ICO Template")

    # This is used in the Verification portion of the contract
    # To determine whether a transfer of system assets ( NEO/Gas) involving
    # This contract's address can proceed
    if trigger == Verification:

        # check if the invoker is the owner of this contract
        is_owner = CheckWitness(token.owner)

        # If owner, proceed
        if is_owner:

            return True

        # Otherwise, we need to lookup the assets and determine
        # If attachments of assets is ok
        attachments = get_asset_attachments()  # type:Attachments

        storage = StorageAPI()

        crowdsale = Crowdsale()

        return crowdsale.can_exchange(token, attachments, storage, True)


    elif trigger == Application:

        if operation != None:

            nep = NEP5Handler()

            for op in nep.get_methods():
                if operation == op:
                    return nep.handle_nep51(operation, args, token)

            if operation == 'deploy':
                return deploy(token)

            if operation == 'circulation':
                storage = StorageAPI()
                return token.get_circulation(storage)

            # the following are handled by crowdsale

            sale = Crowdsale()

            if operation == 'mintTokens':
                return sale.exchange(token)

            if operation == 'create_survey':
                return create_survey(args, token)

            if operation == 'reward':
                return reward(args, token)

            if operation == 'crowdsale_register':
                return sale.kyc_register(args, token)

            if operation == 'crowdsale_status':
                return sale.kyc_status(args)

            if operation == 'crowdsale_available':
                return token.crowdsale_available_amount()

            return 'unknown operation'

    return False


def deploy(token: Token):
    """
    :param token: Token The token to deploy
    :return:
        bool: Whether the operation was successful
    """
    if not CheckWitness(token.owner):
        print("Must be owner to deploy")
        return False

    storage = StorageAPI()

    if not storage.get('initialized'):

        # do deploy logic
        storage.put('initialized', 1)
        storage.put(token.owner, token.initial_amount)
        token.add_to_circulation(token.initial_amount, storage)

        return True

    return False

def reward(args, token: Token):
    surveyid = args[0]
    surveyer_address = args[1]
    nep = NEP5Handler()
    total_tokens_key = concat(surveyid, "total_tokens")
    number_of_surveyers_key = concat(surveyid, "no")
    storage = StorageAPI()
    tokens = storage.get(total_tokens_key)
    number_of_surveyers = storage.get(number_of_surveyers_key)
    token_per_person = tokens / number_of_surveyers
    token_per_person_unit = token_per_person / 100000000
    if token_per_person_unit == 0:
        print("Tokens for the survey are over")
        return False
    Notify(token_per_person_unit)
    if not nep.do_transfer(storage, token.owner, surveyer_address, token_per_person_unit):
        print("Token transfer didnt go through")
        return False
    new_tokens_total = tokens - token_per_person_unit
    new_surveyer_number = number_of_surveyers - 1
    storage.put(total_tokens_key, new_tokens_total)
    storage.put(number_of_surveyers_key, new_surveyer_number)
    print("Reward successful")
    return True

def create_survey(args, token:Token):
    attachments = get_asset_attachments()
    tokens = attachments.gas_attached * token.tokens_per_gas / 100000000
    surveyid = args[0]
    number_of_surveyers = args[1]
    total_tokens_key = concat(surveyid, "total_tokens")
    number_of_surveyers_key = concat(surveyid, "no")
    storage = StorageAPI()
    storage.put(total_tokens_key, tokens)
    storage.put(number_of_surveyers_key,  number_of_surveyers)
    return True
