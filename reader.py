import json
import os
import re
from numpy import mean, sort
from classes import Hand
import csv
import matplotlib.pyplot as plt

# get pattern data
pattern_file = './config/patterns.json'
with open(pattern_file, 'r') as file:
    patterns = json.load(file)

def get_text_files(dirs):
    all_files = []

    for dir in dirs:
        if not os.path.isdir(dir):
            print(f"Error: The directory {dir} does not exist.")
            exit()

        text_files = [f for f in os.listdir(dir) if f.endswith('.txt')]
        text_file_data = []

        for file_name in text_files:
            file_path = os.path.join(dir, file_name)
            try:
                with open(file_path, 'r') as file:
                    text_file_data.append(file.read()[:-2])
            except Exception as e:
                print(f"Error reading file {file_name}: {e}")

        all_files.extend(text_file_data)

    return all_files

def get_hand_list(sessions, user, include_sitting_out=False):
    hand_split_pattern = re.compile(patterns["handSplit"])
    all_hands = []

    for session in sessions:
        hands = re.split(hand_split_pattern, session)
        for hand in hands:
            new_hand = Hand(hand, user)
            if new_hand.position != "sitting out" or include_sitting_out:
                all_hands.append(new_hand)

    return all_hands

def get_player_stats(hands):
    stats = {
        "vpip": 0.,
        "best_hand": "",
        "bb/100": 0.,
        "af": 100.,
        "cprofit": 0.,
        "earliest_hand": "",
        "pfr": 0.
    }

    # basic stats
    stats["vpip"] = round(mean([hand.vpip for hand in hands]), 2)
    stats["pfr"] = round(1-mean([hand.pfr for hand in hands]), 2)
    if sum([hand.calls for hand in hands]) != 0:
        stats["af"] = round((sum([hand.bets for hand in hands]) + sum([hand.raises for hand in hands]))/sum([hand.calls for hand in hands]), 2)
    stats["cprofit"] = round(sum([hand.profit for hand in hands]), 2)
    stats["bb/100"] = round(sum([hand.get_profit_in_bb() for hand in hands]) / len(hands) * 100, 2) if len(hands) > 0 else 0.

    # best hand
    won_with_hands = {}
    for hand in hands:
        if hand.won == True:
            unsuited_hand = hand.hand[0] + hand.hand[2]
            if unsuited_hand in won_with_hands: won_with_hands[unsuited_hand] += 1
            else: won_with_hands[unsuited_hand] = 1
    stats["best_hand"] = max(won_with_hands, key=won_with_hands.get) if len(won_with_hands) > 0 else "Not enough data"

    # earliest hand
    sorted_hands_list = sorted(hands, key=lambda hand: hand.date)
    if len(sorted_hands_list) > 0:
        stats["earliest_hand"] = sorted_hands_list[0].date

    return stats

def save_hands_to_csv(hands, filename='hands_chronological.csv'):
    sorted_hands = sorted(hands, key=lambda hand: hand.date)

    headers = ['Hand ID', 'Timestamp', 'Position', 'Stakes', 'Hand', 'Saw Flop', 'Win', 'Net Profit', 'Profit in BB']

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)

        for hand in sorted_hands:
            writer.writerow([
                hand.id,
                hand.date.strftime("%Y/%m/%d %H:%M:%S"),
                hand.position,
                hand.stakes,
                hand.hand,
                hand.saw_flop,
                "Yes" if hand.won else "No",
                f'${hand.profit}',
                hand.get_profit_in_bb()
            ])

    print(f'Hands saved to {filename} successfully.')

def plot_cumulative_profit(hands, savefig=False):
    hands_sorted = sorted(hands, key=lambda x: x.date)
    
    profits = [hand.profit for hand in hands_sorted]
    
    cumulative_profits = []
    cumulative_profit = 0
    for profit in profits:
        cumulative_profit += profit
        cumulative_profits.append(cumulative_profit)
    
    plt.figure(figsize=(10, 6))
    plt.plot(cumulative_profits, marker='', linestyle='-', color='b')
    plt.title('Cumulative Profit Over Hands')
    plt.xlabel('Hands')
    plt.ylabel('Cumulative Profit ($)')
    plt.grid(True)
    if savefig:
        plt.savefig('Cumulative Profit.png')
    plt.show()
