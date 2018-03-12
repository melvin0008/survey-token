import os
import argparse
import threading
import json
import binascii
import base58
import uuid

from time import sleep
from Crypto import Random

from logzero import logger
from twisted.internet import reactor, task, endpoints
from twisted.web.server import Request, Site
from twisted.enterprise import adbapi
from klein import Klein, resource

from neo.Network.NodeLeader import NodeLeader
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Settings import settings

from neo.Network.api.decorators import json_response, gen_authenticated_decorator, catch_exceptions
from neo.contrib.smartcontract import SmartContract

from utils.decorators import cors
from neocore.KeyPair import KeyPair
from surtokencontract import SurTokenContract
from database import Database

# Dev:
SMART_CONTRACT_HASH = "18f39545aaf1f42a7ecbe6e4d0dc7995c1f83dc6"
VERSION = "0.1.0"

# Default REST API port is 8080, and can be overwritten with an env var:
API_PORT = os.getenv("NEO_REST_API_PORT", 8080)

# If you want to enable logging to a file, set the filename here:
LOGFILE = os.getenv("NEO_REST_LOGFILE", None)

# Internal: if LOGFILE is set, file logging will be setup with max
# 10 MB per file and 3 rotations:
if LOGFILE:
    settings.set_logfile(LOGFILE, max_bytes=1e7, backup_count=3)


dir_current = os.path.dirname(os.path.abspath(__file__))
wallet_path = os.path.join(dir_current, "neo-privnet.wallet")
print("wallet path:", wallet_path)
surTokenContract = SurTokenContract(SMART_CONTRACT_HASH, wallet_path, 'coz')

# Internal: setup the klein instance
app = Klein()
survey_db = Database('surveys')
results_db = Database('results')
# Custom code that runs in the background
#
def custom_background_code():
    """ Custom code run in a background thread. Prints the current block height.
    This function is run in a daemonized thread, which means it can be instantly killed at any
    moment, whenever the main thread quits. If you need more safety, don't use a  daemonized
    thread and handle exiting this thread in another way (eg. with signals and events).
    """
    while True:
        logger.info("Block %s / %s", str(Blockchain.Default().Height), str(Blockchain.Default().HeaderHeight))
        sleep(15)

# API error codes
STATUS_ERROR_AUTH_TOKEN = 1
STATUS_ERROR_JSON = 2
STATUS_ERROR_GENERIC = 3


def build_error(error_code, error_message, to_json=True):
    """ Builder for generic errors """
    res = {
        "errorCode": error_code,
        "errorMessage": error_message
    }
    return json.dumps(res) if to_json else res

@app.route('/api/', methods=['GET'])
@json_response
def token_version(request):
    # Collect data.

    return {
        "version": VERSION
    }


@app.route('/api/wallet/<address>', methods=['GET'])
@json_response
def token_balance(request, address):
    # Collect data.
    results = surTokenContract.read_only_invoke("balanceOf", address)
    balance = results[0].GetBigInteger()
    logger.info("balance: %s", balance)

    return {
        "balance": balance
    }

@app.route('/api/survey/<survey_id>', methods=['GET'])
@cors
def get_survey(request, survey_id):
    data = survey_db.query(survey_id)
    data.addCallback(toJSON, request)
    data.addErrback(onFail, request, 'Failed to query db')
    return data

@app.route('/api/survey', methods=['POST'])
@cors
def survey(request):
    data = json.loads(request.content.read().decode("utf-8"))
    survey_id = uuid.uuid4().hex
    data = survey_db.insert_json(survey_id, data)
    data.addCallback(onSuccess, request, survey_id)
    data.addErrback(onFail, request, 'Insert failed')
    return data

@app.route('/api/result', methods=['POST'])
@cors
def result(request):
    data = json.loads(request.content.read().decode("utf-8"))
    survey_id = data['survey_id']
    data = results_db.insert_json(survey_id, data['json'])
    data.addCallback(onSuccess, request, survey_id)
    data.addErrback(onFail, request, 'Insert failed')
    return data

@app.route('/api/reward', methods=['POST'])
@json_response
def reward(request):
    data = json.loads(request.content.read().decode("utf-8"))
    survey_id = data['survey_id']
    hex_address = binascii.hexlify(base58.b58decode_check(data['reward_address'])[1:])
    surTokenContract.add_invoke('reward', survey_id, hex_address)
    return True

def onSuccess(result, request, data):
    request.setResponseCode(201)
    response = {'data': data}
    return json.dumps(response)

def onFail(failure, request, msg):
    request.setResponseCode(417)
    print(failure)
    response = {'message': msg}
    return json.dumps(response)

def toJSON(results, request):
    request.setHeader('Content-Type', 'application/json')
    responseJSON = []
    print(results)
    for record in results:
        mapper = {}
        mapper['id'] = record[0]
        mapper['json'] = json.loads(record[1])
        responseJSON.append(mapper)
    return json.dumps(responseJSON)

#
# Main method which starts everything up
#
def main():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-m", "--mainnet", action="store_true", default=False,
                       help="Use MainNet instead of the default TestNet")
    group.add_argument("-p", "--privnet", action="store_true", default=False,
                       help="Use PrivNet instead of the default TestNet")
    group.add_argument("--coznet", action="store_true", default=False,
                       help="Use the CoZ network instead of the default TestNet")
    group.add_argument("-c", "--config", action="store", help="Use a specific config file")

    args = parser.parse_args()

    # Setup depending on command line arguments. By default, the testnet settings are already loaded.
    if args.config:
        settings.setup(args.config)
    elif args.mainnet:
        settings.setup_mainnet()
    elif args.privnet:
        settings.setup_privnet()
    elif args.coznet:
        settings.setup_coznet()

    # Setup the blockchain
    blockchain = LevelDBBlockchain(settings.LEVELDB_PATH)
    # logger.info(settings.LEVELDB_PATH)
    Blockchain.RegisterBlockchain(blockchain)
    dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
    dbloop.start(.1)
    NodeLeader.Instance().Start()

    # Disable smart contract events for external smart contracts
    settings.set_log_smart_contract_events(True)
    logger.info("Using network: %s" % settings.net_name)

    # Start a thread with custom code
    d = threading.Thread(target=custom_background_code)
    d.setDaemon(True)  # daemonizing the thread will kill it when the main thread is quit
    d.start()

    # Start SurTokenContract thread
    surTokenContract.start()

    # Hook up Klein API to Twisted reactor
    endpoint_description = "tcp:port=%s" % API_PORT
    endpoint = endpoints.serverFromString(reactor, endpoint_description)
    endpoint.listen(Site(app.resource()))

    # Run all the things (blocking call)
    logger.info("Everything setup and running. Waiting for events...")
    reactor.run()
    logger.info("Shutting down.")


if __name__ == "__main__":
    main()