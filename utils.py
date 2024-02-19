from datetime import datetime


def format_card_string(string):
    '''Takes a string of cards and formats them visually. Card strings can have any number of cards and must be in the form 8sTc...'''
    if len(string) % 2 != 0: raise ValueError("Card string is not formatted correctly (card string length should be even).")
    cards = len(string) // 2
    formatted_cards = []
    for i in range(cards):
        curr_card = string[i*2 : i*2 + 2]
        # Verify card value
        try:
            card_value = int(curr_card[0])
            if card_value < 2: raise ValueError(f"Card string is not formatted correctly ({card_value} found at position {i*2}).")
        except:
            if curr_card[0] != 'A' and curr_card[0] != 'T' and curr_card[0] != 'J' \
            and curr_card[0] != 'Q' and curr_card[0] != 'K':
                raise ValueError(f"Card string is not formatted correctly ({curr_card[0]} found at position {i*2}).")
        
        # Verify card suit
        if curr_card[1] != 's' and curr_card[1] != 'c' and curr_card[1] != 'd' and curr_card[1] != 'h':
            raise ValueError(f"Card string is not formatted correctly ({curr_card[1]} found at position {i*2 + 1}).")
        
        match curr_card[1]:
            case 's':
                formatted_cards.append(f'{curr_card[0]}♠')
            case 'c':
                formatted_cards.append(f'{curr_card[0]}♣')
            case 'd':
                formatted_cards.append(f'{curr_card[0]}♦')
            case 'h':
                formatted_cards.append(f'{curr_card[0]}♥')

    s = " "
    return s.join(formatted_cards)

def get_sorted_hands(hands, reverse=True):
    '''Returns the list of hands sorted based on date.'''
    return sorted(hands, key=lambda hand: hand.date, reverse=reverse)

def format_profit_value(profit):
    '''Returns a string that correctly displays an amount of money (positive or negative).'''
    profit = round(profit, 2)
    return f'-${abs(profit)}' if profit < 0 else f'${profit}'

def format_date_string(date_str):
    '''Takes a date string and formats it in an easy to read way.'''
    input_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    if input_date.date() == now.date():
        return input_date.strftime("%H:%M")
    elif input_date.year == now.year:
        return input_date.strftime("%B %d")
    else:
        return input_date.strftime("%B %Y")
