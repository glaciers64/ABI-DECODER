import decoder
import config

if __name__ == '__main__':
    decoder.decodeABI(
        rpc=config.rpc, 
        address=config.address,
    )
