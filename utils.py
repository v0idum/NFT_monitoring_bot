def _filtered(collection: list):
    for NFT in collection:
        for nft in collection:
            if NFT['token_add'] == nft['token_add'] and NFT['id'] != nft['id']:
                if NFT['id'] > nft['id']:
                    collection.remove(nft)
                else:
                    collection.remove(NFT)
                    break
    return collection


def get_floor_price_nft(collection: list):
    return min(_filtered(collection), key=lambda e: e['price'])
