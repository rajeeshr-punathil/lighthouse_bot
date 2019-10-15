#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A bot to find the nearest lighthouse.
Once started, this will run until we press Ctrl-C on the command line.

Commands supported:
    /start
    /next
    /prev
    /bye

Inputs supported:
    Country (Select from Menu)
    State (Select from Menu)
    Location.
"""

from dotenv import load_dotenv
import json
import logging
from math import cos, asin, sqrt
import os
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, 
                          Filters, ConversationHandler)

load_dotenv()

# Keep the data files inside a .data directory.
with open('.data/lighthouses.json') as lhfile:
    LIGHTHOUSES = json.load(lhfile)

with open('.data/countries.json') as ctryfile:
    COUNTRIES = json.load(ctryfile)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Integer constants
COUNTRY, STATE, LOCATION, NEXT, PREV = range(5)

def start(update, context):
    """Handle the first command user runs: /start"""
    logger.info('Starting the search..')
    chat_id = update.message.chat_id
    user = update.message.from_user
    country_keyboard = [[country["name"] for country in COUNTRIES]]
    update.message.reply_text('Hi %s.\nWelcome to Lighthouse Bot.\n'
                              'Let\'s find the lighthouse nearest to you.\n'
                              'Send /bye anytime you want to stop searching.\n\n'
                              'Choose the country you\'re in now:' % user.first_name,
                              reply_markup=ReplyKeyboardMarkup(country_keyboard,
                                                               one_time_keyboard=True))
    return COUNTRY

def get_country(update, context):
    """Get the chosen country and prepare the state list to choose from."""
    user = update.message.from_user
    country_name = update.message.text
    country = list(filter(lambda c: c["name"] == country_name, COUNTRIES))[0]
    state_keyboard = [[state["name"] for state in country["states"]]]
    context.chat_data['input'] = {'country': country}
    logger.info('Country chosen by %s: %s', user.first_name, country_name)
    update.message.reply_text('Country chosen: %s.\n\n'
                              'Choose the state you\'re in:' % country_name,
                              reply_markup=ReplyKeyboardMarkup(state_keyboard,
                                                               one_time_keyboard=True))
    return STATE

def get_state(update, context):
    """Get the chosen state and redirect user to choose location."""
    user = update.message.from_user
    state_name = update.message.text
    country = context.chat_data['input']['country']
    state = list(filter(lambda c: c["name"] == state_name, country["states"]))[0]
    context.chat_data['input']['state'] = state
    logger.info('State chosen by %s: %s', user.first_name, state_name)
    update.message.reply_text('State chosen: %s.\n\n'
                              'Send your location:' % state_name,
                              reply_markup=ReplyKeyboardRemove())
    return LOCATION

def get_location(update, context):
    """Get the location and find nearest lighthouses."""
    user = update.message.from_user
    logger.info('Location received.')
    user_location = update.message.location
    context.chat_data['input']['latitude'] = user_location.latitude
    context.chat_data['input']['longitude'] = user_location.longitude
    # Now its time to query the DB and load result to context.chat_data.
    load_nearest(context)
    return get_next(update, context)

def get_distance(lhouse, iput):
    """Find the distance between given lighthouse and user's chosen location.
    Haversine formula is used.
    """
    lh_lat = lhouse['latitude']
    lh_long = lhouse['longitude']
    ip_lat = iput['latitude']
    ip_long = iput['longitude']

    p = 0.017453292519943295 # Pi/180
    a = (0.5 - cos((lh_lat - ip_lat) * p) / 2 + 
         cos(ip_lat * p) * cos(lh_lat * p) * (1 - cos((lh_long - ip_long) * p)) / 2)
    return 12742 * asin(sqrt(a)) # 2*R*asin

def load_nearest(context):
    """Get 5 nearest lighthouses for the chosen country, state and location."""
    country_name = context.chat_data['input']['country']["name"]
    state_name = context.chat_data['input']['state']["name"]
    latitude = context.chat_data['input']['latitude']
    longitude = context.chat_data['input']['longitude']
    lhouses = list(filter(
        lambda x: x['country'] == country_name and x['state'] == state_name,
        LIGHTHOUSES
    ))
    result = []
    for lhouse in lhouses:
        result.append({
            'name': lhouse['name'],
            'latitude': lhouse['latitude'],
            'longitude': lhouse['longitude'],
            'distance': get_distance(lhouse, context.chat_data['input'])
        })
    sorted_result = sorted(result, key=lambda x: x['distance'])
    context.chat_data["result"] = sorted_result[:5]
    context.chat_data['result_index'] = -1

def get_next(update, context):
    """Return the next lighthouse in queue."""
    # End the conversation if no lighthouse found for the given country/state.
    if not context.chat_data.get('result', None):
        update.message.reply_text('No more lighthouses found!'
                                  ' You can try again with /start command.')
        return ConversationHandler.END
    index = min(context.chat_data['result_index'] + 1,
                len(context.chat_data['result']) - 1)
    context.chat_data['result_index'] = index
    nearest = context.chat_data['result'][index]
    index_text = {
        1: '',
        2: 'second ',
        3: 'third '
    }.get(index + 1, '%dth ' % (index + 1))
    logger.info("User checking the %s result..", index_text)
    message = (update.message
        .reply_text('Your %snearest lighthouse is %s at:' % (index_text,
                                                             nearest['name']))
        .reply_location(nearest['latitude'], nearest['longitude'])
        .reply_text('Satisfied? Stop search by /bye command:'))
    if index >= len(context.chat_data['result']) - 1:
        message.reply_text('Find the previous result by /prev command:')
        return PREV
    message.reply_text('Already visited? Find the next by /next command:')
    return NEXT

def get_prev(update, context):
    """Return the previous lighthouse result in queue."""
    # End the conversation if no lighthouse found for the given country/state.
    if not context.chat_data.get('result', None):
        update.message.reply_text('No more lighthouses found!'
                                  ' You can try again with /start command.')
        return ConversationHandler.END
    index = max(context.chat_data['result_index'] - 1, 0)
    context.chat_data['result_index'] = index
    nearest = context.chat_data['result'][index]
    index_text = {
        1: '',
        2: 'second ',
        3: 'third '
    }.get(index + 1, '%dth ' % (index + 1))
    logger.info("User checking the %s result..", index_text)
    message = (update.message
        .reply_text('Your %snearest lighthouse is %s at:' % (index_text,
                                                             nearest['name']))
        .reply_location(nearest['latitude'], nearest['longitude'])
        .reply_text('Satisfied? Stop search by /bye command:'))
    if index <= 0:
        message.reply_text('Already visited? Find the next by /next command:')
        return NEXT
    message.reply_text('Find the previous result by /prev command:')
    return PREV

def bye(update, context):
    """Command to stop search."""
    user = update.message.from_user
    update.message.reply_text('Bye %s. See you later.' % user.first_name,
                               reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def error(update, context):
    """Now just logging the error."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Initiate the botserver and start polling for the updates"""
    logger.info('Starting the bot server..')
    # Create a .env file and store the token there as TELEGRAM_TOKEN.
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    logger.info('Created the Updater.')
    dp = updater.dispatcher
    # Calling them stages so as not to confuse them with country.states.
    stages = {COUNTRY: [MessageHandler(Filters.text, get_country)],
              STATE: [MessageHandler(Filters.text, get_state)],
              LOCATION: [MessageHandler(Filters.location, get_location)],
              NEXT: [CommandHandler('next', get_next)],
              PREV: [CommandHandler('prev', get_prev)]}
    conv_handler = ConversationHandler(entry_points=[CommandHandler('start', start)],
                                       states=stages,
                                       fallbacks=[CommandHandler('bye', bye)])
    dp.add_handler(conv_handler)
    logger.info('Added the handler set.')
    dp.add_error_handler(error)
    logger.info('Added the error handler.')

    updater.start_polling()
    logger.info("Started polling.")
    updater.idle()

if __name__ == "__main__":
    main()
