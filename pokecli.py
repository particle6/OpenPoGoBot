#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pgoapi - Pokemon Go API
Copyright (c) 2016 tjado <https://github.com/tejado>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.

Author: tjado <https://github.com/tejado>
"""

import os
import re
import json
import requests
import argparse
import time
import ssl
import logging
import sys
import codecs
from pokemongo_bot import logger
from getpass import getpass
from pokemongo_bot import PokemonGoBot
from pokemongo_bot.cell_workers.utils import print_green, print_yellow, print_red

if sys.version_info >= (2, 7, 9):
    ssl._create_default_https_context = ssl._create_unverified_context


def init_config():
    parser = argparse.ArgumentParser()

    # Read passed in Arguments
    parser.add_argument("-j",
                        "--config-json",
                        help="Load a config JSON file. Overrides all other command line options if specified.",
                        type=str,
                        default=None,
                        dest="json")
    parser.add_argument("-a",
                        "--auth-service",
                        help="Auth Service ('ptc' or 'google')",
                        dest="auth_service")
    parser.add_argument("-u", "--username", help="Username", dest="username")
    parser.add_argument("-p", "--password", help="Password", dest="password")
    parser.add_argument("-l", "--location", help="Location", dest="location")
    parser.add_argument("-lc",
                        "--location-cache",
                        help="Bot will start at last known location",
                        action="store_true",
                        dest="location_cache")
    parser.add_argument("-m",
                        "--mode",
                        help="Farming Mode",
                        type=str,
                        default="all",
                        dest="mode")
    parser.add_argument(
        "-w",
        "--walk",
        help="Walk instead of teleport with given speed (meters per second, e.g. 2.5)",
        type=float,
        default=2.5,
        dest="walk")
    parser.add_argument("-cp",
                        "--combat-power",
                        "--combat-points",
                        help="Transfer Pokemon that have CP less than this value (default 100)",
                        type=int,
                        default=100,
                        dest="cp")
    parser.add_argument(
        "-iv",
        "--pokemon-potential",
        help="Transfer Pokemon that have an IV ratio less than this value (default 0.40)",
        type=float,
        default=0.40,
        dest="pokemon_potential")
    parser.add_argument("-k",
                        "--gmapkey",
                        help="Set Google Maps API KEY",
                        type=str,
                        default=None,
                        dest="gmapkey")
    parser.add_argument(
        "-ms",
        "--max-steps",
        help="Set the steps around your initial location(DEFAULT 5 mean 25 cells around your location)",
        type=int,
        default=50,
        dest="max_steps")
    parser.add_argument(
        "-it",
        "--initial-transfer",
        help="Transfer all pokemon with same ID on bot start, except pokemon with highest CP. Respects --cp",
        action="store_true",
        dest="initial_transfer")
    parser.add_argument("-d",
                        "--debug",
                        help="Debug Mode",
                        action="store_true",
                        dest="debug")
    parser.add_argument("-t",
                        "--test",
                        help="Only parse the specified location",
                        action="store_true",
                        dest="test")
    parser.add_argument(
        "-du",
        "--distance-unit",
        help="Set the unit to display distance in (e.g, km for kilometers, mi for miles, ft for feet)",
        type=str,
        default="km",
        dest="distance_unit")

    parser.add_argument(
        "-ign",
        "--ign-init-trans",
        type=str,
        default='',
        dest="ign_init_trans")

    config = parser.parse_args()

    if config.json:
        try:
            # attempt to load values from JSON, overwriting any existing values
            with open(config.json) as data:
                config.__dict__.update(json.load(data))
            return config
        except Exception as e:
            logging.error("Error loading {}.".format(config.json))
            return None
    else:
        # No JSON file specified, stick with command line args
        if config.auth_service not in ['ptc', 'google']:
            logging.error("Invalid Auth service specified! ('ptc' or 'google')")
            return None

        if not (config.location or config.location_cache):
            parser.error("Needs either --use-location-cache or --location.")
            return None

        if not config.username:
            config.username = raw_input("Username: ")
        if not config.password:
            config.password = getpass("Password: ")

        return config


def main():
    # log settings
    # log format
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')

    sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    config = init_config()
    if not config:
        return

    logger.log('[x] PokemonGO Bot v1.0', 'green')
    logger.log('[x] Configuration initialized', 'yellow')

    try:
        bot = PokemonGoBot(config)
        bot.start()

        logger.log('[x] Starting PokemonGo Bot....', 'green')

        while (True):
            bot.take_step()

    except KeyboardInterrupt:
        logger.log('[x] Exiting PokemonGo Bot', 'red')
        # TODO Add number of pokemon catched, pokestops visited, highest CP
        # pokemon catched, etc.


if __name__ == '__main__':
    main()
