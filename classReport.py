#!/usr/bin/python
# coding: utf-8

import glob
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# ParseStar function taken from PyEM, slightly modified to work with model.star files containing multiple tables


def parseStar(starFile, tableName, keep_index=False, augment=False):
    headers = []
    foundTable = False
    foundheader = False
    ln = 0
    lb = 0
    i = 0
    with open(starFile, "r") as f:
        for l in f:
            if(l.startswith(tableName)):
                foundTable = True
            else:
                ln += 1
                if foundheader and not lastheader:
                    # Don't add to skipped line value if I'm reading the data
                    ln -= 1
            if(foundTable):
                if l.startswith("_"):
                    foundheader = True
                    lastheader = True
                    if keep_index:
                        head = l.rstrip()
                    else:
                        head = l.split('#')[0].rstrip().lstrip('_')
                    headers.append(head)
                else:
                    lastheader = False
                if foundheader and not lastheader:
                    # Read through the data to see how long it is, record length in lb
                    # Use this value in the pd.read_csv line
                    if l.startswith(" "):
                        break
                    lb += 1
    df = pd.read_csv(starFile, skiprows=ln,
                     delimiter='\s+', nrows=lb, header=None)
    df.columns = headers
    return df  # A PANDAS data frame object is returned


def sortModelStars(model=" "):
    s = model.split("it")
    it = int(s[1][0:3])
    if s[0].startswith("run_ct"):
        it += 1
    return it


def plotDistribution(cd, legend):
    """
    Graphing the distribution data
    """
    maxDist = cd.max(axis=0).max()
    minDist = cd.min(axis=0).min()
    ymax = maxDist + .06
    ymin = minDist - .005
    if ymax > 1:
        ymax = 1
    if ymin < 0:
        ymin = 0
    cd.plot(use_index=True, linewidth=2)
    plt.legend(legend, ncol=2, loc='upper left', title="Classes")
    plt.ylim(ymin, ymax)
    plt.grid(linestyle='-', linewidth=.2)
    plt.xlabel('Iteration')
    plt.ylabel('Distribution')
    plt.title('Class Distribution')


def plotResolution(rs, legend):
    """
    Graphing the resolution data
    """
    maxRes = rs.max(axis=0).max()
    minRes = rs.min(axis=0).min()
    ymax = maxRes + 2
    ymin = minRes - 1
    if ymin < 0:
        ymin = 0
    rs.plot(use_index=True, linewidth=2)
    plt.legend(legend, ncol=2, loc='upper left', title="Classes")
    plt.ylim(ymin, ymax)
    plt.grid(linestyle='-', linewidth=.2)
    plt.xlabel('Iteration')
    plt.ylabel('Resolution (A)')
    plt.title('Class Resolution')


# Use the runJob file to determine the number of classes without having to iterate through the whole data.star file
def main():
    """
    Parsing the path of the job folder
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', nargs=1, help='the path of the directory for the job')
    parser.add_argument(
        '-s', dest='s', action='store_true', help='Show the interactive form of the graphs in addition to saving to a PDF.')
    args = parser.parse_args()
    path = args.path[0]
    jobName = path.split("/")
    jobName = jobName[len(jobName)-2]
    runJob = glob.glob(path + "/run.job")[0]

    numClasses = 0
    micrographs = 0
    min = 1
    max = 0
    with open(runJob, "r") as f:
        for l in f:
            if l.startswith("Number of classes"):
                numClasses = (int)(l.split("== ")[1])

    """
    Here we iterate through the model.star files, reading the data we want into PANDAS data frames
    So far I'm taking the class distribution data and the estimated resolution data
    """
    modelStars = glob.glob(path + '/*model.star')
    modelStars.sort(key=sortModelStars)
    classDict = {}
    resDict = {}
    it = 0
    for name in modelStars:
        filename = name
        df = parseStar(filename, "data_model_classes")
        classDist = []
        resolution = []
        for column in df:
            if column == "rlnClassDistribution":
                classDist = list(df[column])
            if column == "rlnEstimatedResolution":
                resolution = list(df[column])
        classDict[it] = classDist
        resDict[it] = resolution
        it += 1
    cd = pd.DataFrame.from_dict(classDict, orient='index')
    rs = pd.DataFrame.from_dict(resDict, orient='index')

    """
    Setting up the tables to be graphed
    """
    headers = []
    legend = ''
    for i in range(numClasses):
        headers.append("class" + str(i))
        legend += str(i+1)
    cd.columns = headers
    rs.columns = headers
    pp = PdfPages(jobName + '.pdf')

    """
    Outputting to the PDF
    """
    # Plot the distribution and save it to the PDF
    plotDistribution(cd, legend)
    pp.savefig()
    plt.close()

    # Plot the resolution and save it to the PDF
    plotResolution(rs, legend)
    pp.savefig()
    plt.close

    # Close the PDF
    pp.close()

    # If the -s flag was input, show the plots in python
    if(args.s):
        plotDistribution(cd, legend)
        plt.show()


main()
# TODO:
# Look into getting images of the mrcs, not sure if it's possible.
# Do accuracy angles and stuff like that
# Make it work for other job types (2d class, refine, etc)
