from pyparsing import Word, alphas, alphanums, dictOf, Literal, restOfLine, OneOrMore, ZeroOrMore, empty, Suppress, replaceWith, Keyword, Group, Combine, Dict, delimitedList, Optional, CaselessKeyword, Forward, ParseResults, SkipTo
import argparse

def getGrammar():
    identifier = Word(alphas+"_",alphanums+"_")
    # Semicolon as end of line
    eol = Suppress(";")
    # test <name>; (NON-STANDARD IF)
    testdecl = Suppress(CaselessKeyword("test") + identifier) + Optional(CaselessKeyword("#ordered")) + eol
    # endtest; (NON-STANDARD IF)
    endtest = Suppress(CaselessKeyword("endtest") + eol)

    # process <id>;
    processdecl = CaselessKeyword("process") + \
            Word(alphas+"_"+"{"+"}",alphanums+"_"+"{"+"}").setResultsName("processname1") + \
            eol

    # endprocess;
    endprocess = CaselessKeyword("endprocess") + eol

    # state <name>;
    statedecl = CaselessKeyword("state") + \
            identifier.setResultsName("statename1") + \
            eol
    # endstate;
    endstate = CaselessKeyword("endstate") + eol
    # nextstate <name>;
    nextstate = CaselessKeyword("nextstate") + \
            identifier.setResultsName("statename2") + \
            eol
    # exit;
    ifexit = CaselessKeyword("exit") + eol

    parameter = Forward()
    parameter << identifier + Optional(Suppress("(") + Group(ZeroOrMore(parameter)) + Suppress(")")) + Optional(Suppress(","))

    # input <name>(params...);
    ifinput= CaselessKeyword("input") + \
            (identifier +
                    Suppress("(") +
                    Group(ZeroOrMore(parameter)) +
                    Suppress(")")
            )\
            .setResultsName("input",listAllMatches=True) + eol
    # output <name>(params...);
    ifoutput= CaselessKeyword("output") + \
            (identifier +
                    Suppress("(") +
                    Group(ZeroOrMore(parameter)) +
                    Suppress(")")
            )\
            .setResultsName("output",listAllMatches=True) + eol

    ifinformal=CaselessKeyword("informal") + (Combine('"' + SkipTo('"') + '"')).setResultsName("informal",listAllMatches=True) + eol

    # full state block
    state = Group(statedecl + \
            OneOrMore(nextstate | ifexit | ifinput | ifinformal | ifoutput ) + \
            endstate)

    # state group
    states = ZeroOrMore(state)

    # full process group
    process = Group(processdecl + \
            OneOrMore(state) + \
            endprocess)

    # process group
    processes = ZeroOrMore(process)

    # full test block
    test = Group(testdecl + processes + endtest)
    # test group
    tests = ZeroOrMore(test)

    return tests

def parse(inputfile):
    tests = getGrammar()
    parsed = tests.parseFile(inputfile,parseAll=True)
    return parsed

# Couldn't find a better way to do this...
# isinstance and peeking are not nice...
def _getParams(paramlst):
    ret = '{'
    for p,i in zip(paramlst,range(len(paramlst))):
        if not isinstance(p,ParseResults):
            ret += p + ","
            if i+1<len(paramlst) and isinstance(paramlst[i+1],ParseResults):
                ret+=_getParams(paramlst[i+1])
    ret = ret[0:-1] + '},' #slice to remove last comma in sublist
    return ret

def getParams(paramlst):
    if len(paramlst) > 0:
        ret = '"' + _getParams(paramlst)[0:-1] + '"' # slice to remove last comma in complete list
        return ret
    else:
        return "NULL"

def processFile(inputfile,outputfile):
    parsed = parse(inputfile)
    #print repr(parsed)
    #print parsed
    testfn=0
    for test_el in parsed:
        #testn = testn + 1
        to_write = ""
        testn=0
        ordtestn=0
        signalid=0
        source = ""
        target = ""
        ordered = False
        parrayname="purposes"
        if test_el[0] == "#ordered":
            ordered = True
            parrayname="ordpurposes"
            del test_el[0]
        for process_el in test_el:
            pel = list(process_el)
            process_name_index = pel.index('process') + 1
            process = pel[process_name_index]
            for state_el in process_el[process_name_index+1:]: #slice omitting process declaration, should be comprehension or filter?
                el = list(state_el)
                if 'state' in el:
                    source = el[el.index('state') + 1]
                    #if source == target:
                    #    pass #TODO
                    #else:
                    #    pass #TODO
                    target = el[el.index('nextstate') + 1]
                    nsig = el.count("input") + el.count("output")
                    to_write += """
                        {parrayname}[{testn}].numSignals = {nsig};
                        {parrayname}[{testn}].process = "{processname}";
                        {parrayname}[{testn}].source = "{source}";
                        {parrayname}[{testn}].target = "{target}";
                    """.format(nsig=nsig,processname=process,testn=testn,source=source,target=target,parrayname=parrayname)

                    signalindex=0
                    for inp in state_el.input:
                        params = getParams(inp[1])
                        to_write+= """
                            signalData signal{signalid} = {{"{inp}","input",{params}}};
                            {parrayname}[{testn}].signals[{signalindex}] = signal{signalid};
                        """.format(testn=testn,signalindex=signalindex,signalid=signalid,inp=inp[0],params=params,parrayname=parrayname)
                        signalid+=1
                        signalindex+=1
                    for outp in state_el.output:
                        params = getParams(outp[1])
                        to_write+= """
                            signalData signal{signalid} = {{"{outp}","output",{params}}};
                            {parrayname}[{testn}].signals[{signalindex}] = signal{signalid};
                        """.format(testn=testn,signalindex=signalindex,signalid=signalid,outp=outp[0],params=params,parrayname=parrayname)
                        signalid+=1
                        signalindex+=1
                    for inf in state_el.informal:
                        to_write+= """
                            signalData signal{signalid} = {{{command},"informal",NULL}};
                            {parrayname}[{testn}].signals[{signalindex}] = signal{signalid};
                        """.format(testn=testn,signalindex=signalindex,signalid=signalid,command=inf,parrayname=parrayname)
                        signalid+=1
                        signalindex+=1
                    testn+=1

        fname = (str(testfn) + ".").join(outputfile.split(".")) if testfn>0 else outputfile

        f = open(fname,'w')

        if ordered:
            ordtestn=testn
            testn=0

        cstr = '''

            numOrdPurposes = {0};
            numPurposes = {1};

            int i;
            for (i=0; i < numPurposes;i++){{
                purposes[i].status = false;
                purposes[i].visited = false;
                purposes[i].process = NULL;
                purposes[i].source = NULL;
                purposes[i].target = NULL;
                purposes[i].numBoundClocks = 0;
                purposes[i].numActiveClocks = 0;
                purposes[i].numSignals = 0;
                purposes[i].numVariables = 0;
                purposes[i].depth = -1;
            }}

            for (i=0; i < numOrdPurposes;i++){{
                ordPurposes[i].status = false;
                ordPurposes[i].visited = false;
                ordPurposes[i].process = NULL;
                ordPurposes[i].source = NULL;
                ordPurposes[i].target = NULL;
                ordPurposes[i].numBoundClocks = 0;
                ordPurposes[i].numActiveClocks = 0;
                ordPurposes[i].numSignals = 0;
                ordPurposes[i].numVariables = 0;
                ordPurposes[i].depth = -1;
            }}

        '''.format(ordtestn, testn) + to_write + "\n"
        f.write(cstr)
        f.close()
        testfn+=1

def cFileName(string):
    if not string.endswith((".C",".c")):
        raise argparse.ArgumentTypeError("Output file name must end in .C")
    return string

if __name__ == '__main__':
    argumentParser = argparse.ArgumentParser()
    argumentParser.add_argument("inputfile", help="Determine input file name")
    argumentParser.add_argument("-o", dest="outputfile", default="test.C", type=cFileName, help="Determine output file name (default: test.C)")
    args = argumentParser.parse_args()
    processFile(args.inputfile,args.outputfile)
