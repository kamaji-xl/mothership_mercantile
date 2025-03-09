import zmq
import random
import json
from datetime import datetime
import re

KCR = 'kcr'


def apply_cost_mod(cost):
    cost, mod = parse_cost(cost)

    if mod == KCR:
        cost = int(cost) * 1000

    return cost


def parse_cost(cost):
    match = re.match(r'(\d+)(\D+)', cost)
    if match:
        return match.groups()
    return None


def complete_transaction(req, log):
    command = req['command']
    item_name = req['item_name']
    qty = req['qty']
    cost = req['cost']
    cost = apply_cost_mod(cost)
    char_name = req['char_name']
    starting_balance = req['balance']
    new_balance = 0
    date_time = datetime.now()
    total_cost = int(qty) * int(cost)

    if command == "buy":
        cost = -int(cost)
        new_balance = int(starting_balance) + int(cost) * int(qty)
        total_cost = -total_cost
        if new_balance < 0:
            return {
                "status": "Insufficient funds",
            }
    elif command == "sell":
        new_balance = int(starting_balance) + int(cost) * int(qty)

    if char_name not in log:
        log[char_name] = {'transaction_count': 0, 'transactions': []}

    log[char_name]['transaction_count'] += 1

    transaction_details = {
        "number": log[char_name]['transaction_count']-1,
        "item": item_name,
        "action": command,
        "qty": qty,
        "cost_per_item": cost,
        "total_cost": total_cost,
        "pre_balance": starting_balance,
        "post_balance": new_balance,
        "date": date_time.strftime("%m-%d-%Y"),
    }

    log[char_name]['transactions'].append(transaction_details)
    transaction_details.update({"status": "success"})

    return transaction_details


def merc_req_handler(req, log):
    if req["command"] == "buy" or req["command"] == "sell":
        res = complete_transaction(req, log)
    elif req["command"] == "pull_hist":
        res = pull_history(req, log)
    else:
        res = {"status": "error"}

    return res


def print_transactions(details):
    for key, value in details.items():
        print(f"{key}: {value}")


def pull_history(req, log):
    char_name = req['char_name']
    t_type = req['type']

    if t_type == 'all':
        try:
            t_list = []
            for txn in log[char_name]['transactions']:
                transaction = [txn['number'], txn['item'], txn['action'], txn['qty'], txn['cost_per_item'],
                               txn['total_cost'], txn['pre_balance'], txn['post_balance'], txn['date']]
                t_list.append(transaction)
            res = {"status": "success", "transactions": t_list}

        except KeyError as e:
            print(f"KeyError: {e}")
            res = {"status": "error"}
    else:
        try:
            t_list = []
            print(t_type)
            for txn in log[char_name]['transactions']:
                print("test", txn)
                if txn['item'] == t_type:
                    transaction = [txn['number'], txn['item'], txn['action'], txn['qty'], txn['cost_per_item'],
                                   txn['total_cost'], txn['pre_balance'], txn['post_balance'], txn['date']]
                    t_list.append(transaction)
            res = {"status": "success", "transactions": t_list}

        except KeyError as e:
            print(f"KeyError: {e}")
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
            print("Received request:")
            for key, value in request_json.items():
                print(f"\t{key}: {value}")
            response = merc_req_handler(request_json, transaction_log)
            print(f"\nsending response:")
            for key in response.keys():
                print(f"\t{key}: {response[key]}")
            socket.send_json(response)
        except zmq.error.ZMQError as e:
            print("ZMQ Error:", e)
