#!/usr/bin/env python

import fnmatch
import os
import plistlib
import sys

import jsontemplate

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
    with open(os.path.join(bundleDir, templateName)) as f:
        template = f.read()
    bundles[bundleId]['Template'] = jsontemplate.Template(template)
    
    finalName = plist['Contents'][0].get('FinalTemplate', None)
    if finalName:
        with open(os.path.join(bundleDir, finalName)) as f:
            final = f.read()
        bundles[bundleId]['FinalTemplate'] = jsontemplate.Template(final)

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
