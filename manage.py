#!/usr/bin/env python
import os
import sys
import faulthandler

if __name__ == "__main__":
    f = open('faulthandler.txt', 'w')
    faulthandler.enable(f, all_threads=True)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Inventory.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
