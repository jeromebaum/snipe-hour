#!/usr/bin/env python

import fnmatch
import os
import plistlib
import sys
import json

import jsontemplate

def plistFormatter(jsonString):
    """
    Parse the given string as JSON and output as XML plist.
    """
    json = json.loads(jsonString)
    return plist.writeToString(json)

more_formatters = { 'plist': plistFormatter }

def loadTemplate(filename):
    """
    Load the template from the given filename.
    """
    with open(filename) as f:
        template = f.read()
    return jsontemplate.Template(template, more_formatters=more_formatters)

bundlePlists = []
for root, dirnames, filenames in os.walk('.'):
    for filename in fnmatch.filter(filenames, 'Bundle.plist'):
        bundlePlists.append(os.path.join(root, filename))

bundles = {}
for bPlist in bundlePlists:
    plist = plistlib.readPlist(bPlist)
    bundleId = plist['BundleIdentifier']
    bundles[bundleId] = { 'data': plist }
    bundleDir = os.path.dirname(bPlist)
    
    templateName = plist['Contents'][0]['Template']
    templateName = os.path.join(bundleDir, templateName)
    bundles[bundleId]['Template'] = loadTemplate(templateName)
    
    finalName = plist['Contents'][0].get('FinalTemplate', None)
    if finalName:
        finalName = os.path.join(bundleDir, finalName)
        bundles[bundleId]['FinalTemplate'] = loadTemplate(finalName)

rootBundle = sys.argv[1]
currentList = [{
    'BundleIdentifier': rootBundle,
    'After': 'Start',
    'Before': 'End',
    'Data': {},
}]

def expandBundle(bundle):
    """
    Expand the given bundle.
    """
    meta = {
        'After': bundle['After'],
        'Before': bundle['Before'],
    }
    dataDict = {
        'meta': meta,
        'data': bundle['Data'],
    }
    calledBundle = bundles[bundle['BundleIdentifier']]
    plist = calledBundle['Template'].expand(dataDict)
    return plistlib.readPlistFromString(plist)

def transformList(lst):
    """
    Expand all bundles in the given list, and flatten the result.
    """
    result = []
    for bundle in lst:
        result += expandBundle(bundle)
    return result

def expandFinal(bundle):
    """
    Run the given bungle through the final transform.
    """
    meta = {
        'After': bundle['After'],
        'Before': bundle['Before'],
    }
    dataDict = {
        'meta': meta,
        'data': bundle['Data'],
    }
    calledBundle = bundles[bundle['BundleIdentifier']]
    return calledBundle['FinalTemplate'].expand(dataDict)

def finalExpandList(lst):
    """
    Run all bundles in the given list through the final transform, and concat.
    """
    result = ""
    for bundle in lst:
        result += expandFinal(bundle)
    return result

while True:
    oldList = currentList
    currentList = transformList(currentList)
    if currentList == oldList:
        break

output = finalExpandList(currentList)
print output
