import requests
import time
from json import loads as load
import statistics
import math


def getLeague():
    leagues = requests.get('http://api.pathofexile.com/leagues')
    leagues = leagues.json()
    current_league = leagues[4]['id']  # current challenge league
    return current_league


def getCurrencies(league):
    response = requests.get(
        'https://poe.ninja/api/data/currencyoverview?league=' + current_league + '&type=Currency')
    currencies = load(response.text)['lines']
    rates = {
        c['currencyTypeName']: c['chaosEquivalent'] for c in currencies
    }
    return rates


def get_category_jewel_price(a, ilvl):
    data_set = {  # structure for API request. All info from https://www.reddit.com/r/pathofexiledev/comments/7aiil7/how_to_make_your_own_queries_against_the_official/ . Absolutely no other documentation
        "query": {
            "status": {
                "option": "online"
            },
            "stats": [{
                "type": "and",
                "filters": [{"id": 'enchant.stat_3948993189', "value": {"option": a['clusterId']}}]
            }],
            "filters": {
                "type_filters": {
                    "filters": {
                        "rarity": {
                            "option": "nonunique"
                        }
                    }
                },
                "misc_filters": {
                    "filters": {
                        "corrupted": {
                            "option": "false"
                        },
                        "ilvl": {
                            "min": ilvl
                        }
                    }
                },
                "trade_filters": {
                    "filters": {
                        "sale_type": {
                            "option": "priced"
                        }
                    }
                }
            }
        },
        "sort": {
            "price": "asc"
        }
    }
    # send the request to API
    print("Sending request...")
    try:
        response = requests.post(
            'https://www.pathofexile.com/api/trade/search/' + current_league, json=data_set)
        response = response.json()
        print("Got response!")
    except Exception as e:
        print(e)
        print("Waiting 60 seconds.")
        time.sleep(60)
    result = response['result']
    id = response['id']
    size = response['total']

    # if there are more than 10 listings, strip all of them away after 10th. We cant request info about items more than 10 items at once
    if size > 10:
        del result[10:]

    # make correct formatting
    if size > 1:
        str1 = ','.join(result)
    else:
        str1 = result

    # time delay, so API wont rate limit me
    time.sleep(0.4)
    # get all actual listings of items
    print("Requesting item info...")
    address = 'https://www.pathofexile.com/api/trade/fetch/' + \
        str(str1) + '?query=' + id
    request = requests.get(address)
    results_json = request.json()
    # list to hold all prices of an item. Later used to calculate medium price
    medium = list()
    print(a['clusterName'])
    print('Listings:' + str(size))
    for p in results_json['result']:
        # conversion for some more valuable currency
        if(p['listing']['price']['currency'] == "exalted"):
            p['listing']['price']['amount'] = p['listing']['price']['amount'] * \
                rates["Exalted Orb"]
            p['listing']['price']['currency'] = "chaos"
        elif(p['listing']['price']['currency'] == "alch"):
            p['listing']['price']['amount'] = p['listing']['price']['amount'] * \
                rates["Orb of Alchemy"]
            p['listing']['price']['currency'] = "chaos"
        if(p['listing']['price']['currency'] == "chaos"):
            medium.append(p['listing']['price']['amount'])
        print("Price: ", p['listing']['price']['amount'],
              " ", p['listing']['price']['currency'], '\n')
    # get the average median of all listed prices for an item
    avg = statistics.median_grouped(medium)
    print("The average median is " + str(round(avg, 2)) + '\n')
    return avg


def getNotablePrice(a, b, query, inp):
    if query == 1:
        ilvl = b['notableLevel']
    else:
        ilvl = max(b[0]['notableLevel'], b[1]['notableLevel'])

    data_set = {  # structure for API request. All info from https://www.reddit.com/r/pathofexiledev/comments/7aiil7/how_to_make_your_own_queries_against_the_official/ . Absolutely no other documentation
        "query": {
            "status": {
                "option": "online"
            },
            "type": "Small Cluster Jewel" if inp == 1 else "Medium Cluster Jewel",
            "stats": [{
                "type": "and",
                "filters": [{"id": b['notableId']}] if query == 1 else [{"id": b[0]['notableId']}, {"id": b[1]['notableId']}]
            }],
            "filters": {
                "type_filters": {
                    "filters": {
                        "rarity": {
                            "option": "nonunique"
                        }
                    }
                },
                "trade_filters": {
                    "filters": {
                        "sale_type": {
                            "option": "priced"
                        }
                    }
                }
            }
        },
        "sort": {
            "price": "asc"
        }
    }
    # time delay, so API won't rate limit me
    time.sleep(0.4)
    # send the request to API
    print("Sending request...")
    try:
        response = requests.post(
            'https://www.pathofexile.com/api/trade/search/' + current_league, json=data_set)
        response = response.json()
        print("Got response!")
    except Exception as e:
        print(e)
        print("Waiting 60 seconds.")
        time.sleep(60)

    result = response['result']
    id = response['id']
    size = response['total']

    # if there are less than 10 listings for an item, we just just skip it (no demand)
    if size < 10:
        print("Not enough items!(" + str(size) + ") Skipping...")
        return 0

    # if there are more than 10 listings, strip all of them away after 10th. We cant request info about items more than 10 items at once
    if size > 10:
        del result[10:]

    # make correct formatting
    if size > 1:
        str1 = ','.join(result)
    else:
        str1 = result

    # get all actual listings of items
    print("Requesting item info...")
    address = 'https://www.pathofexile.com/api/trade/fetch/' + \
        str(str1) + '?query=' + id
    request = requests.get(address)
    results_json = request.json()

    # probability to get an item while crafting. Formula is mostly correct
    if query == 1:
        probability = b['notableWeight']/a['clusterWeightPrefix']
        tries = math.ceil(1 / probability)
        alt_count = tries
        aug_count = math.ceil(alt_count/4)
        craft_price = alt_count * \
            rates["Orb of Alteration"] + aug_count * \
            rates["Orb of Augmentation"]

    else:
        suffixWeight = 14150
        probabilityFirst = b[0]['notableWeight'] / a['clusterWeightPrefix']
        probabilityFirstSecond = b[1]['notableWeight'] / \
            (a['clusterWeightPrefix'] + suffixWeight - b[0]['notableWeight'])
        probabilityFirstSucess = probabilityFirst * probabilityFirstSecond

        probabilitySecond = b[1]['notableWeight'] / a['clusterWeightPrefix']
        probabilitySecondFirst = b[0]['notableWeight'] / \
            (a['clusterWeightPrefix'] + suffixWeight - b[1]['notableWeight'])
        probabilitySecondSucess = probabilitySecond * probabilitySecondFirst

        probability = probabilityFirstSucess + \
            probabilitySecondSucess  # overall probability to hit both

        probability_first = (b[0]['notableWeight'] + b[1]
                             ['notableWeight']) / a['clusterWeightPrefix']
        probability_second = probability/probability_first

        tries = math.ceil(1 / probability)
        regal_count = math.ceil(1 / probability_second)
        scour_count = regal_count - 1
        trans_count = regal_count - 1
        alt_count = tries - trans_count
        aug_count = math.ceil((tries + alt_count) / 4) + 1
        craft_price = alt_count * rates["Orb of Alteration"] + aug_count * rates["Orb of Augmentation"] + regal_count * \
            rates["Regal Orb"] + scour_count * rates["Orb of Scouring"] + \
            trans_count * rates["Orb of Transmutation"]

    jewel_price = get_category_jewel_price(a, ilvl)
    craft_and_jewel_price = craft_price + jewel_price

    # list to hold all prices of an item. Later used to calculate medium price
    medium = list()

    if query == 1:
        print(b['notableName'] + ": " + str(round(probability*100, 3)) + "%" +
              " Cost for rerolls: " + str(round(craft_price, 2)) + " Tries: " + str(round(tries)))
        print('Listings:' + str(size))
    else:
        print(b[0]['notableName'] + " and " + b[1]['notableName'] + ": " + str(round(probability*100, 3)
                                                                               ) + "%" + " Cost for rerolls: " + str(round(craft_price, 2)) + " Tries: " + str(round(tries)))
        print('Listings:' + str(size))

    for p in results_json['result']:
        # conversion for some more valuable currency
        if(p['listing']['price']['currency'] == "exalted"):
            p['listing']['price']['amount'] = p['listing']['price']['amount'] * \
                rates["Exalted Orb"]
            p['listing']['price']['currency'] = "chaos"
        elif(p['listing']['price']['currency'] == "alch"):
            p['listing']['price']['amount'] = p['listing']['price']['amount'] * \
                rates["Orb of Alchemy"]
            p['listing']['price']['currency'] = "chaos"
        if(p['listing']['price']['currency'] == "chaos"):
            medium.append(p['listing']['price']['amount'])
        print("Price: ", p['listing']['price']['amount'],
              " ", p['listing']['price']['currency'], '\n')

    # get the average median of all listed prices for an item
    avg = statistics.median_grouped(medium)
    # profit margin
    profit = avg - craft_and_jewel_price
    PPT = profit/tries
    first = (medium[0]+medium[1])/2
    LPPT = (first - craft_and_jewel_price)/tries
    print("The average median is ", round(avg, 2),
          "     Profit:", round(profit, 2), '\n')
    x = {
        'name': b['notableName'] if query == 1 else (b[0]['notableName'] + " and " + b[1]['notableName']),
        'listings': size,
        'tries': round(tries),
        'craft': round(craft_price, 2),
        'first': round(first, 2),
        'average': round(avg, 2),
        'profit': round(profit, 2),
        'PPT': round(PPT, 3),
        # when first item is a lot cheaper than average
        'LPPT': round(LPPT, 3),
        'category': a['clusterName'],
        'request': data_set,
        'category_full': a,
        'notable_full': b,
        'ilvl': ilvl,
        'id': id
    }
    return x


current_league = getLeague()

rates = getCurrencies(current_league)