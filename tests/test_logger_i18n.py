"""静态守门：GenshinUID 日志必须接入 t()，且 locales 三语结构完整。

对照 gsuid-core ``tests/test_logger_i18n.py``，本文件只扫本插件，不依赖 Core 源码。
"""

import re
import ast
import json
from typing import Set, Dict, List, Tuple, Iterable, Iterator, Optional
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import field, dataclass

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "GenshinUID"
_LOCALES = _ROOT / "locales"

_LOG_METHODS = {
    "trace",
    "debug",
    "info",
    "success",
    "warning",
    "warn",
    "error",
    "critical",
    "fatal",
    "exception",
    "log",
}
_LOGGER_CHAIN_METHODS = {"bind", "new", "unbind", "opt", "patch", "contextualize"}
_BRACE_FIELD_RE = re.compile(r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)(![rsa])?(?::([^{}]*))?\}(?!\})")
_PRINTF_FIELD_RE = re.compile(
    r"(?<!%)%(?!%)(?:\(([^)]+)\))?[-+#0 ]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[hlL]?([diouxXeEfFgGcrsa])"
)


@dataclass(eq=False)
class _Scope:
    parent: Optional["_Scope"] = None
    assignments: Dict[str, List[Optional[ast.AST]]] = field(default_factory=lambda: defaultdict(list))
    i18n_names: Set[str] = field(default_factory=set)
    logger_names: Set[str] = field(default_factory=set)
    logger_factories: Set[str] = field(default_factory=set)
    logging_modules: Set[str] = field(default_factory=set)
    structlog_modules: Set[str] = field(default_factory=set)


@dataclass
class _ParsedSource:
    path: Path
    source: str
    tree: ast.Module
    scopes: Dict[int, _Scope]
    module_scope: _Scope


class _ScopeBuilder(ast.NodeVisitor):
    def __init__(self, own_i18n_t: bool = False) -> None:
        self.module_scope = _Scope()
        if own_i18n_t:
            self.module_scope.i18n_names.add("t")
        self.current = self.module_scope
        self.scopes: Dict[int, _Scope] = {}

    def visit(self, node: ast.AST):  # type: ignore[no-untyped-def]
        self.scopes[id(node)] = self.current
        return super().visit(node)

    def _visit_child_scope(self, node: ast.AST, body: Iterable[ast.stmt], params: Iterable[str] = ()) -> None:
        previous = self.current
        self.current = _Scope(parent=previous)
        self.scopes[id(node)] = self.current
        for name in params:
            self.current.assignments[name].append(None)
        for stmt in body:
            self.visit(stmt)
        self.current = previous

    @staticmethod
    def _argument_names(args: ast.arguments) -> Iterator[str]:
        for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs):
            yield arg.arg
        if args.vararg is not None:
            yield args.vararg.arg
        if args.kwarg is not None:
            yield args.kwarg.arg

    @staticmethod
    def _target_names(target: ast.AST) -> Iterator[str]:
        if isinstance(target, ast.Name):
            yield target.id
        elif isinstance(target, (ast.List, ast.Tuple)):
            for item in target.elts:
                yield from _ScopeBuilder._target_names(item)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for dec in node.decorator_list:
            self.visit(dec)
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)
        if node.returns is not None:
            self.visit(node.returns)
        self._visit_child_scope(node, node.body, self._argument_names(node.args))

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def visit_Lambda(self, node: ast.Lambda) -> None:
        previous = self.current
        self.current = _Scope(parent=previous)
        self.scopes[id(node)] = self.current
        for name in self._argument_names(node.args):
            self.current.assignments[name].append(None)
        self.visit(node.body)
        self.current = previous

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for dec in node.decorator_list:
            self.visit(dec)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        self._visit_child_scope(node, node.body)

    def visit_Import(self, node: ast.Import) -> None:
        for item in node.names:
            bound = item.asname or item.name.split(".", 1)[0]
            if item.name == "logging":
                self.current.logging_modules.add(bound)
            elif item.name == "structlog":
                self.current.structlog_modules.add(bound)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for item in node.names:
            bound = item.asname or item.name
            if node.module == "gsuid_core.i18n" and item.name == "t":
                self.current.i18n_names.add(bound)
            elif node.module == "gsuid_core.logger" and item.name == "logger":
                self.current.logger_names.add(bound)
            elif node.module == "logging" and item.name == "getLogger":
                self.current.logger_factories.add(bound)
            elif node.module == "structlog" and item.name == "get_logger":
                self.current.logger_factories.add(bound)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            for name in self._target_names(target):
                self.current.assignments[name].append(node.value)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        for name in self._target_names(node.target):
            self.current.assignments[name].append(node.value)
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        for name in self._target_names(node.target):
            self.current.assignments[name].append(node.value)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        for name in self._target_names(node.target):
            self.current.assignments[name].append(None)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.visit_For(node)  # type: ignore[arg-type]

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if item.optional_vars is not None:
                for name in self._target_names(item.optional_vars):
                    self.current.assignments[name].append(None)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.visit_With(node)  # type: ignore[arg-type]

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.current.assignments[node.name].append(None)
        self.generic_visit(node)


def _parse_source(path: Path) -> _ParsedSource:
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(path))
    builder = _ScopeBuilder()
    builder.visit(tree)
    return _ParsedSource(path, source, tree, builder.scopes, builder.module_scope)


def _parse_text(source: str) -> _ParsedSource:
    tree = ast.parse(source, filename="<logger-i18n-test>")
    builder = _ScopeBuilder()
    builder.visit(tree)
    return _ParsedSource(Path("<logger-i18n-test>"), source, tree, builder.scopes, builder.module_scope)


def _iter_source_files() -> Iterator[Path]:
    for path in sorted(_SRC.rglob("*.py")):
        if "__pycache__" not in path.parts:
            yield path


def _lookup_scope_with_name(scope: _Scope, name: str) -> Optional[_Scope]:
    current: Optional[_Scope] = scope
    while current is not None:
        if (
            name in current.assignments
            or name in current.i18n_names
            or name in current.logger_names
            or name in current.logger_factories
            or name in current.logging_modules
            or name in current.structlog_modules
        ):
            return current
        current = current.parent
    return None


def _is_i18n_name(name: str, scope: _Scope) -> bool:
    owner = _lookup_scope_with_name(scope, name)
    return owner is not None and name in owner.i18n_names and name not in owner.assignments


def _is_i18n_call(node: ast.AST, scope: _Scope) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and _is_i18n_name(node.func.id, scope)


def _looks_like_logger_name(name: str) -> bool:
    lowered = name.lower()
    return lowered in {"logger", "_logger", "_slg"} or lowered.endswith("_logger")


def _is_factory_call(node: ast.Call, scope: _Scope) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        owner = _lookup_scope_with_name(scope, func.id)
        return owner is not None and func.id in owner.logger_factories
    if not isinstance(func, ast.Attribute) or not isinstance(func.value, ast.Name):
        return False
    owner = _lookup_scope_with_name(scope, func.value.id)
    if owner is None:
        return False
    return (func.attr == "getLogger" and func.value.id in owner.logging_modules) or (
        func.attr == "get_logger" and func.value.id in owner.structlog_modules
    )


def _is_logger_expr(node: ast.AST, scope: _Scope, seen: Optional[Set[Tuple[int, str]]] = None) -> bool:
    if seen is None:
        seen = set()
    if isinstance(node, ast.Name):
        owner = _lookup_scope_with_name(scope, node.id)
        if owner is not None and node.id in owner.logger_names:
            return True
        if owner is not None and node.id in owner.assignments:
            marker = (id(owner), node.id)
            if marker in seen:
                return False
            seen.add(marker)
            return any(
                value is not None and _is_logger_expr(value, owner, seen) for value in owner.assignments[node.id]
            )
        return _looks_like_logger_name(node.id)
    if isinstance(node, ast.Attribute):
        return _looks_like_logger_name(node.attr)
    if not isinstance(node, ast.Call):
        return False
    if _is_factory_call(node, scope):
        return True
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr in _LOGGER_CHAIN_METHODS
        and _is_logger_expr(node.func.value, scope, seen)
    )


def _logger_message(node: ast.Call) -> Optional[ast.AST]:
    if not isinstance(node.func, ast.Attribute):
        return None
    position = 1 if node.func.attr == "log" else 0
    if len(node.args) > position:
        return node.args[position]
    for keyword in node.keywords:
        if keyword.arg in {"event", "msg", "message"}:
            return keyword.value
    return None


def _is_logger_call(node: ast.Call, scope: _Scope) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr in _LOG_METHODS
        and _is_logger_expr(node.func.value, scope)
    )


def _combine_message_states(states: Iterable[str]) -> str:
    state_set = set(states)
    if "static" in state_set:
        return "static"
    if state_set == {"translated"}:
        return "translated"
    return "dynamic"


def _message_state(
    node: ast.AST,
    scope: _Scope,
    seen: Optional[Set[Tuple[int, str]]] = None,
) -> str:
    if seen is None:
        seen = set()
    if _is_i18n_call(node, scope):
        return "translated"
    if isinstance(node, ast.Name):
        owner = _lookup_scope_with_name(scope, node.id)
        if owner is None or node.id not in owner.assignments:
            return "dynamic"
        marker = (id(owner), node.id)
        if marker in seen:
            return "dynamic"
        seen.add(marker)
        states = [_message_state(value, owner, seen) for value in owner.assignments[node.id] if value is not None]
        return _combine_message_states(states) if states else "dynamic"
    if isinstance(node, ast.Constant):
        return "static" if isinstance(node.value, str) else "dynamic"
    if isinstance(node, ast.JoinedStr):
        return "static" if any(isinstance(value, ast.Constant) for value in node.values) else "dynamic"
    if isinstance(node, ast.BinOp):
        return _combine_message_states(
            (_message_state(node.left, scope, seen), _message_state(node.right, scope, seen))
        )
    if isinstance(node, ast.IfExp):
        return _combine_message_states(
            (_message_state(node.body, scope, seen), _message_state(node.orelse, scope, seen))
        )
    if isinstance(node, ast.NamedExpr):
        return _message_state(node.value, scope, seen)
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"format", "format_map"}:
            return _message_state(node.func.value, scope, seen)
        return "dynamic"
    return "dynamic"


def _translated_sources(
    node: ast.AST,
    scope: _Scope,
    seen: Optional[Set[Tuple[int, str]]] = None,
) -> List[ast.Call]:
    if seen is None:
        seen = set()
    if _is_i18n_call(node, scope):
        assert isinstance(node, ast.Call)
        return [node]
    if not isinstance(node, ast.Name):
        return []
    owner = _lookup_scope_with_name(scope, node.id)
    if owner is None or node.id not in owner.assignments:
        return []
    marker = (id(owner), node.id)
    if marker in seen:
        return []
    seen.add(marker)
    calls: List[ast.Call] = []
    for value in owner.assignments[node.id]:
        if value is not None:
            calls.extend(_translated_sources(value, owner, seen))
    return calls


def _scope_for(parsed: _ParsedSource, node: ast.AST) -> _Scope:
    # 参数注解等表达式在定义函数时由外层作用域求值；ScopeBuilder 不需要深入记录
    # 它们，扫描时回落模块作用域即可。实际函数体和类体中的节点都会有精确 scope。
    return parsed.scopes.get(id(node), parsed.module_scope)


def _collect_logger_violations(parsed: _ParsedSource) -> Tuple[List[str], int]:
    violations: List[str] = []
    count = 0
    for node in ast.walk(parsed.tree):
        if not isinstance(node, ast.Call):
            continue
        scope = _scope_for(parsed, node)
        if not _is_logger_call(node, scope):
            continue
        count += 1
        message = _logger_message(node)
        if message is None:
            continue
        state = _message_state(message, scope)
        if state == "static":
            violations.append(f"L{node.lineno}: {ast.unparse(node)}")
            continue
        if state != "translated":
            continue
        for source in _translated_sources(message, scope):
            key_arg = source.args[0] if source.args else None
            if not isinstance(key_arg, ast.Constant) or not isinstance(key_arg.value, str):
                violations.append(f"L{node.lineno}: logger 中的 t() 必须使用静态字符串 key: {ast.unparse(node)}")
                continue
            key = key_arg.value
            if not re.match(r"^log\.[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$", key):
                violations.append(f"L{node.lineno}: logger t() key 必须为 log.<module>.<semantic>，实际: {key!r}")
    return violations, count


def _reject_duplicate_keys(pairs: List[Tuple[str, object]]) -> Dict[str, object]:
    result: Dict[str, object] = {}
    duplicates: Set[str] = set()
    for key, value in pairs:
        if key in result:
            duplicates.add(key)
        result[key] = value
    if duplicates:
        raise ValueError(f"重复 key: {', '.join(sorted(duplicates))}")
    return result


def _load_catalog_file(path: Path) -> Dict[str, str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as e:
        raise AssertionError(f"{path.relative_to(_ROOT).as_posix()} 不是完整有效的 locale JSON: {e}") from e
    assert isinstance(raw, dict), f"{path.relative_to(_ROOT).as_posix()} 顶层必须是 JSON 对象"
    invalid = [
        repr(key)
        for key, value in raw.items()
        if not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip()
    ]
    assert not invalid, f"{path.relative_to(_ROOT).as_posix()} 含非字符串或空 key/value: {invalid[:20]}"
    return raw  # type: ignore[return-value]


def _load_catalogs() -> Dict[str, Dict[str, str]]:
    """支持 ``locales/<lang>/*.json`` 目录布局；兼容遗留单文件 ``locales/<lang>.json``。"""
    catalogs: Dict[str, Dict[str, str]] = {}
    if not _LOCALES.is_dir():
        return catalogs
    for path in sorted(_LOCALES.iterdir()):
        if path.is_dir() and not path.name.startswith((".", "_")):
            merged: Dict[str, str] = {}
            for f in sorted(path.glob("*.json")):
                part = _load_catalog_file(f)
                overlap = set(merged) & set(part)
                assert not overlap, f"{path.name}/ 模块间重复 key: {sorted(overlap)[:20]}"
                merged.update(part)
            catalogs[path.name] = merged
        elif path.is_file() and path.suffix == ".json":
            catalogs[path.stem] = _load_catalog_file(path)
    return catalogs


def _placeholder_signature(text: str) -> Tuple[Counter, Counter]:
    brace = Counter(
        (match.group(1), match.group(2) or "", match.group(3) or "") for match in _BRACE_FIELD_RE.finditer(text)
    )
    printf = Counter((match.group(1) or "", match.group(2)) for match in _PRINTF_FIELD_RE.finditer(text))
    return brace, printf


def _iter_i18n_calls(parsed: _ParsedSource) -> Iterator[ast.Call]:
    for node in ast.walk(parsed.tree):
        if isinstance(node, ast.Call) and _is_i18n_call(node, _scope_for(parsed, node)):
            yield node


def _format_offenders(offenders: Iterable[str]) -> str:
    return "\n".join(f"  {item}" for item in offenders)


def test_logger_detector_covers_supported_forms() -> None:
    parsed = _parse_text(
        """
import logging
import structlog
from gsuid_core.i18n import t as i18n_t
from gsuid_core.logger import logger

logger.trace("trace literal")
logger.bind(component="x").debug(f"debug {value}")
logger.log("INFO", "log literal")
message = "indirect literal"
logger.warning(message)
stdlib_logger = logging.getLogger(__name__)
stdlib_logger.error("stdlib literal")
struct_logger = structlog.get_logger("test")
struct_logger.info(i18n_t("log.good.ok"))
logger.exception(error)
"""
    )
    violations, count = _collect_logger_violations(parsed)
    assert count == 7
    assert len(violations) == 5
    assert any("trace literal" in item for item in violations)
    assert any("logger.warning(message)" in item for item in violations)
    assert not any("log.good.ok" in item for item in violations)


def test_all_plugin_logger_messages_use_i18n() -> None:
    offenders: List[str] = []
    count = 0
    for path in _iter_source_files():
        parsed = _parse_source(path)
        violations, file_count = _collect_logger_violations(parsed)
        count += file_count
        rel = path.relative_to(_ROOT).as_posix()
        offenders.extend(f"{rel}:{item}" for item in violations)

    assert count > 100, f"只识别到 {count} 个 logger 调用，扫描器可能已失效"
    assert not offenders, "以下插件日志含未接入 t() 的静态文案：\n" + _format_offenders(offenders)


def test_locale_languages_exist() -> None:
    found = {p.name for p in _LOCALES.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))}
    assert found == {"zh-cn", "en", "ja"}, f"locale 语言目录应为 zh-cn/en/ja，实际 {sorted(found)}"


def test_locale_catalogs_have_identical_keys_and_placeholders() -> None:
    catalogs = _load_catalogs()
    assert catalogs, "未找到 locale JSON"
    reference_lang = "zh-cn"
    assert reference_lang in catalogs, "缺少基准语言 zh-cn/"
    reference = catalogs[reference_lang]
    offenders: List[str] = []

    for lang, catalog in catalogs.items():
        missing = sorted(set(reference) - set(catalog))
        extra = sorted(set(catalog) - set(reference))
        if missing or extra:
            offenders.append(f"{lang}: 缺失={missing[:20]}，多余={extra[:20]}")
            continue
        for key, reference_text in reference.items():
            if _placeholder_signature(reference_text) != _placeholder_signature(catalog[key]):
                offenders.append(
                    f"{lang}: {key!r} 占位符不一致: "
                    f"zh-cn={_placeholder_signature(reference_text)!r}, "
                    f"{lang}={_placeholder_signature(catalog[key])!r}"
                )

    assert not offenders, "locale key 或占位符不完整：\n" + _format_offenders(offenders)


def test_static_i18n_keys_exist_and_format_kwargs_are_complete() -> None:
    catalogs = _load_catalogs()
    offenders: List[str] = []
    for path in _iter_source_files():
        parsed = _parse_source(path)
        rel = path.relative_to(_ROOT).as_posix()
        for call in _iter_i18n_calls(parsed):
            if not call.args or not isinstance(call.args[0], ast.Constant) or not isinstance(call.args[0].value, str):
                continue
            key = call.args[0].value
            missing_langs = [lang for lang, catalog in catalogs.items() if key not in catalog]
            if missing_langs:
                offenders.append(f"{rel}:L{call.lineno}: {key!r} 缺少 locale: {missing_langs}")
                continue
            required = {item[0] for item in _placeholder_signature(catalogs["zh-cn"][key])[0]}
            if any(keyword.arg is None for keyword in call.keywords):
                continue
            provided = {keyword.arg for keyword in call.keywords if keyword.arg not in {None, "lang"}}
            missing_params = sorted(required - provided)
            if missing_params:
                offenders.append(
                    f"{rel}:L{call.lineno}: {key!r} 未传具名占位符 {missing_params}; 调用={ast.unparse(call)}"
                )

    assert not offenders, "静态 i18n key 或调用参数不完整：\n" + _format_offenders(offenders)


def test_duplicate_locale_key_detector_is_active() -> None:
    with pytest.raises(ValueError, match="重复 key"):
        json.loads('{"same": "first", "same": "second"}', object_pairs_hook=_reject_duplicate_keys)
