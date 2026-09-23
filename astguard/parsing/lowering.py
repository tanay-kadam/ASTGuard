"""Tree-sitter C/C++ structured scalar event lowering.

Memory writes, aliases and callee effects are deliberately outside the relation
semantics. Ambiguous modifying expressions fail the entire DFG.
"""
from __future__ import annotations

from dataclasses import dataclass

from .cfg import Event, StructuredCFG
from .dfg import DFGExtraction
from .reaching_defs import ReachingDefinitions
from .scopes import ScopeResolver


class UnsupportedFlow(ValueError):
    pass


class TreeCFGBuilder:
    forbidden = {'goto_statement', 'switch_statement', 'case_statement', 'try_statement',
                 'throw_statement', 'lambda_expression', 'co_await_expression',
                 'co_yield_statement', 'preproc_if', 'preproc_ifdef', 'preproc_elif',
                 'structured_binding_declarator', 'for_range_loop'}

    def __init__(self, source, tree, tokens):
        self.source = source.encode('utf-8')
        self.tree = tree
        self.tokens = tokens
        self.token_ids = {(t.start_byte, t.end_byte): t.id for t in tokens}
        self.resolver = ScopeResolver()
        self.scope = self.resolver.new_scope()
        self.events = {0: Event(0, 'noop', None, None)}
        self.successors = {0: set()}
        self.bindings = {}
        self.loops = []

    def text(self, node):
        return self.source[node.start_byte:node.end_byte].decode('utf-8')

    def occurrence(self, node):
        key = (node.start_byte, node.end_byte)
        if key not in self.token_ids:
            raise UnsupportedFlow('identifier_alignment')
        return self.token_ids[key]

    def emit(self, tails, kind='noop', binding=None, occurrence=None, reads=()):
        index = len(self.events)
        self.events[index] = Event(index, kind, binding, occurrence, tuple(reads))
        self.successors[index] = set()
        for tail in tails:
            self.successors[tail].add(index)
        return {index}

    def connect(self, tails, targets):
        for tail in tails:
            self.successors[tail].update(targets)

    def descendants(self, node):
        yield node
        for child in node.named_children:
            yield from self.descendants(child)

    def identifier(self, node):
        if node is None:
            raise UnsupportedFlow('missing_declarator')
        if node.type == 'identifier':
            return node
        if node.type in {'pointer_declarator','reference_declarator','array_declarator',
                          'parenthesized_declarator','function_declarator'}:
            candidate = node.child_by_field_name('declarator')
            if candidate is None and node.named_children:
                candidate = node.named_children[0]
            return self.identifier(candidate)
        raise UnsupportedFlow('binding:' + node.type)

    def declare(self, node, tails, parameter=False):
        target = node.child_by_field_name('declarator') if node.type == 'init_declarator' else node
        ident = self.identifier(target)
        occurrence = self.occurrence(ident)
        binding = self.scope.declare(self.text(ident), occurrence)
        self.bindings[occurrence] = binding
        value = node.child_by_field_name('value') if node.type == 'init_declarator' else None
        if value is not None:
            tails, reads = self.expr(value, tails)
            return self.emit(tails, 'write', binding, occurrence, reads)
        if parameter:
            return self.emit(tails, 'write', binding, occurrence)
        return tails

    def modifying(self, node):
        return any(n.type in {'assignment_expression','update_expression'} for n in self.descendants(node))

    def read(self, node, tails):
        occurrence = self.occurrence(node)
        binding = self.scope.resolve(self.text(node))
        if binding is not None:
            self.bindings[occurrence] = binding
            tails = self.emit(tails, 'read', binding, occurrence)
        # Unknown scalar reads have no invented definition but may source an RHS.
        return tails, [occurrence]

    def expr(self, node, tails):
        if node is None:
            return tails, []
        kind = node.type
        if kind == 'identifier':
            return self.read(node, tails)
        if kind in {'number_literal','string_literal','char_literal','true','false','null','nullptr',
                    'type_identifier','primitive_type','sizeof_expression','alignof_expression'}:
            return tails, []
        if kind in {'field_expression','subscript_expression'}:
            operands = [node.child_by_field_name('argument')] if kind == 'field_expression' else [node.child_by_field_name('argument'),node.child_by_field_name('index')]
            return self.sequence(operands, tails)
        if kind == 'call_expression':
            arguments = node.child_by_field_name('arguments')
            children = arguments.named_children if arguments is not None else []
            if any(self.modifying(child) for child in children):
                raise UnsupportedFlow('modifying_call_argument')
            return self.sequence(children, tails)
        if kind == 'assignment_expression':
            left, right = node.child_by_field_name('left'), node.child_by_field_name('right')
            if self.modifying(right):
                raise UnsupportedFlow('nested_modifying_expression')
            operator = node.child_by_field_name('operator')
            op = self.text(operator) if operator is not None else '='
            if left.type != 'identifier':
                # Base/index reads are retained, but memory writes define no scalar.
                return self.sequence([left, right], tails)
            binding = self.scope.resolve(self.text(left))
            if binding is None:
                return self.expr(right, tails)
            occurrence = self.occurrence(left)
            self.bindings[occurrence] = binding
            old = []
            if op != '=':
                tails, old = self.read(left, tails)
            tails, reads = self.expr(right, tails)
            return self.emit(tails, 'write', binding, occurrence, old + reads), old + reads
        if kind == 'update_expression':
            argument = node.child_by_field_name('argument')
            if argument is None or argument.type != 'identifier':
                raise UnsupportedFlow('non_scalar_update')
            binding = self.scope.resolve(self.text(argument))
            tails, reads = self.read(argument, tails)
            if binding:
                tails = self.emit(tails, 'write', binding, self.occurrence(argument), reads)
            return tails, reads
        if kind == 'conditional_expression':
            tails, conditions = self.expr(node.child_by_field_name('condition'), tails)
            a, ra = self.expr(node.child_by_field_name('consequence'), tails)
            b, rb = self.expr(node.child_by_field_name('alternative'), tails)
            return a | b, conditions + ra + rb
        if kind == 'binary_expression':
            left, right = node.child_by_field_name('left'), node.child_by_field_name('right')
            operator = node.child_by_field_name('operator')
            op = self.text(operator) if operator else ''
            if op in {'&&','||'}:
                tails, reads = self.expr(left, tails)
                branch, more = self.expr(right, tails)
                return tails | branch, reads + more
            if self.modifying(left) or self.modifying(right):
                raise UnsupportedFlow('unsequenced_modifying_expression')
        if kind in self.forbidden:
            raise UnsupportedFlow(kind)
        return self.sequence(node.named_children, tails)

    def sequence(self, nodes, tails):
        reads = []
        for node in nodes:
            tails, current = self.expr(node, tails)
            reads.extend(current)
        return tails, reads

    def statement(self, node, tails):
        if node is None or not tails:
            return tails
        kind = node.type
        if kind == 'compound_statement':
            outer = self.scope
            self.scope = self.resolver.new_scope(outer)
            for child in node.named_children:
                tails = self.statement(child, tails)
            self.scope = outer
            return tails
        if kind == 'declaration':
            for child in node.children_by_field_name('declarator'):
                tails = self.declare(child, tails)
            return tails
        if kind == 'if_statement':
            tails, _ = self.expr(node.child_by_field_name('condition'), tails)
            left = self.statement(node.child_by_field_name('consequence'), tails)
            right = self.statement(node.child_by_field_name('alternative'), tails)
            return left | right
        if kind == 'else_clause':
            for child in node.named_children:
                tails = self.statement(child, tails)
            return tails
        if kind in {'while_statement','for_statement','do_statement'}:
            outer = self.scope
            self.scope = self.resolver.new_scope(outer)
            initializer = node.child_by_field_name('initializer')
            if initializer is not None:
                tails = self.statement(initializer, tails)
            condition_entry = self.emit(set())
            exit_node = self.emit(set())
            update_entry = self.emit(set()) if kind == 'for_statement' else condition_entry
            body_entry = self.emit(set())
            self.connect(tails, body_entry if kind == 'do_statement' else condition_entry)
            condition = node.child_by_field_name('condition')
            condition_tails, _ = self.expr(condition, condition_entry)
            self.connect(condition_tails, body_entry)
            if condition is not None:
                self.connect(condition_tails, exit_node)
            self.loops.append((exit_node, update_entry))
            body_tails = self.statement(node.child_by_field_name('body'), body_entry)
            self.loops.pop()
            self.connect(body_tails, update_entry)
            if kind == 'for_statement':
                updates, _ = self.expr(node.child_by_field_name('update'), update_entry)
                self.connect(updates, condition_entry)
            self.scope = outer
            return exit_node
        if kind == 'break_statement':
            if not self.loops:
                raise UnsupportedFlow('break_outside_loop')
            self.connect(tails, self.loops[-1][0])
            return set()
        if kind == 'continue_statement':
            if not self.loops:
                raise UnsupportedFlow('continue_outside_loop')
            self.connect(tails, self.loops[-1][1])
            return set()
        if kind == 'return_statement':
            self.sequence(node.named_children, tails)
            return set()
        if kind == 'comment':
            return tails
        return self.expr(node, tails)[0]

    def build(self):
        root = self.tree.native_root
        for node in self.descendants(root):
            if node.type in self.forbidden:
                raise UnsupportedFlow(node.type)
        functions = [node for node in root.named_children if node.type == 'function_definition']
        if not functions and not self.source.strip():
            return StructuredCFG(self.events, self.successors, 0)
        if len(functions) != 1:
            raise UnsupportedFlow('expected_one_function_definition')
        function = functions[0]
        tails = {0}
        declarator = function.child_by_field_name('declarator')
        for node in self.descendants(declarator):
            if node.type == 'parameter_declaration':
                parameter = node.child_by_field_name('declarator')
                if parameter is not None:
                    tails = self.declare(parameter, tails, parameter=True)
        self.statement(function.child_by_field_name('body'), tails)
        return StructuredCFG(self.events, self.successors, 0)

    def build_visible_prefix(self, boundary: int):
        """Lower only complete supported statements wholly inside a visible prefix."""
        root=self.tree.native_root
        functions=[node for node in self.descendants(root) if node.type=='function_definition' and node.start_byte < boundary]
        if len(functions) != 1:
            raise UnsupportedFlow('visible_prefix_expected_one_function')
        function=functions[0];tails={0}
        declarator=function.child_by_field_name('declarator')
        if declarator is not None:
            for node in self.descendants(declarator):
                if node.type=='parameter_declaration' and node.end_byte<=boundary and not node.has_error:
                    parameter=node.child_by_field_name('declarator')
                    if parameter is not None:tails=self.declare(parameter,tails,parameter=True)
        body=function.child_by_field_name('body')
        if body is None:return StructuredCFG(self.events,self.successors,0)
        outer=self.scope;self.scope=self.resolver.new_scope(outer)
        for child in body.named_children:
            if child.end_byte>boundary or child.has_error or child.is_missing:
                continue
            tails=self.statement(child,tails)
        self.scope=outer
        return StructuredCFG(self.events,self.successors,0)


def extract_dependencies(source, tree, tokens):
    if not tree.successful:
        return DFGExtraction('parse_failed', (), {}, ('parse_failed',))
    builder = TreeCFGBuilder(source, tree, tokens)
    try:
        cfg = builder.build()
        result = ReachingDefinitions().solve(cfg)
        return DFGExtraction('ok', tuple(result.dependency_edges), builder.bindings)
    except UnsupportedFlow as exc:
        return DFGExtraction('unsupported', (), {}, (str(exc),))


def extract_visible_prefix_dependencies(source, tree, tokens, boundary):
    """DFG for complete supported statements, without omitted-suffix facts."""
    builder=TreeCFGBuilder(source,tree,tokens)
    try:
        cfg=builder.build_visible_prefix(boundary)
        result=ReachingDefinitions().solve(cfg)
        return DFGExtraction('ok',tuple(result.dependency_edges),builder.bindings,('visible_prefix_complete_statements',))
    except UnsupportedFlow as exc:
        return DFGExtraction('unsupported',(),{},(str(exc),))
