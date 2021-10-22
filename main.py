import asyncio

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from loguru import logger

from sqliter import SQLighter
from utils import get_floor_price_nft

COLLECTION_URL = 'https://qzlsklfacc.medianetwork.cloud/nft_for_sale?collection=%s'
NFT_URL = 'https://solanart.io/search/?token=%s'

logger.add('app.log', format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

bot = Bot(token='BOT_TOKEN')  # <- Your telegram bot token
dp = Dispatcher(bot)

db = SQLighter('nft_collection')


@logger.catch
@dp.message_handler(commands=['watchlist'])
async def show_watchlist(message: types.Message):
    logger.info('Show watchlist')
    watchlist = db.get_watchlist(message.chat.id)
    result = 'Watchlist:\n\n'
    for el in watchlist:
        if el[2]:  # started or not
            result += f'{el[0]} - max price {el[1]}\n'
        else:
            result += f'{el[0]} - not started\n'
    await message.answer(result)


@logger.catch
@dp.message_handler(commands=['add'])
async def add_collection(message: types.Message):
    logger.info('Adding collection')
    collection_name = message.get_args()
    if len(collection_name.split()) != 1:
        await message.answer('Invalid cmd call!\nExample:\n/add coll_name')
        return
    collection = await fetch_collection(collection_name)
    if type(collection) is not list:
        await message.answer('Invalid collection name!')
        return
    if db.collection_exists(collection_name, message.chat.id):
        await message.answer('The collection has already been added!')
        return
    db.add_collection(collection_name, message.chat.id)
    logger.info(f'{collection_name} collection added')
    await message.answer(f'{collection_name} collection added!')


@logger.catch
@dp.message_handler(commands=['del'])
async def del_collection(message: types.Message):
    logger.info('Delete collection')
    collection_name = message.get_args()
    if len(collection_name.split()) != 1:
        await message.answer('Invalid cmd call!\nExample:\n/del coll_name')
        return
    if not db.collection_exists(collection_name, message.chat.id):
        await message.answer('Collection does not exist in watchlist!')
        return
    db.delete_collection(collection_name, message.chat.id)
    logger.info(f'{collection_name} collection deleted')
    await message.answer('Collection deleted!')


@logger.catch
@dp.message_handler(commands=['start'])
async def start_watch(message: types.Message):
    logger.info('Start watch')
    args = message.get_args().split()
    if len(args) != 2:
        await message.answer('Invalid cmd call!\nExample:\n/start coll_name max_price')
        return
    if not db.collection_exists(args[0], message.chat.id):
        collection = await fetch_collection(args[0])
        if type(collection) is not list:
            await message.answer('Invalid collection name!')
            return
        db.add_collection(args[0], message.chat.id)
    if not args[1].replace('.', '', 1).isdigit():
        await message.answer('Invalid price format')
        return
    db.start_watch(args[0], args[1], message.chat.id)
    logger.info(f'Started watching {args[0]} with max price {args[1]}')
    await message.answer(f'{args[0]} started with max price {args[1]}')


@logger.catch
@dp.message_handler(commands=['stop'])
async def stop_watch(message: types.Message):
    logger.info('Stop watch')
    collection_name = message.get_args()
    if len(collection_name) == 0:
        logger.info('Stop all alerts')
        db.stop_all(message.chat.id)
        await message.answer('All alerts stopped!')
        return
    if len(collection_name.split()) > 1:
        await message.answer('Invalid cmd call!\nExample:\n/stop coll_name')
        return
    if not db.collection_exists(collection_name, message.chat.id):
        await message.answer('Collection does not exist in watchlist!')
        return
    db.stop_watch(collection_name, message.chat.id)
    logger.info(f'Stopped watching {collection_name}')
    await message.answer(f'{collection_name} stopped!')


@logger.catch
async def monitor():
    logger.info('Monitoring started')
    while True:
        collections = db.get_collections()
        for collection in collections:
            name, chat_id, max_price, last_nft_id = collection
            res = await fetch_collection(name)
            floor_price_nft = get_floor_price_nft(res)
            if floor_price_nft['price'] <= max_price and floor_price_nft['id'] != last_nft_id:
                db.update_last_nft_id(name, chat_id, floor_price_nft['id'])
                logger.info(f'NEW NFT ALERT: {floor_price_nft}')
                await bot.send_message(chat_id, NFT_URL % floor_price_nft['token_add'])
            await asyncio.sleep(20)
        await asyncio.sleep(10)


async def on_bot_start_up(dispatcher: Dispatcher) -> None:
    """List of actions which should be done before bot start"""
    asyncio.create_task(monitor())


@logger.catch
async def fetch_collection(name):
    session = aiohttp.ClientSession()
    async with session.get(COLLECTION_URL % name) as res:
        collection = await res.json()
    await session.close()
    return collection


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_bot_start_up)
