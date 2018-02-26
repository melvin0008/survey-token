from nex.common.storage import StorageAPI

class Token():
    """
    Basic settings for an NEP5 Token and crowdsale
    """

    name = 'Survey Token'

    symbol = 'SUR'

    decimals = 8

    # This is the script hash of the address for the owner of the token
    # This can be found in ``neo-python`` with the walet open, use ``wallet`` command
    owner = b'#\xba\'\x03\xc52c\xe8\xd6\xe5"\xdc2 39\xdc\xd8\xee\xe9'

    sc_address = b'\x94\xcfe\x12\xf1T\x9d\xee\x86I\x0b\xd1 \xdb>6g\x1e\x9c\xb3'

    in_circulation_key = b'in_circulation'

    total_supply = 10000000 * 100000000  # 10m total supply * 10^8 ( decimals)

    initial_amount = 2500000 * 100000000  # 2.5m to owners * 10^8

    # for now assume 1 dollar per token, and one neo = 40 dollars * 10^8
    tokens_per_neo = 130 * 100000000

    # for now assume 1 dollar per token, and one gas = 20 dollars * 10^8
    tokens_per_gas = 40 * 100000000

    # maximum amount you can mint in the limited round ( 500 neo/person * 10000 Tokens/NEO * 10^8 )
    max_exchange_limited_round = 500 * 10000 * 100000000

    # when to start the crowdsale
    block_sale_start = 1

    # when to end the initial limited round
    limited_round_end = 1 + 10000000


    def crowdsale_available_amount(self):
        """

        :return: int The amount of tokens left for sale in the crowdsale
        """
        storage = StorageAPI()

        in_circ = storage.get(self.in_circulation_key)

        available = self.total_supply - in_circ

        return available


    def add_to_circulation(self, amount:int, storage:StorageAPI):
        """
        Adds an amount of token to circlulation

        :param amount: int the amount to add to circulation
        :param storage:StorageAPI A StorageAPI object for storage interaction
        """
        current_supply = storage.get(self.in_circulation_key)

        current_supply += amount

        storage.put(self.in_circulation_key, current_supply)



    def get_circulation(self, storage:StorageAPI):
        """
        Get the total amount of tokens in circulation

        :param storage:StorageAPI A StorageAPI object for storage interaction
        :return:
            int: Total amount in circulation
        """
        return storage.get(self.in_circulation_key)

