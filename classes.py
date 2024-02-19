from datetime import datetime
import json
import re

class Hand:
    def __init__(self, rawtext, user):
        self.rawtext = rawtext
        self.user = user
        self.parse_raw_text()

    def parse_raw_text(self):
        # get pattern data
        pattern_file = './config/patterns.json'
        with open(pattern_file, 'r') as file:
            patterns = json.load(file)

        # compiling regex strings
        header_pattern = re.compile(patterns["header"])
        button_pattern = re.compile(patterns["button"])
        position_pattern = re.compile(f'{patterns["position"]} {self.user}')
        blind_pattern = re.compile(f'{self.user} {patterns["blind"]}')
        hand_pattern = re.compile(f'{patterns["hand"]["beforeUser"]} {self.user} {patterns["hand"]["afterUser"]}')
        win_pattern = re.compile(f'{self.user} {patterns["win"]}')
        call_pattern = re.compile(f'{self.user} {patterns["call"]}')
        bet_pattern = re.compile(f'{self.user} {patterns["bet"]}')
        raise_pattern = re.compile(f'{self.user} {patterns["raise"]}')
        fold_pattern = re.compile(f'{self.user} {patterns["fold"]}')
        dead_pattern = re.compile(f'{self.user} {patterns["dead"]}')
        uncalled_pattern = re.compile(f'{patterns["uncalledBet"]} {self.user}')
        community_pattern = re.compile(f'{patterns["community"]}')

        spent_amt = 0.0

        # get date and stakes
        header = re.search(header_pattern, self.rawtext)
        date = header.group(3)
        stakes = header.group(2)
        id = int(header.group(1))

        # get hand
        hand = re.search(hand_pattern, self.rawtext)
        if not hand:
            self.id = id
            self.date = self.parse_date(date)
            self.position = "sitting out"
            self.stakes = stakes
            self.hand = ""
            self.won = False
            self.vpip = False
            self.saw_flop = False
            self.money_spent = 0.
            self.money_won = 0.
            self.profit = 0.
            self.calls = 0
            self.bets = 0
            self.raises = 0
            self.pfr = False
            self.community = ""
            return
        hand = hand.group(1)

        # get position
        position = "other"
        # check button
        button = int(re.search(button_pattern, self.rawtext).group(1))
        seat = int(re.search(position_pattern, self.rawtext).group(1))
        position = "button" if button == seat else position
        # check blinds
        blind = re.search(blind_pattern, self.rawtext)
        if blind:
            blind_type = f"{blind.group(1)} blind"
            position = blind_type

        # check win
        win = re.search(win_pattern, self.rawtext)
        win_status = bool(win)
        win_amt = float(win.group(1)) if win_status else 0.

        # check vpip
        pre_summary = self.rawtext.split("*** SUMMARY ***")[0]
        calls, bets, raises = 0, 0, 0
        for match in re.finditer(call_pattern, pre_summary):
            spent_amt += float(match.group(1))
            calls += 1
        for match in re.finditer(bet_pattern, pre_summary):
            spent_amt += float(match.group(1))
            bets += 1
        for match in re.finditer(raise_pattern, pre_summary):
            spent_amt += float(match.group(1))
            raises += 1
        vpip = spent_amt > 0

        # stats for AF
        self.calls = calls
        self.bets = bets
        self.raises = raises

        # check fold before flop
        pre_flop = self.rawtext.split("*** FLOP ***")
        sf = re.search(fold_pattern, pre_flop[0]) == None
        if len(pre_flop) <= 1: sf = False

        # check raise before flop
        pfr = re.search(raise_pattern, pre_flop[0]) == None

        # hand spending on deads and blinds
        stakes_pair = (float(stakes.split('/')[0][1:]), float(stakes.split('/')[1][1:]))
        if position == "small blind": spent_amt += stakes_pair[0]
        elif position == "big blind": spent_amt += stakes_pair[1]
        dead = re.search(dead_pattern, self.rawtext)
        if dead: spent_amt += float(dead.group(1))

        # money won from uncalled bets
        uncalled_bet = re.search(uncalled_pattern, self.rawtext)
        if uncalled_bet: win_amt += float(uncalled_bet.group(1))

        # rounding before finalizing
        spent_amt = round(spent_amt, 2)
        win_amt = round(win_amt, 2)
        profit = win_amt - spent_amt

        # get community cards
        community = re.search(community_pattern, self.rawtext)
        comm_cards = ""
        if community: 
            comm_cards = community.group(1)

        self.id = id
        self.date = self.parse_date(date)
        self.position = position
        self.stakes = stakes
        self.hand = hand.replace(" ", "")
        self.won = True if profit > 0 else False
        self.vpip = vpip
        self.saw_flop = sf
        self.money_spent = spent_amt
        self.money_won = win_amt
        self.profit = profit
        self.pfr = pfr
        self.community = comm_cards.replace(" ", "")

    def parse_date(self, date_str):
        # Parse the date string to a datetime object
        return datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S %Z")

    def set_date(self, date_str):
        self.date = self.parse_date(date_str)

    def __str__(self):
        return f'__________Hand #{self.id} ({self.stakes})__________\nTimestamp: {self.date}\nPosition: {self.position}\nHand: {self.hand}\nWin: {"Yes" if self.won else "No"}\nNet: ${self.profit}'
    
    def get_profit_in_bb(self):
        bb_amt = float(self.stakes.split('/')[1][1:])
        return self.profit/bb_amt