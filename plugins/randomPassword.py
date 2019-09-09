#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Jaroslaw Glodowski
import random, string, json, logging

# generate x amount of random characters
def random_char(x):
  return ''.join(random.choice(string.digits) for i in range(x))

# main function
def getIdentifier(labName, region, identifier):
  # list of colors
  # https://simple.wikipedia.org/wiki/List_of_colors
  listOfColors = ["Amaranth", "Amber", "Amethyst", "Apricot", "Aquamarine", "Azure", "Beige", "Blue", "Blush", "Bronze", "Burgundy", "Carmine", "Cerise", "Cerulean", "Champagne", "Coffee", "Copper", "Coral", "Crimson", "Cyan", "Emerald", "Gold", "Grey", "Green", "Indigo", "Jade", "Lavender", "Lemon", "Lilac", "Lime", "Magenta", "Maroon", "Mauve", "Ochre", "Olive", "Orange", "Orchid", "Peach", "Pear", "Pink", "Plum", "Puce", "Purple", "Raspberry", "Red", "Rose", "Ruby", "Salmon", "Sapphire", "Scarlet", "Silver", "Teal", "Turquoise", "Ultramarine", "Violet", "Yellow"]
  # get the color
  color = random.choice(listOfColors)
  # get random characters
  characters = random_char(4)
  # password
  password = (str(color.upper()) + "@" + str(characters))
  # ====================================================================================================================
  logging.basicConfig(filename='/var/log/boru.log',level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
  log = logging.getLogger('randomPassword')
  log.info("[randomPassword | {}] Random password generated: {}".format(str(labName), str(password)))
  # =============================================================================================
  # return password
  return json.dumps({'userPassword' : str(password)})

