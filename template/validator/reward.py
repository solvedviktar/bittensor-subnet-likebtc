# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# TODO(developer): Set your name
# Copyright © 2023 <your name>

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import torch
import hashlib
from typing import List

import template
from template.validator.likebtc import add_likebtc_hash


def acceptance_check(query: template.protocol.Dummy, response: int, winner_hash_dec: int) -> float:
    ''' Validation of acceptance criteria for miner results.
        Function returns new winner if his hash is lower.
    '''
    hash_data = (str(query.input_block_number) + query.input_payload +
                 query.imput_lowest_hash + str(response))
    hash = hashlib.sha256(hash_data.encode()).hexdigest()

    if hash.startswith('0' * query.input_zeroes_acceptance) and \
            (not winner_hash_dec or winner_hash_dec > int(hash, 16)):
        winner_hash_dec = int(hash, 16)

    return winner_hash_dec


def get_rewards(
    self,
    query: template.protocol.Dummy,
    responses: List[float],
) -> torch.FloatTensor:
    """
    Returns a tensor of rewards for the given query and responses.

    Args:
    - query (int): The query sent to the miner.
    - responses (List[float]): A list of responses from the miner.

    Returns:
    - torch.FloatTensor: A tensor of rewards for the given query and responses.
    """
    # Get all the reward results by iteratively calling your reward() function.

    winner_index = None
    winner_hash_dec = None

    for _index, response in enumerate(responses):
        new_winner_hash_dec = acceptance_check(query, response, winner_hash_dec)
        if winner_hash_dec != new_winner_hash_dec:
            winner_index = _index
            winner_hash_dec = new_winner_hash_dec

    if winner_hash_dec:
        add_likebtc_hash('%064x' % winner_hash_dec)

    return torch.FloatTensor(
        [1.0 if _index == winner_index else 0 for _index in range(len(responses))]
    ).to(self.device)
