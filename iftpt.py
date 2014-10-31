from pyparsing import Word, alphas, alphanums, Literal, restOfLine, OneOrMore, ZeroOrMore, empty, Suppress, replaceWith, Keyword, Group, Combine, Dict

def main():
    eol = Suppress(";")
    statedecl = Keyword("state") + Word(alphas+"_",alphanums+"_") + eol
    endstate = Keyword("endstate") + eol
    nextstate = Keyword("nextstate") + Word(alphas+"_",alphanums+"_") + eol
    ifexit = Keyword("exit") + eol
    state = statedecl + OneOrMore(nextstate | ifexit) + endstate
    states = ZeroOrMore(Group(state))
    la = states.parseString("state lala; nextstate po; endstate;state carlito;nextstate desastre; endstate;")
    print la

if __name__ == '__main__':
    main()
    	

