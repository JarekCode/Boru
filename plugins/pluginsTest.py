#!/usr/bin/env python3
# ------------------
# John Ó Ríordán
# ------------------
# ---------------------------------------------------
# pluginsTest.py |  Used to test parameter scripts in the directory
# ---------------------------------------------------
import argparse
from importlib import import_module

###########################################################################################
"""
Get command line args from the user.
"""
def get_args():
    parser = argparse.ArgumentParser(
        description='Test parameter plugins which are used to add functionality')

    parser.add_argument('-p', '--plugin',
                        required=True,
                        action='store',
                        help='Plugin to test (without file extension)')

    parser.add_argument('-l', '--lab',
                        required=True,
                        action='store',
                        help='lab to test against')

    parser.add_argument('-r', '--region',
                        required=True,
                        action='store',
                        help='lab region to test against')

    parser.add_argument('-i', '--identifier',
                        required=True,
                        action='store',
                        help='Identifier to resolve')

    args = parser.parse_args()

    return args

###########################################################################################


def main():

    args = get_args()

    # Take the plugin specified by the script and load it as a module
    module_name = args.plugin
    module = import_module(module_name)

    result = module.getIdentifier(args.lab, args.region, args.identifier)
    print (result)

###########################################################################################

""" Start program """
if __name__ == "__main__":
    main()

