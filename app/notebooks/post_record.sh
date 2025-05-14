#!/bin/bash

sox input.wav -r 8000 -b 16 -c 1 -e signed-integer input.raw
