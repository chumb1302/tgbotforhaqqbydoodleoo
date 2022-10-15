from multiprocessing import context
from subprocess import call
from time import time
import telebot
from enum import auto
from telebot import types
from web3 import Web3
from typing import Optional
from hexbytes import HexBytes
from web3.middleware import geth_poa_middleware
from datetime import datetime
bot = telebot.TeleBot('5695547707:AAHQsmTD8J5zQOVipUrlXVKIwsmeQJ1ltNM')

context = {}

address = ''


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 'Привет! \nДля того чтобы воспользоваться краном тебе нужно узнать свой EIP-55 адрес. \nНапиши /help')


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(
        message.chat.id, 'Как узнать свой EIP-55 адрес? - /faucetinfo \nВоспользоваться краном - /faucet \nСсылка на оф. документацию - /docs \nСсылка на оф. кран - /mainfaucet')


@bot.message_handler(commands=['faucetinfo'])
def faucetinfo(message):
    bot.send_message(message.chat.id, 'На сервере где установлена нода командой haqqd debug addr <wallet_addr> узнаем наш Address (EIP-55). (<wallet_addr> заменить на своей действующий haqq адрес)')


@bot.message_handler(commands=['docs'])
def faucetinfo(message):
    bot.send_message(
        message.chat.id, 'Документация - https://docs.haqq.network/')


@bot.message_handler(commands=['mainfaucet'])
def faucetinfo(message):
    bot.send_message(
        message.chat.id, 'Кран от разработчиков - https://testedge2.haqq.network/')


@bot.message_handler(commands=['faucet'])
def faucet(message):
    last_command_use_time = context.get(message.chat.id)
    if not last_command_use_time or (datetime.now() - last_command_use_time).days > 1:
        message = bot.send_message(
            message.chat.id, 'Введите свой EIP-55 адрес:')
        bot.register_next_step_handler(message, get_address)
        context[message.chat.id] = datetime.now()
    else:
        bot.send_message(
            message.chat.id, 'Вы уже запращивали тестовые токены. Возвращайтесь через 24 часа:)')


def get_address(message):
    global address
    address = message.text
    txs_markup = types.InlineKeyboardMarkup()
    txs_yes = types.InlineKeyboardButton(
        text='Все верно', callback_data='txs_yes')
    txs_no = types.InlineKeyboardButton(
        text='Я хочу изменить адрес', callback_data='txs_no')
    txs_markup.add(txs_yes, txs_no)
    question = 'Проверь правильность введенного тобой адреса - '+address+''
    global message_id_to_del
    message_id_to_del = bot.send_message(message.from_user.id, text=question,
                                         reply_markup=txs_markup).message_id


@bot.callback_query_handler(func=lambda call: call.data == 'txs_yes' or 'txs_no')
def callback_txs(call):

    if call.data == "txs_yes":
        try:
            haqqTestnetRPC = "https://rpc.eth.testedge2.haqq.network"
            web3 = Web3(Web3.HTTPProvider(haqqTestnetRPC))

            from_address = '0x890675D1d55d07D6F40434D07ed8FaeaecE2e6a8' #metamask address from which tokens will be sent 

            web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            web3.eth.account.enable_unaudited_hdwallet_features()

            mnemonic = 'drink cheese...' #mnemonic phrase of the address from which tokens will be sent

            account = web3.eth.account.from_mnemonic(mnemonic)
            private_key = account.privateKey

            def build_txn(
                *,
                web3: Web3,
                from_address: str,
                address: str,
                amount: float,
            ) -> dict[str, int | str]:
                gas_price = web3.eth.gas_price
                gas = 2_000_000
                nonce = web3.eth.getTransactionCount(from_address)
                txn = {
                    'chainId': web3.eth.chain_id,
                    'from': from_address,
                    'to': address,
                    'value': int(Web3.toWei(amount, 'ether')),
                    'nonce': nonce,
                    'gasPrice': gas_price,
                    'gas': gas,
                }
                return txn

            transaction = build_txn(
                web3=web3,
                from_address=from_address,
                address=address,
                amount=0.1
            )

            signed_txn = web3.eth.account.sign_transaction(
                transaction, private_key)
            txn_hash = web3.eth.sendRawTransaction(signed_txn.rawTransaction)
            print(txn_hash.hex())

            bot.send_message(call.message.chat.id,
                             'На ваш адрес успешно отправлено 0.1 ISLM')
            bot.delete_message(call.message.chat.id, message_id_to_del)
        except Exception:
            bot.send_message(call.message.chat.id,
                             'Введите корректный адрес:')
            bot.delete_message(call.message.chat.id, message_id_to_del)
            bot.register_next_step_handler(call.message, get_address)
    elif call.data == "txs_no":
        message = bot.send_message(
            call.message.chat.id, 'Введите свой EIP-55 адрес:')
        bot.register_next_step_handler(message, get_address)


bot.polling(none_stop=True, interval=0)
