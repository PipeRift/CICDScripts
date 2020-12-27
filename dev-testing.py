import sys
import os
from os import path
import shutil

import helpers
from helpers import env


def main():
    env.init([])
    print(env.getEnginePath())
    print(env.getEngineVersion())
    print(env.isEnginePathSet())
    return 0

if __name__ == '__main__':
    sys.exit(main())