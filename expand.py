#!/usr/bin/env python

import fnmatch
import os
import plistlib
import sys
import json
import re

import jsontemplate

def plistFormatter(jsonObj):
    """
    Output the given JSON object as XML plist.
    """
    string = plistlib.writePlistToString(jsonObj)
    string = re.sub(r'(?s).*?<plist[^>]*>', '', string)
    string = re.sub(r'</plist>', '', string)
    return string

def plistFlattener(plist):
    """
    Remove surrounding <dict/> tags from given plist.
    """
    plist = re.sub(r'(?s)^\s*<dict>', '', plist, count=1)
    plist = re.sub(r'(?s)</dict>\s*', '', plist, count=1)
    return plist

more_formatters = {
    'plist': plistFormatter,
    'json': json.dumps,
    'jsonToFlatPlist': lambda s: plistFlattener(plistFormatter(json.loads(s))),
}

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
    
    templateName = plist['Template']
    templateName = os.path.join(bundleDir, templateName)
    bundles[bundleId]['Template'] = loadTemplate(templateName)
    
    finalName = plist.get('FinalTemplate', None)
    if finalName:
        finalName = os.path.join(bundleDir, finalName)
        bundles[bundleId]['FinalTemplate'] = loadTemplate(finalName)

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

if __name__ == '__main__':
    rootBundle = sys.argv[1]
    currentList = [{
        'BundleIdentifier': rootBundle,
        'After': 'Start',
        'Before': 'End',
        'Data': {},
    }]

    while True:
        oldList = currentList
        currentList = transformList(currentList)
        if currentList == oldList:
            break

    output = finalExpandList(currentList)
    print output
