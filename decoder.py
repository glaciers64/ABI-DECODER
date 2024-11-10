import requests
from evmdasm import EvmBytecode
from termcolor import cprint
from tqdm import tqdm
from time import sleep
from json import JSONDecodeError, dump
from web3 import Web3

import config

def getHashes(bytecode) -> list:
    opcodes = EvmBytecode(bytecode).disassemble()

    hashes = set()
    for i in range(len(opcodes) - 3):
        if (
            opcodes[i].name == "PUSH4"
            and opcodes[i + 1].name == "EQ"
            and opcodes[i + 2].name == "PUSH2"
            and opcodes[i + 3].name == "JUMPI"
        ):
            hashes.add(opcodes[i].operand)
    return list(hashes)

def getSignature(hash, retry_limit=5):
    url = f'https://www.4byte.directory/api/v1/signatures/?hex_signature={hash}'
    for attempt in range(retry_limit):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Kiểm tra nếu lỗi HTTP
            results = response.json().get('results', [])
            results.sort(key=lambda r: r['created_at'])
            return (True, [m['text_signature'] for m in results])
        except (JSONDecodeError, requests.RequestException):
            cprint(f'Retry {attempt + 1}/{retry_limit} for hash {hash}', 'yellow')
            sleep(1)
    return (False, None)

def getFunction(hash, sign):
    if not sign:
        cprint(f'No match found for hash {hash}', 'red')
        return None
    if len(sign) > 2:
        print(f'Multiple matches found for hash {hash}:', ', '.join(sign))
    return sign[0]

def getAbiForFunc(sign):
    name, sign = sign[0].split('(', 1)
    args = sign[:-1].split(',')
    if args == ['']:
        args = []
    return {
        "type": "function",
        "name": name,
        "inputs": [{"type": t} for t in args],
        "outputs": [{"type": "unknown"}],
    }

def decodeABI(rpc, address, output_file="ABI.json"):
    w3 = Web3(Web3.HTTPProvider(rpc))

    bytecode = w3.eth.get_code(Web3.to_checksum_address(address))
    hashes = getHashes(bytecode)

    signatures = {}

    cprint('Decoding hashes...', 'cyan')
    for hash in tqdm(hashes):
        (status, signature_for_hash) = getSignature(hash)
        while not status:
            sleep(1)
            (status, signature_for_hash) = getSignature(hash)
        signatures[hash] = signature_for_hash

    abi = []
    functions = []
    for hash, sign in signatures.items():
        func = getFunction(hash, sign)
        if not func: continue
        functions.append(func)
        abi.append(getAbiForFunc(sign))
    
    cprint('Initialized interface with functions:', 'green')
    for func in sorted(functions):
        print('   ', func)
    
    cprint('\nABI for contract:', 'green')
    print(abi)

    with open(output_file, 'w') as f:
        dump(abi, f, indent=4)
    cprint(f'ABI has been saved to {output_file}', 'cyan')
