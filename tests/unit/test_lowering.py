from astguard.parsing.lexical import lex
from astguard.parsing.trees import select_c_or_cpp
from astguard.parsing.lowering import extract_dependencies,extract_visible_prefix_dependencies


def graph(source):
    tokens = lex(source)
    result = extract_dependencies(source,select_c_or_cpp(source),tokens)
    assert result.status == 'ok', result.reasons
    return tokens, set(result.edges)


def occurrences(tokens,name):
    return [token.id for token in tokens if token.text == name]


def test_parameter_definition_and_rhs_read():
    tokens,edges = graph('int f(int x){int y=x; return y;}')
    x0,x1 = occurrences(tokens,'x')
    y0,y1 = occurrences(tokens,'y')
    assert edges == {(x1,x0),(y0,x1),(y1,y0)}


def test_branch_union():
    tokens,edges = graph('int f(int p){int x=0; if(p){x=1;}else{x=2;} return x;}')
    x0,x1,x2,x3 = occurrences(tokens,'x')
    assert (x3,x1) in edges and (x3,x2) in edges
    assert (x3,x0) not in edges


def test_loop_fixed_point_and_continue():
    tokens,edges = graph('int f(int p){int x=0; while(p){x=x+1; continue;} return x;}')
    x0,x1,x2,x3 = occurrences(tokens,'x')
    assert {(x2,x0),(x2,x1),(x1,x2),(x3,x0),(x3,x1)} <= edges


def test_shadowed_binding_survives():
    tokens,edges = graph('int f(int x){{int x=1; x=x+1;} return x;}')
    outer,inner,write,read,ret = occurrences(tokens,'x')
    assert (ret,outer) in edges
    assert (read,inner) in edges
    assert (ret,write) not in edges


def test_unsupported_switch_and_syntax_failure():
    for source in ['int f(int x){switch(x){case 1:return 0;}return 1;}', 'int f( {']:
        result = extract_dependencies(source,select_c_or_cpp(source),lex(source))
        assert result.status in {'unsupported','parse_failed'}
        assert not result.edges


def test_visible_prefix_uses_only_complete_statements():
    source='int f(int x){ int y=x; y=y+1; return y; }'
    boundary=source.index('y=y+1')
    raw=source.encode()
    visible=(raw[:boundary]+bytes(10 if value==10 else 32 for value in raw[boundary:])).decode()
    tokens=lex(source)
    result=extract_visible_prefix_dependencies(visible,select_c_or_cpp(visible),tokens,boundary)
    assert result.status=='ok'
    x0,x1=occurrences(tokens,'x')
    y0,*_=occurrences(tokens,'y')
    assert set(result.edges)=={(x1,x0),(y0,x1)}
    touched={item for edge in result.edges for item in edge}
    assert all(tokens[item].end_byte<=boundary for item in touched)
