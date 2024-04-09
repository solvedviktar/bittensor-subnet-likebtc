<div align="center">

# **Bittensor Subnet LikeBTC**

---

## Quickstarter

This subnet is fully based on the original template.
- Supports original instructions for running on staging described in `docs/running_on_staging.md`.
- Used `main` branch from [subtensor](https://github.com/opentensor/subtensor.git) repository.
- Tested with 2 miners and one validator.

---

## Introduction

**IMPORTANT**: Subnet does not support concurrency (multiple validators) for validator!

The subnet emulates Bitcoin blockchain process (a bit different to avoid extreme complexity rise because of CPU-based development) with blocks storage. Validator(s) is broadcasting information of current network info state. Miner(s) is trying to calculate new hash value by adding random nonce with network state info, and in the best case find a hash that is lower than the previous, in the worst case just anyone matched with nonce acceptance criteria.

At the first run, validator creates file `likebtc_hashes.txt` (like a storage) with hash blocks sequence, like:
```
00006f8062e0d6b3d2dcdcc34b3acb918f82b930ab2a5cf81ee11cd5aa883c15
000013d5dd961db3327c1b179c3f14bc1ee9b8049755c0448ee6a95e72cf04c7
00007ae764ee4f54367edf146eb6197e28fbdd4cbf0a06cdeb3d69a1fc376162
00009b747742ae1c942d92c1946a40051ca9f799b76c4fc6ceb6c9cb79d96733
00001a1b7fb950563d9ed53d9fd3d445f393720b7ae865de56cb34a9f9916e09
000042bbe92add4e4cf07df65851534513f4d7801d17ff0ecc47d5110f32a297
00000e5938ffe9d5eec91e2cc5cc490d422b87a006cf214ea1303cac28198d2f
000088eb38ee3dbd8560057005fca64044b22846a211cc10e2f8ae62f8e21600
00009f4e9352b4fefb0bf6c279777498999eb9c0239a0ce950a8d9f28a797e0b
00005f78cecb396ab841bf13ddd6b4d52677fce102fc8303ea078f797f742cba
000000de4fdaf0cdba6067469471137b5d5fe437b65c2183d948daa1bdddeda7
...
```

Main miner logic:
```python
    async def forward(
        self, synapse: template.protocol.Dummy
    ) -> template.protocol.Dummy:
        """
        Processes the incoming 'Dummy' synapse by performing a predefined operation on the input data.
        This method should be replaced with actual logic relevant to the miner's purpose.

        Args:
            synapse (template.protocol.Dummy): The synapse object containing the 'dummy_input' data.

        Returns:
            template.protocol.Dummy: The synapse object with the 'dummy_output' field set to twice the 'dummy_input' value.

        The 'forward' function is a placeholder and should be overridden with logic that is appropriate for
        the miner's intended operation. This method demonstrates a basic transformation of input data.
        """
        _start = time.time()
        _now = _start

        best_matched_nonce = None
        best_matched_hash_dec = None

        while _now - _start < self.forward_time_limit:
            _now = time.time()

            nonce = random.SystemRandom().randint(synapse.input_nonce_left_range_limit,
                                                  synapse.input_nonce_right_range_limit)
            hash_data = (str(synapse.input_block_number) + synapse.input_payload +
                         synapse.imput_lowest_hash + str(nonce))
            hash = hashlib.sha256(hash_data.encode()).hexdigest()

            if hash.startswith('0' * synapse.input_zeroes_acceptance):
                matched_nonce = nonce
                matched_hash_dec = int(hash, 16)

                if not synapse.imput_lowest_hash or matched_hash_dec < int(synapse.imput_lowest_hash, 16):
                    best_matched_nonce = matched_nonce
                    break  # Excellent match, do not need to mine more.

                # Trying to find the best result even it's not an excellent match.
                if not best_matched_hash_dec or best_matched_hash_dec > matched_hash_dec:
                    best_matched_nonce = matched_nonce
                    best_matched_hash_dec = matched_hash_dec

        synapse.output_nonce = best_matched_nonce

        return synapse
```

Main validation logic with rewards calculation where only one miner wins:
```python
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

```

Miner <---> Validator communication protocol:
```python
class Dummy(bt.Synapse):
    # Required request input, filled by sending dendrite caller.
    input_block_number: int
    input_payload: str
    imput_lowest_hash: str
    input_nonce_left_range_limit: int
    input_nonce_right_range_limit: int
    input_zeroes_acceptance: int

    # Optional request output, filled by recieving axon.
    output_nonce: typing.Optional[int] = None
```

---

# Testing output

Validator info
```
miner_uids = tensor([1, 0, 2])
responses = [959447406921, 627152916782, None]
self.scores = tensor([0.1874, 0.6207, 0.0000])
rewards = tensor([0., 1., 0.])
miner_uids = tensor([0, 2, 1])
responses = [861468504410, None, 162961849740]
self.scores = tensor([0.2686, 0.5586, 0.0000])
rewards = tensor([1., 0., 0.])
miner_uids = tensor([2, 1, 0])
responses = [None, 585666259813, 807281306476]
self.scores = tensor([0.3418, 0.5028, 0.0000])
rewards = tensor([0., 1., 0.])
miner_uids = tensor([1, 0, 2])
responses = [None, 325178953147, None]
self.scores = tensor([0.3076, 0.5525, 0.0000])
rewards = tensor([0., 1., 0.])
miner_uids = tensor([1, 0, 2])
responses = [None, 446413583199, None]
self.scores = tensor([0.3768, 0.4972, 0.0000])
rewards = tensor([0., 1., 0.])
miner_uids = tensor([1, 2, 0])
```

Miner0 after receiving reward
```
                                                                     Wallet - miner0:5DxsF2xuwtxSUK7D13pWNtUQbmVpzTrUP3uBeWq5cp9uewyK                                                                     
Subnet: 1                                                                                                                                                                                                 
COLDKEY  HOTKEY   UID  ACTIVE   STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS   EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON                HOTKEY_SS58                                     
miner0   default  0      True   85.76990  0.57948  1.00000    0.57948    0.57948    0.00000   237_589_749  0.00000        *      875  37.45.255.187:8091  5C5gHny94g6SqZAH2tWvURUn47qseryyQzpnKiixW8KJmkFR
1        1        1            τ85.76990  0.57948  1.00000    0.57948    0.57948    0.00000  ρ237_589_749  0.00000                                                                                        
                                                                                          Wallet balance: τ299.0                                                                                          
root@6a5200414671:~#
```

Miner1 after receiving reward
```
                                                                     Wallet - miner1:5DLFkPyMDGM4yrsxtbkoFMXMJ8RMBWvW47S4FoDBuZ48Tn8C                                                                     
Subnet: 1                                                                                                                                                                                                 
COLDKEY  HOTKEY   UID  ACTIVE   STAKE(τ)     RANK    TRUST  CONSENSUS  INCENTIVE  DIVIDENDS   EMISSION(ρ)   VTRUST  VPERMIT  UPDATED  AXON                HOTKEY_SS58                                     
miner1   default  1      True   62.24093  0.42051  1.00000    0.42051    0.42051    0.00000   172_412_538  0.00000        *      879  37.45.255.187:8092  5FU6vpLtXkxhqquoArtYgJJQgtyjvjKJ7NtyMj3dGpjNtjnh
1        1        1            τ62.24093  0.42051  1.00000    0.42051    0.42051    0.00000  ρ172_412_538  0.00000                                                                                        
                                                                                          Wallet balance: τ299.0                                                                                          
root@6a5200414671:~#
```

