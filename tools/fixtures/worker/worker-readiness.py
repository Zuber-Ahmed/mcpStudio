"""Trusted runtime/parser fixture only; no application repository analysis."""
import asyncio
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
from tree_sitter import Language, Parser
import tree_sitter_typescript
from temporalio import workflow
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner
from readiness_workflow import ReadinessWorkflow

checks=[]
def check(name,passed): checks.append({'name':name,'passed':bool(passed)})
def kinds(node):
    yield node.type
    for child in node.children:
        yield from kinds(child)
async def main():
    check('selected Python runtime',sys.version_info[:3]==(3,14,10))
    expected={'temporalio':'1.35.0','tree-sitter':'0.26.0','tree-sitter-typescript':'0.23.2'}
    versions={name:importlib.metadata.version(name) for name in expected}
    check('exact direct dependency pins',versions==expected)
    parser=Parser(Language(tree_sitter_typescript.language_typescript()))
    source=b'export function fixtureRead(id: string): string { return id; }'
    tree=parser.parse(source)
    check('TypeScript grammar parses typed function',not tree.root_node.has_error and 'function_declaration' in set(kinds(tree.root_node)))
    function=next(c for c in tree.root_node.children[0].children if c.type=='function_declaration')
    check('source byte range preserves evidence',source[function.start_byte:function.end_byte].startswith(b'function fixtureRead'))
    check('repeated parse is deterministic',str(parser.parse(source).root_node)==str(tree.root_node))
    invalid=parser.parse(b'export function broken( {')
    check('malformed syntax stays diagnostic',invalid.root_node.has_error)
    tsx=Parser(Language(tree_sitter_typescript.language_tsx()))
    view=tsx.parse(b'export const Page = () => <main>fixture</main>;')
    check('TSX grammar parses JSX',not view.root_node.has_error and 'jsx_element' in set(kinds(view.root_node)))
    canary=Path('/tmp/source-executed')
    malicious=b'require("fs").writeFileSync("/tmp/source-executed", "unsafe");'
    parsed=parser.parse(malicious)
    check('source script is parsed without execution',not parsed.root_node.has_error and not canary.exists())
    scope={'source_digest':hashlib.sha256(source).hexdigest(),'source_bytes':len(source)}
    definition=workflow._Definition.must_from_class(ReadinessWorkflow)
    check('Temporal workflow metadata loads',definition.name=='ReadinessWorkflow')
    try:
        SandboxedWorkflowRunner().prepare_workflow(definition)
        check('Temporal workflow sandbox prepares fixture',True)
    except Exception as ex:
        check('Temporal workflow sandbox prepares fixture',False)
        scope['temporal_error']=str(ex)
    check('container has no default network route',not any(line.split()[1]=='00000000' for line in Path('/proc/net/route').read_text().splitlines()[1:]))
    report={'scope':'Container runtime/parser and Temporal sandbox import readiness; no Temporal server or application analyzer',
        'python':sys.version,'dependencies':versions,'passed':all(c['passed'] for c in checks),
        'checks':checks,'fixture':scope,'network':'disabled by Docker',
        'remaining':'Actual workflow execution/retry/recovery and application discovery are not tested by this fixture.'}
    Path('/evidence/worker-runtime-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    if not report['passed']: raise SystemExit(1)
asyncio.run(main())
