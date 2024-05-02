import re

P_REQUEST_LOG = re.compile(r'^(.*?) - - \[(.*?)\] "(.*?)" (\d+) (\d+|-)$')
