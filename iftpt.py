from pyparsing import Word, alphas, alphanums, dictOf, Literal, restOfLine, OneOrMore, ZeroOrMore, empty, Suppress, replaceWith, Keyword, Group, Combine, Dict, delimitedList, Optional, CaselessKeyword

def parse():
    identifier = Word(alphas+"_",alphanums+"_")
    # Semicolon as end of line
    eol = Suppress(";")
    # test <name>; (NON-STANDARD IF)
    testdecl = Suppress(CaselessKeyword("test") + identifier + eol)
    # endtest; (NON-STANDARD IF)
    endtest = Suppress(CaselessKeyword("endtest") + eol)
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
    # input <name>(params...);
    ifinput= CaselessKeyword("input") + \
            (identifier +
                    Suppress("(") +
                    Group(ZeroOrMore(identifier + Optional(Suppress(",")))) +
                    Suppress(")")
            )\
            .setResultsName("input",listAllMatches=True) + eol
    # output <name>(params...);
    ifoutput= CaselessKeyword("output") + \
            (identifier +
                    Suppress("(") +
                    Group(ZeroOrMore(identifier + Optional(Suppress(",")))) +
                    Suppress(")")
            )\
            .setResultsName("output",listAllMatches=True) + eol
    # full state block
    state = statedecl + \
            OneOrMore(nextstate | ifexit | ifinput | ifoutput ) + \
            endstate
    # state group
    states = ZeroOrMore(Group(state))
    # full test block
    test = testdecl + states + endtest
    # test group
    tests = ZeroOrMore(Group(test))
    parsed = tests.parseFile("test_ex/test.if")
    return parsed

def getParams(paramlst):
    if len(paramlst) > 0:
        ret = '"{'
        for p in paramlst:
            ret += p + ","
        ret = ret[0:-1] + '}"'
        return ret
    else:
        return "NULL"

if __name__ == '__main__':
    parsed = parse()
    #print repr(parsed)
    #print parsed

    testn=0
    ordtestn=0
    signalid=0

    to_write = ""

    for elst in parsed:
        testn = testn + 1
        source = ""
        target = ""
        for selst in elst:
            el = list(selst)
            source = el[el.index('state') + 1]
            if source == target:
                pass #TODO
            else:
                pass #TODO
            target = el[el.index('nextstate') + 1]
            nsig = el.count("input") + el.count("output")
            to_write += """
                purposes[{testn}].numSignals = {nsig};
                purposes[{testn}].numSignals = {{{processname}}}0;
                purposes[{testn}].source = "{source}";
                purposes[{testn}].target = "{target}";
            """.format(nsig=nsig,processname="process",testn=testn-1,source=source,target=target) #TODO FALTA PROCESS!!!!

            signalindex=0
            for inp in selst.input:
                params = getParams(inp[1]) #TODO Recursividad
                to_write+= """
                    signalData signal{signalid} = {{"{inp}","input",{params}}};
                    purposes[{testn}].signals[{signalindex}] = signal{signalid};
                """.format(testn=testn-1,signalindex=signalindex,signalid=signalid,inp=inp[0],params=params)
                signalid+=1
                signalindex+=1
            for outp in selst.output:
                params = getParams(outp[1]) #TODO Recursividad
                to_write+= """
                    signalData signal{signalid} = {{"{outp}","output",{params}}};
                    purposes[{testn}].signals[{signalindex}] = signal{signalid};
                """.format(testn=testn-1,signalindex=signalindex,signalid=signalid,outp=outp[0],params=params)
                signalid+=1
                signalindex+=1

    f = open('test.C','w')

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
