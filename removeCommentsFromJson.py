#!/usr/bin/python -tt

# import modules used here -- sys is a very standard one
import os
import io
import sys
import re
import json     ##json to serialize data, web friendly?? and read json config file


def removeCommentsFromJson(filename):
    with open(filename) as jsonFileHandle:
        content = ''.join(jsonFileHandle.readlines())
        content = re.sub(r'//(?!www)[.\S ]*', '', content) # // comment, if there is a link http://www. exclude from comments
        content = re.sub(r'#[.\S ]*', '', content) # # comment
        content = re.sub(r'/\*[.\s\S]*?\*/', '', content) # /* .. */ comment
        content = re.sub(r'<!--[.\s\S]*?-->', '', content) # <!-- .. --> comment

        # If there are 2 or more new lines replace with one
        content = re.sub(r'[\n]{2,}', '\n', content)

        print content

        return json.loads(content)

# Gather our code in a main() function
def main():
    removeCommentsFromJson('sample-comments-conf.json')


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
  main()

