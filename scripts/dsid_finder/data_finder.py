#!/usr/bin/env python3
__author__ = "Josh McFayden"
__doc__ = """API for PMG Central Page"""

# Python imports
import subprocess
from collections import OrderedDict
import logging
import pandas as pd
import os

import utils


metas=['crossSection','genFiltEff','kFactor']
fixedL3s=['Baseline','Systematic','Alternative','Specialised']


scopetag_dict=utils.scopetag_dict

def main():

    # Parse options from command line
    from optparse import OptionParser
    usage = "usage: %prog ldn"
    parser = OptionParser(usage=usage)#, version="%prog")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",    help="Set verbose mode (default: %default)")
    parser.add_option("-m", "--metadata", action="store_true", dest="metadata", help="Also print dataset metadata (default: %default)")
    parser.add_option("-a", "--aod", action="store_true", dest="aod", help="Also print AODs (with standard tags) availble for each sample (default: %default)")
    parser.add_option("-p", "--phys", action="store_true", dest="phys", help="Also print DAOD_PHYSs (with standard tags) availble for each sample (default: %default)")
    parser.add_option("-L", "--physlite", action="store_true", dest="physlite", help="Also print DAOD_PHYSLITEs (with standard tags) availble for each sample (default: %default)")
    parser.add_option("-f", "--outformat", action="store", dest="outformat", help="Print only specific output format availble for each sample (default: %default)")
    parser.add_option("-s", "--scope", action="store", dest="scope", help="Select specific scope (default: %default)")
    parser.add_option("-S", "--shortscope", action="store", dest="shortscope", help="Force shortscope (default: %default)")

    parser.set_defaults(verbose=False,metadata=False,aod=False,phys=None,physlite=None,outformat=None,scope=None,shortscope=None,table=None)

    (opts, args) = parser.parse_args()

    if len(args) != 1:
        raise ValueError("Please provide exactly one evtgen dataset")   

    # Set up logging
    if opts.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s',level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s')

    logging.debug(opts)

    # Decode all scopes and tags needed
    allowedscopes=["mc16_13TeV","mc20_13TeV","mc21_13p6TeV","mc23_13p6TeV"]
    scope=opts.scope

    if not scope:
        print("ERROR: Scope required")
        return
    if scope not in allowedscopes:
        print("ERROR: Scope must be one of:",allowedscopes)
        return
        

    
    scopeshort=scope.split('_')[0]
    
    evgenshort=scopetag_dict[scopeshort]["evgen"]["short"]

    if opts.shortscope:
        scopeshort=opts.shortscope
        evgenshort=opts.shortscope

    simshort=scopetag_dict[scopeshort]["sim"]["short"]
    recshort=scopetag_dict[scopeshort]["reco"]["short"]

    tagcombs=utils.getTagCombs(scopeshort)


    
    DBfilebase='/eos/atlas/atlascerngroupdisk/asg-calib/'
    DBfile=DBfilebase+'dev/PMGTools/PMGxsecDB_mc16.txt'
    if not os.access(DBfile, os.R_OK):
        DBfilebase='/cvmfs/atlas.cern.ch/repo/sw/database/GroupData/'
        DBfile=DBfilebase+'dev/PMGTools/PMGxsecDB_mc16.txt'
        logging.debug('EOS not found, falling back to cvmfs')
        if not os.access(DBfile, os.R_OK):
            logging.error('DB file not found! Tried EOS and cvmfs.')
    
    if scopeshort != "mc16" and scopeshort != "mc20":
        DBfile=DBfilebase+f'dev/PMGTools/PMGxsecDB_{simshort}.txt'

    # AMI client
    try:
        import pyAMI.client
        import pyAMI.atlas.api as AtlasAPI
    except ImportError:
        logging.error("Unable to find pyAMI client. Please try this command first: lsetup pyAMI")
        return -1

    # Rucio client
    try:
        from rucio.client import Client
        rucio = Client()
    except ImportError:
        logging.error("Unable to find Rucio client. Please try this command first: lsetup rucio")
        return -1


    # AMI session
    try:
        #ami = pyAMI.client.Client('atlas')
        ami = pyAMI.client.Client('atlas-replica')
        AtlasAPI.init()
    except:
        logging.error("Could not establish pyAMI session. Are you sure you have a valid certificate? Do: voms-proxy-init -voms atlas")
        return -1


    # Parsing of command line options
    hashcomb=[]
    logging.info("Looking for samples with AND of hashtags:")
    maxLevel=1
    for n,arg in enumerate(args):
        hashcomb.append(arg)
        logging.info("  - PMGL%i:%s"%(n+1,arg))
        maxLevel=n+1

    ldns=[args[0]]

    metadata=None
    outformats=None
    aods=None
    physs=None
    physlites=None
    if opts.metadata:
        metadata=getMetadata(ldns,DBfile)
    if opts.outformat:
        outformats=utils.getOutputFormat(rucio,opts.outformat,ldns,scopeshort,tagcombs)
    if opts.aod:
        aods=utils.getOutputFormat(rucio,"AOD",ldns,scopeshort,tagcombs)
    if opts.phys:
        physs=utils.getOutputFormat(rucio,"DAOD_PHYS",ldns,scopeshort,tagcombs)
    if opts.physlite:
        physlites=utils.getOutputFormat(rucio,"DAOD_PHYSLITE",ldns,scopeshort,tagcombs)
    table={}
    
    for ldn in ldns:
        if ldn not in table:
            s_ldn=ldn.split('.')
            table[ldn]={
                'Dataset':s_ldn[1]+"."+s_ldn[2].replace('_','\_')+"."+s_ldn[-1],
                'crossSection':"",
                'genFiltEff':"",
                'kFactor':"",
            }
        if not opts.metadata:
            #Check mode
            print(ldn)
        else:
            
            print(ldn,metadata[ldn]['crossSection'],metadata[ldn]['genFiltEff'],metadata[ldn]['kFactor'])

            for meta in metas:
                table[ldn][meta]=metadata[ldn][meta]
            
        if opts.outformat:
            if not outformats:
                continue
            for tagcomb in tagcombs:
                spaces=' '.join(['' for i in range(len(f'   {tagcomb} {opts.outformat}: ')+2)])
                outformats[ldn][tagcomb].sort(reverse=True,key = lambda x: int(x.split('_')[-1][1:])) #do the sort on the last tag numerically
                for outformat in outformats[ldn][tagcomb]:
                    print(f'   {tagcomb.replace("-", " ")} {opts.outformat} ', outformat)
        if opts.aod:
                for tagcomb in tagcombs:
                    for outformat in aods[ldn][tagcomb]:
                        print(f'   AOD: {tagcomb.replace("-", " ")} {opts.outformat} ', outformat)
        if opts.phys:
            for tagcomb in tagcombs:
                physs[ldn][tagcomb].sort()
                dsid = physs[ldn][tagcomb]
                print(f'  {tagcomb.replace("-", " ")} DAOD_PHYS {dsid[-1] if dsid and len(dsid) else ""} ')
        if opts.physlite:
            for tagcomb in tagcombs:
                physlites[ldn][tagcomb].sort()
                dsid = physlites[ldn][tagcomb]
                print(f'  {tagcomb.replace("-", " ")} DAOD_PHYSLITE {dsid[-1] if dsid and len(dsid) else ""} ')
     



def getAvailableHashtags(ami,scopeshort,hashcomb,maxLevel):

    hashcombcmd=''


    for n,hashtag in enumerate(hashcomb):
        if not len(hashcombcmd):
            hashcombcmd='d.`IDENTIFIER` IN (SELECT h%i.`DATASETFK` FROM `HASHTAGS` h%i WHERE h%i.`SCOPE` = \'PMGL%i\' AND h%i.`NAME` = \'%s\')'%(n+1,n+1,n+1,n+1,n+1,hashtag)
        else:
            hashcombcmd+=' AND d.`IDENTIFIER` IN (SELECT h%i.`DATASETFK` FROM `HASHTAGS` h%i WHERE h%i.`SCOPE` = \'PMGL%i\' AND h%i.`NAME` = \'%s\')'%(n+1,n+1,n+1,n+1,n+1,hashtag)

    cmd=f'SearchQuery -catalog="{scopeshort}_001:production" -entity="DATASET" -sql="SELECT DISTINCT h.`SCOPE`, h.`NAME` FROM `DATASET` d ,`HASHTAGS` h WHERE %s AND d.`IDENTIFIER` = h.`DATASETFK` AND h.`SCOPE` = \'PMGL%i\'"'%(hashcombcmd,maxLevel+1)

    result = ami.execute(cmd,format='dom_object')
    hashtags=[str(res[u'HASHTAGS.NAME']) for res in result.get_rows()]

    return hashtags

def getSamplesFromHashtags(ami,hashcomb,scope):
    # Build AMI DatasetWBListDatasetsForHashtag command using AND of L1,...,LN hashtags
    scopecmd=''
    namecmd=''
    for n,hashtag in enumerate(hashcomb):
        if not len(scopecmd):
            scopecmd='PMGL%i'%(n+1)
        else:
            scopecmd+=',PMGL%i'%(n+1)
        if not len(namecmd):
            namecmd='%s'%(hashtag)
        else:
            namecmd+=',%s'%(hashtag)

    cmd='DatasetWBListDatasetsForHashtag -scope="%s" -name="%s" -operator="AND"'%(scopecmd,namecmd)
    #print(cmd)
    result = ami.execute(cmd,format='dom_object')
    ldns=[str(res[u'ldn']) for res in result.get_rows() if scope in str(res[u'ldn'])]

    return ldns

def getSamplesFromHashtagLevel(ami,hashcomb,level,scope):
    # Build AMI DatasetWBListDatasetsForHashtag command using AND of L1,...,LN hashtags
    scopecmd='PMGL%i'%(level)
    namecmd='%s'%(hashcomb[0])

    cmd='DatasetWBListDatasetsForHashtag -scope="%s" -name="%s" -operator="AND"'%(scopecmd,namecmd)
    #print(cmd)
    result = ami.execute(cmd,format='dom_object')
    ldns=[str(res[u'ldn']) for res in result.get_rows() if scope in str(res[u'ldn'])]

    return ldns


def getHashtagsForLdn(ami,ldn):

    cmd='DatasetWBListHashtags -ldn="%s"'%(ldn)

    hashes=[[],[],[],[]]
    result = ami.execute(cmd,format='dom_object')
    allhashes=result.get_rows()
    for xhash in allhashes:
        if xhash[u'scopeName']=='PMG_GLOBAL_SCOPE':
            for i in range(0,4):
                if xhash[u'scope']==f'PMGL{i+1}':
                    hashes[i].append(xhash[u'name'])
                    break

    return hashes


def getMetadata(dslist,DBfile):
    valsnotfound={'crossSection':"UNKNOWN",
                  'genFiltEff':"UNKNOWN",
                  'kFactor':"UNKNOWN"}

    returnVals={}

    try:
        with open(DBfile) as f:
            s = f.read()
    except IOError:
        logging.error("Looks like there was a problem reading PMG cross section database file: %s"%DBfile)
        for ds in dslist: returnVals[ds]=valsnotfound
        return returnVals


    for ds in dslist:

        if ds not in returnVals:
            returnVals[ds]={}

        p1 = subprocess.Popen(['cat','%s'%DBfile], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['grep',ds.split('.')[1]], stdin=p1.stdout, stdout=subprocess.PIPE)
        p3 = subprocess.Popen(['grep',ds.split('.')[-1]], stdin=p2.stdout, stdout=subprocess.PIPE)
        matchline=p3.communicate()[0]
        if len(matchline):
            returnVals[ds]={'crossSection':matchline.split()[2].decode("utf-8"),
                            'genFiltEff':matchline.split()[3].decode("utf-8"),
                            'kFactor':matchline.split()[4].decode("utf-8")}
        else:
            returnVals[ds]=valsnotfound



    return returnVals

def getEVNTldn(ldn,evgenshort,simshort,recshort,opts):
    #print("BEFORE:",ldn)
    if opts.verbose:
        print(f'INFO: Finding EVNT ldn for {ldn}')
    ldnsplit=ldn.split('.')            
    evgenldn=ldn
    prodstep=ldnsplit[3]
    outformat=ldnsplit[4]
    tags=ldnsplit[5]
    if 'AOD' in outformat:
        evgenldn=evgenldn.replace(f'{recshort}_',f'{evgenshort}_')
    elif 'HITS' in outformat:
        evgenldn=evgenldn.replace(f'{simshort}_',f'{evgenshort}_')
    evgenldn=evgenldn.replace(prodstep,'evgen').replace(outformat,'EVNT').replace(tags,tags.split('_')[0])
    #print("AFTER:",evgenldn)

    return evgenldn

if __name__ == '__main__':
    main()
