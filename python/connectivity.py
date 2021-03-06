import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
import scipy.io
import os
import textwrap

# from xlrd import open_workbook

def GetNamesList(namesCellArray):
    '''
    Converts cell array with text from matlab to python list
    :param namesCellArray: An (n,) array loaded as a cell array with text from matlab
    :return: a list with the text converted to string
    '''
    namesList = []
    for ind in range(namesCellArray.size):
        name = namesCellArray[ind][0].encode('ascii', 'ignore')
        namesList.append(name)

    return namesList

def FindStringInList(S, L):
    ind = [ind for ind, entry in enumerate(L) if S[:] == entry[:]]
    return ind

def GetRegionOutputs(region, connections, inputRegions, outputRegions):
    ind = FindStringInList(region, inputRegions)
    if not ind:
        raise Exception('Region not found: '  + region)

    regionOutputs = np.empty((connections.shape[1],len(ind), ), dtype='|S20')
    outputVals = np.zeros((connections.shape[1],len(ind), ), dtype=float)

    for iter, i in enumerate(ind): ### If there are multiple injections in a region
        projStrengths = connections[i,:]
        sortedInds = np.argsort(projStrengths)[::-1]   ### descending order sort (argsort defaults to ascending)
        regionOutputs[:, iter] = [ outputRegions[k] for k in sortedInds]
        outputVals[:,iter]  = np.asarray([projStrengths[k] for k in sortedInds])

    return regionOutputs, outputVals

def GetRegionInputs(region, connections, inputRegions, outputRegions):
    ind = FindStringInList(region, outputRegions)
    if not ind:
        raise Exception('Region not found: '  + region)

    regionInputs = np.empty((connections.shape[0],len(ind), ), dtype='|S20')
    inputVals = np.zeros((connections.shape[0],len(ind), ), dtype=float)

    for iter, i in enumerate(ind): ### If there are multiple injections in a region
        projStrengths = connections[:,i]
        sortedInds = np.argsort(projStrengths)[::-1]   ### descending order sort (argsort defaults to ascending)
        regionInputs[:, iter] = [ inputRegions[k] for k in sortedInds]
        inputVals[:,iter]  = np.asarray([projStrengths[k] for k in sortedInds])

    return regionInputs, inputVals


def NamesFromAbbrevs(abbrevs, abbrevConvert):
    names = []
    for abb in abbrevs:
        ind = FindStringInList(abb, abbrevConvert['allAbbrevs'])
        names.append(abbrevConvert['allNames'][ind[0]])

    return names


def PrintInputsAndOutputs(regionOutputs, outputVals, regionInput, inputVals, numRegionsListed, abbrevConvert, print_inputs=True):
    if len(outputVals.shape) > 1:
        outputVals = outputVals[0:numRegionsListed, :]
    else:
        outputVals = outputVals[0:numRegionsListed]

    if len(inputVals.shape) > 1:
        inputVals = inputVals[0:numRegionsListed, :]
    else:
        inputVals = inputVals[0:numRegionsListed]

    nOutputLists = regionOutputs.shape[1]
    nInputLists = regionInputs.shape[1]
    regionOutputNames = {}
    regionInputNames = {}
    for i in range(nOutputLists):
        regionOutputNames[i] = NamesFromAbbrevs(regionOutputs[0:numRegionsListed, i], abbrevConvert)

    for j in range(nInputLists):
        regionInputNames[j] = NamesFromAbbrevs(regionInputs[0:numRegionsListed, j], abbrevConvert)

#    print(('{0:55} '*nInputLists + '{1:55} '*nOutputLists).format('inputs:', 'outputs:'))
    
    if print_inputs:
        print('INPUTS:')
    else:
        print('OUTPUTS:')
    for i in range(numRegionsListed):
        formatString = ''
        for k in range(nOutputLists + nInputLists):
            formatString = formatString + '{'+str(2*k)+':5} ' + '{'+str(2*k+1)+':50} '

        dataArr = []
        if print_inputs:
            for k in range(nInputLists):
                print('{0:.2f} \t {1:s}'.format(inputVals[i, k], regionInputNames[k][i]))
                dataArr.append('{0:.2f}'.format(inputVals[i, k]))
                dataArr.append(regionInputNames[k][i])

        else:
            for k in range(nOutputLists):
                print('{0:.2f} \t {1:s}'.format(outputVals[i, k], regionOutputNames[k][i]))
                dataArr.append('{0:.2f}'.format(outputVals[i, k]))
                dataArr.append(regionOutputNames[k][i])

#        print(formatString.format(*dataArr)) ### Why does that star make it work??

        # print('{0:.2f} {1:50} {2:.2f} {3:50}'.format(inputVals[i], regionInputNames[i], outputVals[i], regionOutputNames[i]))




if __name__ == "__main__":
#    baseDir = "/home/izkula/Dropbox/hubz/mesoconnectome"
    import os
    dir_path = os.path.dirname(os.path.realpath(__file__)) # file's dir. janky.
    baseDir = dir_path

    print_inputs=False # If false, then prints outputs
    useRegionalMatrix = False ### Use the processed, regional projection matrix (as opposed to injection-based matrix)
    doUserSelectRegion = True
    numRegionsListed = 30

    ### Load data
    mat = scipy.io.loadmat(os.path.join(baseDir, 'allen_structures.mat'))
    abbrevConvert = {}
    abbrevConvert['allAbbrevs'] = GetNamesList(mat['structures'][:, 0])
    abbrevConvert['allNames'] = GetNamesList(mat['structures'][:, 1])


    if useRegionalMatrix:
        mat = scipy.io.loadmat(os.path.join(baseDir, 'allen_quantitative_projs.mat'))
        outputs = GetNamesList(mat['outputs'][0]);
        input = GetNamesList(mat['input'][:,0]);
        connections = mat['connections']; ### rows are inputs, columns are outputs
    else:
        mat = scipy.io.loadmat(os.path.join(baseDir, 'allen_normalized_projs.mat'))
        outputs = GetNamesList(mat['outputs'][0,:])
        input = GetNamesList(mat['input'][:, 0])
        connections = mat['connections']; ### rows are inputs, columns are outputs


    while True:
        ### Select region
        if doUserSelectRegion:
            print '\n'
            print textwrap.fill(', '.join(sorted(list(set(input) & set(outputs)))), 150) ### Print out list of possible regions

            print '\n'
            region = raw_input("Please enter a region: ")
            print '\n'
            if region[:] == 'Q':
                break
            print "you entered", NamesFromAbbrevs([region], abbrevConvert)

        else:
            region = 'RSPd'

        ### compute inputs and outputs
        [regionOutputs, outputVals] = GetRegionOutputs(region, connections, input, outputs)
        [regionInputs, inputVals] = GetRegionInputs(region, connections, input, outputs)
        PrintInputsAndOutputs(regionOutputs, outputVals, regionInputs, inputVals, numRegionsListed, abbrevConvert, print_inputs=print_inputs)

        if not doUserSelectRegion:
            break


