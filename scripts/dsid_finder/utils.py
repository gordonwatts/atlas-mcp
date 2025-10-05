from collections import OrderedDict

# AMI tag combinations for different MC campaigns and FS/AF2
scopetag_dict=OrderedDict()
scopetag_dict['mc16']={'evgen':
                  {
                      'short':'mc15'
                  },
                  'sim':
                  {
                      'short':'mc16',
                      'FS':['s3126'],
                      'AF2':['a875']
                  },
                  'reco':
                  {
                      'short':'mc16',
                      'campaigns':{
                          'mc16a':['r9364'],
                          'mc16d':['r10201'],
                          'mc16e':['r10724']
                      }
                  }
              }

scopetag_dict['mc20']={'evgen':
                  {
                      'short':'mc15'
                  },
                  'sim':
                  {
                      'short':'mc16',
                      'FS':['s3681','s4231','s3797'],
                      'AF2':['a907']
                  },
                  'reco':
                  {
                      'short':'mc20',
                      'campaigns':{
                          'mc20a':['r13167','r14859'],
                          'mc20d':['r13144','r14860'],
                          'mc20e':['r13145','r14861']
                      }
                  }
              }


scopetag_dict['mc23']={'evgen':
                  {
                      'short':'mc23'
                  },
                  'sim':
                  {
                      'short':'mc23',
                      'FS':['s4162','s4159','s4369'],
                      'AF3':['a910','a911','a934']
                  },
                  'reco':
                  {
                      'short':'mc23',
                      'campaigns':{
                          'mc23a':['r15540','r14622'],
                          'mc23d':['r15530','r15224'],
                          'mc23e':['r16083']
                      }
                  }
              }



def getTagCombs(scopeshort):
    tagcombs=OrderedDict()

    # get combinations for full sim
    for stag in scopetag_dict[scopeshort]["sim"]["FS"]:
        for camp in scopetag_dict[scopeshort]["reco"]["campaigns"]:
            for rtag in scopetag_dict[scopeshort]["reco"]["campaigns"][camp]:
                if f'{camp} - FS' not in tagcombs:
                    tagcombs[f'{camp} - FS']=[f'_{stag}_{rtag}']
                else:
                    tagcombs[f'{camp} - FS'].append(f'_{stag}_{rtag}')

    # get combinations for fast sim
    asimtype=[x for x in scopetag_dict[scopeshort]["sim"] if "AF" in x][0]
    for atag in scopetag_dict[scopeshort]["sim"][asimtype]:
        for camp in scopetag_dict[scopeshort]["reco"]["campaigns"]:
            for rtag in scopetag_dict[scopeshort]["reco"]["campaigns"][camp]:
                if f'{camp} - {asimtype}' not in tagcombs:
                    tagcombs[f'{camp} - {asimtype}']=[f'_{atag}_{rtag}']
                else:
                    tagcombs[f'{camp} - {asimtype}'].append(f'_{atag}_{rtag}')

    return tagcombs

def getAODs(rucio,dsformat,ldns,scopeshort,tagcombs):
    aods={}

    stepformat=None
    if dsformat == "AOD":
        stepformat='.recon.AOD.'
    elif dsformat == "DAOD_PHYS":
        stepformat='.deriv.DAOD_PHYS.'   
    elif dsformat == "DAOD_PHYSLITE":
        stepformat='.deriv.DAOD_PHYSLITE.'
    
    evgenshort=scopetag_dict[scopeshort]["evgen"]["short"]
    simshort=scopetag_dict[scopeshort]["sim"]["short"]
    recshort=scopetag_dict[scopeshort]["reco"]["short"]

    for ldn in ldns:
        if ldn not in aods:
            aods[ldn]=OrderedDict()

        for tagcomb in tagcombs:
            scope=ldn.replace(f'{evgenshort}_',f'{recshort}_').split('.')[0]
            #if opts.verbose: print "DEBUG: Search term for %s is %s"%(ldn,search)
            #dsfound=[x for x in rucio.list_dids(scope,{'name':search},type='container')]
            #print(search)
            dsfound=[]
            for tag in tagcombs[tagcomb]:
                search=ldn.replace(f'{evgenshort}_',f'{recshort}_').replace('.evgen.EVNT.',stepformat)+'%s'%tag+'%'
                dsfound.extend([x for x in rucio.list_dids(scope,{'name':search},did_type='container')])
            aods[ldn][tagcomb]=dsfound
    return aods


def getOutputFormat(rucio,dsformat,ldns,scopeshort,tagcombs):
    aods={}

    step=None
    if dsformat == "AOD":
        step='recon'
    elif "DAOD" in dsformat:
        step='deriv'
    else:
        print("ERROR: Non-recognised format entered! Should be AOD or DAOD_*.")
        return
    
    stepformat=f'.{step}.{dsformat}.'
            
    evgenshort=scopetag_dict[scopeshort]["evgen"]["short"]
    simshort=scopetag_dict[scopeshort]["sim"]["short"]
    recshort=scopetag_dict[scopeshort]["reco"]["short"]

    for ldn in ldns:
        if ldn not in aods:
            aods[ldn]=OrderedDict()

        
        for tagcomb in tagcombs:
            scope=ldn.replace(f'{evgenshort}_',f'{recshort}_').split('.')[0]
            #if opts.verbose: print "DEBUG: Search term for %s is %s"%(ldn,search)
            #dsfound=[x for x in rucio.list_dids(scope,{'name':search},type='container')]
            #print(search)
            dsfound=[]
            for tag in tagcombs[tagcomb]:
                search=ldn.replace(f'{evgenshort}_',f'{recshort}_').replace('.evgen.EVNT.',stepformat)+'%s'%tag+'%'
                #dsfound.extend([x for x in rucio.list_dids(scope,{'name':search},did_type='container')])
                nonemptyds=[]
                for x in rucio.list_dids(scope,{'name':search},did_type='container'):
                    if len(list(rucio.list_content(scope,x))):
                        nonemptyds.append(x)
                
                dsfound.extend(nonemptyds)
                
            aods[ldn][tagcomb]=dsfound
    return aods
