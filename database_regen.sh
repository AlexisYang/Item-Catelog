#!/bin/bash
rm itemcatelog.db
python database_setup.py
python lotsofcategories.py
