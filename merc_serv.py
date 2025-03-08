import zmq
import random
import json
from datetime import datetime
import re

KCR = 'kcr'


def apply_cost_mod(cost):
    cost, mod = parse_cost(cost)
    print(cost, mod)

    if mod == KCR:
        cost = int(cost) * 1000

    return cost


def parse_cost(cost):
    match = re.match(r'(\d+)(\D+)', cost)
    if match:
        return match.groups()
    return None


def buy_item(req, log):
    item_name = req['item_name']
    qty = req['qty']
    cost = req['cost']
    print(cost)
    cost = apply_cost_mod(cost)
    char_name = req['char_name']
    starting_balance = req['balance']
    date_time = datetime.now()

    new_balance = int(starting_balance) - int(cost) * int(qty)

    if char_name not in log:
        log[char_name] = {'transaction_count':0, 'transactions': []}

    transaction_number = log[char_name]['transaction_count']
    log[char_name]['transaction_count'] += 1

    transaction_details = {
        "item": item_name,
        "qty": qty,
        "cost_per_item": cost,
        "total_cost": cost * qty,
        "pre_balance": starting_balance,
        "post_balance": new_balance,
        "date": str(date_time)
    }

    log[char_name]['transactions'].append(transaction_details)

    return transaction_details


def merc_req_handler(req, log):
    if req["command"] == "buy":
        res = buy_item(req, log)
    elif req["command"] == "sell":
        pass
    else:
        res = {"status": "error"}

    return res


if __name__ == "__main__":
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:6700")

    transaction_log = {}

    print(f"Listening on port tcp://localhost:6700")

    while True:
        try:
            request_json = socket.recv_json()
            print(request_json)
            response = merc_req_handler(request_json, transaction_log)
            print(f"\nsending response:")
            for key in response.keys():
                print(f"\t{key}: {response[key]}")
            socket.send_json(response)
        except zmq.error.ZMQError as e:
            print("ZMQ Error:", e)
