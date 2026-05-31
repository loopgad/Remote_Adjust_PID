#!/usr/bin/env python3
"""
Git Pre-commit Hook - 关联文件检测

检测 staged 文件是否需要同步更新关联文件。
基于 .git-hooks-config.yml 配置文件中的规则进行检查。

用法:
    在 .git/hooks/pre-commit 中调用此脚本
    或通过 install-hooks.py 安装

退出码:
    0 - 所有检查通过
    1 - 存在阻塞级别问题
    2 - 存在警告但允许提交 (保留，当前未使用)
"""

import glob
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ============================================================================
# 数据类
# ============================================================================
@dataclass
class RelatedFile:
    """关联文件信息"""
    path: str
    exists: bool
    is_staged: bool = False


@dataclass
class RuleMatch:
    """规则匹配结果"""
    rule_name: str
    description: str
    severity: str  # warn or block
    message: str
    source_file: str
    related_files: list[RelatedFile] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)


@dataclass
class CheckResult:
    """检查结果"""
    passed: bool
    warnings: list[RuleMatch] = field(default_factory=list)
    blocks: list[RuleMatch] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ============================================================================
# 颜色管理 (实例级别，不污染全局)
# ============================================================================
class Colors:
    """ANSI 颜色代码，支持禁用"""
    def __init__(self, enabled: bool = True):
        if enabled and sys.stdout.isatty():
            self.RED = '\033[91m'
            self.YELLOW = '\033[93m'
            self.GREEN = '\033[92m'
            self.BLUE = '\033[94m'
            self.CYAN = '\033[96m'
            self.RESET = '\033[0m'
            self.BOLD = '\033[1m'
        else:
            self.RED = ''
            self.YELLOW = ''
            self.GREEN = ''
            self.BLUE = ''
            self.CYAN = ''
            self.RESET = ''
            self.BOLD = ''


# ============================================================================
# 路径工具
# ============================================================================
def normalize_path(filepath: str) -> str:
    """统一使用正斜杠，便于跨平台匹配"""
    return filepath.replace('\\', '/')


# ============================================================================
# 配置加载
# ============================================================================
class ConfigLoader:
    """加载和解析 YAML 配置文件"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config: dict[str, Any] = {}

    def load(self) -> dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        # 尝试使用 PyYAML
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            # 处理空文件或无效 YAML
            if self.config is None:
                self.config = {}
            return self.config
        except ImportError:
            pass

        # 回退到简单的 YAML 解析器
        return self._parse_simple_yaml()

    def _parse_simple_yaml(self) -> dict[str, Any]:
        """简单的 YAML 解析器（不依赖 PyYAML）"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 移除注释
        lines = []
        for line in content.split('\n'):
            if '#' in line:
                in_quote = False
                quote_char = None
                for i, char in enumerate(line):
                    if char in '"\'':
                        if not in_quote:
                            in_quote = True
                            quote_char = char
                        elif char == quote_char:
                            in_quote = False
                    elif char == '#' and not in_quote:
                        line = line[:i]
                        break
            lines.append(line)

        content = '\n'.join(lines)

        result: dict[str, Any] = {}
        lines = content.split('\n')
        self._parse_yaml_dict(lines, 0, result)
        return result

    def _parse_yaml_dict(self, lines: list[str], start: int, container: dict[str, Any], base_indent: int = -1) -> int:
        """解析 YAML 字典"""
        i = start
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped or stripped.startswith('#'):
                i += 1
                continue

            indent = len(line) - len(line.lstrip())

            # 缩进回退到父级，返回
            if indent <= base_indent:
                return i

            if ':' in stripped:
                key, _, value = stripped.partition(':')
                key = key.strip()
                value = value.strip()

                if value:
                    container[key] = self._parse_yaml_value(value)
                    i += 1
                else:
                    next_i = i + 1
                    while next_i < len(lines) and not lines[next_i].strip():
                        next_i += 1

                    if next_i < len(lines):
                        next_line = lines[next_i].strip()
                        next_indent = len(lines[next_i]) - len(lines[next_i].lstrip())

                        if next_line.startswith('- '):
                            container[key] = []
                            i = self._parse_yaml_list(lines, next_i, next_indent, container[key])
                        elif next_indent > indent:
                            container[key] = {}
                            i = self._parse_yaml_dict(lines, next_i, container[key], indent)
                        else:
                            container[key] = None
                            i += 1
                    else:
                        container[key] = None
                        i += 1
            else:
                i += 1

        return i

    def _parse_yaml_list(self, lines: list[str], start: int, base_indent: int, container: list) -> int:
        """解析 YAML 列表"""
        i = start
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped or stripped.startswith('#'):
                i += 1
                continue

            indent = len(line) - len(line.lstrip())

            if indent < base_indent:
                return i

            if stripped.startswith('- '):
                value = stripped[2:].strip()

                if ':' in value:
                    dict_item: dict[str, Any] = {}
                    container.append(dict_item)

                    key, _, val = value.partition(':')
                    key = key.strip()
                    val = val.strip()

                    if val:
                        dict_item[key] = self._parse_yaml_value(val)
                        i += 1
                    else:
                        lookahead_i = i + 1
                        while lookahead_i < len(lines) and not lines[lookahead_i].strip():
                            lookahead_i += 1

                        if lookahead_i < len(lines):
                            lookahead_line = lines[lookahead_i].strip()
                            lookahead_indent = len(lines[lookahead_i]) - len(lines[lookahead_i].lstrip())

                            if lookahead_line.startswith('- '):
                                dict_item[key] = []
                                i = self._parse_yaml_list(lines, lookahead_i, lookahead_indent, dict_item[key])
                            elif lookahead_indent > indent:
                                dict_item[key] = {}
                                i = self._parse_yaml_dict(lines, lookahead_i, dict_item[key], indent)
                            else:
                                dict_item[key] = None
                                i += 1
                        else:
                            dict_item[key] = None
                            i += 1

                    while i < len(lines):
                        next_line = lines[i]
                        next_stripped = next_line.strip()

                        if not next_stripped or next_stripped.startswith('#'):
                            i += 1
                            continue

                        next_indent = len(next_line) - len(next_line.lstrip())

                        if next_indent <= base_indent:
                            break

                        if ':' in next_stripped:
                            next_key, _, next_val = next_stripped.partition(':')
                            next_key = next_key.strip()
                            next_val = next_val.strip()

                            if next_val:
                                dict_item[next_key] = self._parse_yaml_value(next_val)
                                i += 1
                            else:
                                lookahead_i = i + 1
                                while lookahead_i < len(lines) and not lines[lookahead_i].strip():
                                    lookahead_i += 1

                                if lookahead_i < len(lines):
                                    lookahead_line = lines[lookahead_i].strip()
                                    lookahead_indent = len(lines[lookahead_i]) - len(lines[lookahead_i].lstrip())

                                    if lookahead_line.startswith('- '):
                                        dict_item[next_key] = []
                                        i = self._parse_yaml_list(lines, lookahead_i, lookahead_indent, dict_item[next_key])
                                    elif lookahead_indent > next_indent:
                                        dict_item[next_key] = {}
                                        i = self._parse_yaml_dict(lines, lookahead_i, dict_item[next_key], next_indent)
                                    else:
                                        dict_item[next_key] = None
                                        i += 1
                                else:
                                    dict_item[next_key] = None
                                    i += 1
                        else:
                            i += 1
                else:
                    container.append(self._parse_yaml_value(value))
                    i += 1
            else:
                i += 1

        return i

    def _parse_yaml_value(self, value: str) -> Any:
        """解析 YAML 值"""
        if not value:
            return None

        # 移除引号
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            return value[1:-1]

        # 布尔值
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        elif value.lower() in ('null', '~'):
            return None

        # 数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        return value


# ============================================================================
# Git 操作
# ============================================================================
class GitHelper:
    """Git 操作辅助类"""

    @staticmethod
    def get_staged_files() -> list[str]:
        """获取 staged 文件列表 (已统一为正斜杠)"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
                capture_output=True,
                text=True,
                check=True
            )
            return [normalize_path(f.strip()) for f in result.stdout.split('\n') if f.strip()]
        except subprocess.CalledProcessError:
            return []

    @staticmethod
    def get_staged_files_with_status() -> dict[str, str]:
        """获取 staged 文件及其状态 (已统一为正斜杠)"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-status', '--diff-filter=ACMR'],
                capture_output=True,
                text=True,
                check=True
            )
            files = {}
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        status, filepath = parts[0], normalize_path(parts[1])
                        files[filepath] = status
            return files
        except subprocess.CalledProcessError:
            return {}

    @staticmethod
    def is_file_tracked(filepath: str) -> bool:
        """检查文件是否被 Git 跟踪"""
        try:
            subprocess.run(
                ['git', 'ls-files', '--error-unmatch', filepath],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def file_exists(filepath: str) -> bool:
        """检查文件是否存在"""
        return os.path.exists(filepath)


# ============================================================================
# 规则检查器
# ============================================================================
class RuleChecker:
    """规则检查器"""

    def __init__(self, config: dict[str, Any], repo_root: str):
        self.config = config
        self.repo_root = repo_root
        self.git = GitHelper()
        self.staged_files: list[str] = []
        self.staged_files_set: set[str] = set()

    def check(self) -> CheckResult:
        """执行所有检查"""
        result = CheckResult(passed=True)

        if not self._is_enabled():
            return result

        self.staged_files = self.git.get_staged_files()
        self.staged_files_set = set(self.staged_files)

        if not self.staged_files:
            return result

        # 获取排除模式
        exclude_patterns = self.config.get('config', {}).get('exclude_patterns', [])

        # 过滤排除的文件
        filtered_files = []
        for filepath in self.staged_files:
            excluded = False
            for pattern in exclude_patterns:
                if self._match_pattern(filepath, pattern):
                    excluded = True
                    break
            if not excluded:
                filtered_files.append(filepath)

        if not filtered_files:
            return result

        # 执行规则检查
        for rule in (self.config.get('rules') or []):
            self._collect_matches(result, self._check_rule(rule, filtered_files))

        # 执行特殊规则检查
        for rule in (self.config.get('special_rules') or []):
            self._collect_matches(result, self._check_special_rule(rule, filtered_files))

        # 执行文档关联检查
        for rule in (self.config.get('documentation_rules') or []):
            self._collect_matches(result, self._check_rule(rule, filtered_files))

        # 执行已知问题检测
        for issue in (self.config.get('known_issues') or []):
            self._collect_matches(result, self._check_known_issue(issue, filtered_files))

        return result

    def _collect_matches(self, result: CheckResult, matches: list[RuleMatch]):
        """将匹配结果收集到结果中"""
        for match in matches:
            if match.severity == 'block':
                result.blocks.append(match)
                result.passed = False
            else:
                result.warnings.append(match)

    def _is_enabled(self) -> bool:
        """检查是否启用 hook"""
        env_enabled = os.environ.get('GIT_HOOKS_ENABLED')
        if env_enabled is not None:
            return env_enabled.lower() in ('true', '1', 'yes')

        return self.config.get('config', {}).get('enabled', True)

    def _is_rule_enabled(self, rule: dict[str, Any]) -> bool:
        """检查单条规则是否启用 (支持 per-rule disable)"""
        return rule.get('enabled', True)

    def _check_rule(self, rule: dict[str, Any], staged_files: list[str]) -> list[RuleMatch]:
        """检查单个规则"""
        if not self._is_rule_enabled(rule):
            return []

        matches = []
        match_pattern = rule.get('match', '')
        related_files = rule.get('related') or []
        severity = rule.get('severity', self.config.get('config', {}).get('default_severity', 'warn'))
        message = rule.get('message', '')
        description = rule.get('description', '')

        for staged_file in staged_files:
            if self._match_pattern(staged_file, match_pattern):
                related = []
                missing = []

                for related_pattern in related_files:
                    expanded = self._expand_pattern(related_pattern, staged_file)
                    for expanded_path in expanded:
                        related_info = RelatedFile(
                            path=expanded_path,
                            exists=self.git.file_exists(expanded_path),
                            is_staged=expanded_path in self.staged_files_set
                        )
                        related.append(related_info)

                        if not related_info.exists:
                            missing.append(expanded_path)

                has_unstaged = any(not r.is_staged for r in related)
                if related and has_unstaged:
                    matches.append(RuleMatch(
                        rule_name=rule.get('name', ''),
                        description=description,
                        severity=severity,
                        message=message,
                        source_file=staged_file,
                        related_files=related,
                        missing_files=missing
                    ))

        return matches

    def _check_special_rule(self, rule: dict[str, Any], staged_files: list[str]) -> list[RuleMatch]:
        """检查特殊规则"""
        if not self._is_rule_enabled(rule):
            return []

        matches = []
        check_type = rule.get('check', '')
        match_pattern = rule.get('match', '')
        severity = rule.get('severity', 'warn')
        message = rule.get('message', '')
        description = rule.get('description', '')

        if check_type == 'export_exists':
            for staged_file in staged_files:
                if self._match_pattern(staged_file, match_pattern):
                    issues = self._check_exports(staged_file)
                    if issues:
                        matches.append(RuleMatch(
                            rule_name=rule.get('name', ''),
                            description=description,
                            severity=severity,
                            message=f"{message}\n" + "\n".join(issues),
                            source_file=staged_file
                        ))

        elif check_type == 'duplicate_definitions':
            if isinstance(match_pattern, list):
                staged_matches = [f for f in staged_files if any(self._match_pattern(f, p) for p in match_pattern)]
                if len(staged_matches) > 1:
                    duplicates = self._check_duplicates(staged_matches)
                    if duplicates:
                        matches.append(RuleMatch(
                            rule_name=rule.get('name', ''),
                            description=description,
                            severity=severity,
                            message=f"{message}\n" + "\n".join(duplicates),
                            source_file=', '.join(staged_matches)
                        ))

        elif check_type == 'legacy_wrapper_sync':
            patterns = match_pattern if isinstance(match_pattern, list) else [match_pattern]
            for staged_file in staged_files:
                for pattern in patterns:
                    if self._match_pattern(staged_file, pattern):
                        issues = self._check_legacy_wrapper(staged_file)
                        if issues:
                            matches.append(RuleMatch(
                                rule_name=rule.get('name', ''),
                                description=description,
                                severity=severity,
                                message=f"{message}\n" + "\n".join(issues),
                                source_file=staged_file
                            ))
                        break  # 一个文件只需匹配一次

        elif check_type in ('test_file_association', 'test_file_reverse'):
            # 测试文件关联检查 (支持 exclude 和 related_pattern)
            exclude = rule.get('exclude', '')
            related_pattern_tpl = rule.get('related_pattern', '')
            for staged_file in staged_files:
                if not self._match_pattern(staged_file, match_pattern):
                    continue
                if exclude and self._match_pattern(staged_file, exclude):
                    continue

                expanded = self._expand_pattern(related_pattern_tpl, staged_file)
                if not expanded:
                    continue

                related = []
                missing = []
                for ep in expanded:
                    ri = RelatedFile(
                        path=ep,
                        exists=self.git.file_exists(ep),
                        is_staged=ep in self.staged_files_set
                    )
                    related.append(ri)
                    if not ri.exists:
                        missing.append(ep)

                has_unstaged = any(not r.is_staged for r in related)
                if related and has_unstaged:
                    matches.append(RuleMatch(
                        rule_name=rule.get('name', ''),
                        description=description,
                        severity=severity,
                        message=message,
                        source_file=staged_file,
                        related_files=related,
                        missing_files=missing
                    ))

        return matches

    def _check_known_issue(self, issue: dict[str, Any], staged_files: list[str]) -> list[RuleMatch]:
        """检查已知问题"""
        matches = []
        issue_files = issue.get('files') or []
        pattern = issue.get('pattern', '')
        severity = issue.get('severity', 'warn')
        message = issue.get('message', '')
        description = issue.get('description', '')

        staged_matches = [f for f in staged_files if f in issue_files]

        for filepath in staged_matches:
            full_path = os.path.join(self.repo_root, filepath)
            if not os.path.exists(full_path):
                continue
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            if pattern in content:
                matches.append(RuleMatch(
                    rule_name=issue.get('name', ''),
                    description=description,
                    severity=severity,
                    message=message,
                    source_file=filepath
                ))

        return matches

    def _match_pattern(self, filepath: str, pattern: str | list[str]) -> bool:
        """匹配文件路径模式 (支持 **, *, ?, 正确处理 Windows 路径)"""
        if not pattern:
            return False

        if isinstance(pattern, list):
            return any(self._match_pattern(filepath, p) for p in pattern)

        # 统一为正斜杠
        fp = normalize_path(filepath)
        pat = normalize_path(pattern)

        # ** 匹配零个或多个路径段，需要处理边界斜杠
        # 用占位符(不含*)保护，避免被后续 * 替换破坏
        PH = '\x00DS\x00'
        # 匹配 /**/ 或 /** 或 **/ 或 ** (独立)
        pat = re.sub(r'/\*\*/|/\*\*|\*\*/|\*\*', PH, pat)
        pat = pat.replace('.', r'\.')
        pat = pat.replace('?', '.')
        pat = pat.replace('*', '[^/]*')
        # 恢复占位符：根据上下文决定正则
        # /PH/ → 匹配一个或多个路径段 (含前导和后缀斜杠)
        pat = pat.replace(f'/{PH}/', '(?:/.+)?/')
        # /PH  → 字符串末尾的 **/
        pat = pat.replace(f'/{PH}', '(?:/.*)?')
        # PH/ → 字符串开头 **/
        pat = pat.replace(f'{PH}/', '(?:.*/)?')
        # PH  → 独立的 **
        pat = pat.replace(PH, '.*')

        return bool(re.fullmatch(pat, fp))

    def _expand_pattern(self, pattern: str, source_file: str) -> list[str]:
        """展开模式，替换变量并展开通配符"""
        if not pattern:
            return []

        expanded = pattern

        # $MODULE: 最长匹配的模块路径 (param_id_gui/.../子目录)
        module_match = re.match(r'((?:[^/]+/)*[^/]+)', source_file)
        if module_match:
            expanded = expanded.replace('$MODULE', module_match.group(1))

        # $FILE: 匹配的文件名
        filename = os.path.basename(source_file)
        expanded = expanded.replace('$FILE', filename)

        # $BASENAME: 不带扩展名的文件名
        basename = os.path.splitext(filename)[0]
        expanded = expanded.replace('$BASENAME', basename)

        # 安全检查: 防止路径遍历 (检测 .. 组件)
        if '..' in expanded.split('/') or '..' in expanded.split('\\'):
            return []

        # 处理通配符
        if '*' in expanded or '?' in expanded:
            full_pattern = os.path.join(self.repo_root, expanded)
            matches = glob.glob(full_pattern, recursive=True)
            # 安全检查: 确保所有结果都在仓库根目录内
            repo_root_norm = normalize_path(self.repo_root)
            result = []
            for m in matches:
                rel_path = normalize_path(os.path.relpath(m, self.repo_root))
                # 检查相对路径不以 .. 开头 (防止路径遍历)
                if not rel_path.startswith('..'):
                    result.append(rel_path)
            return result

        return [expanded]

    def _check_exports(self, filepath: str) -> list[str]:
        """检查 __init__.py 导出的类/函数是否存在"""
        issues = []
        full_path = os.path.join(self.repo_root, filepath)

        if not os.path.exists(full_path):
            return issues

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            return issues

        # 提取导出的名称 (单行和多行)
        imports = re.findall(r'from\s+\.\w+\s+import\s+(\w+)(?:\s+as\s+\w+)?', content)
        imports.extend(re.findall(r'from\s+\.\w+\s+import\s+\(([^)]+)\)', content))

        module_dir = os.path.dirname(full_path)

        for name in imports:
            if ',' in name:
                names = [n.strip() for n in name.split(',')]
            else:
                names = [name]

            for n in names:
                if not n:
                    continue

                found = False
                try:
                    pyfiles = os.listdir(module_dir)
                except OSError:
                    continue

                for pyfile in pyfiles:
                    if pyfile == '__init__.py' or not pyfile.endswith('.py'):
                        continue

                    pyfile_path = os.path.join(module_dir, pyfile)
                    try:
                        with open(pyfile_path, 'r', encoding='utf-8') as f:
                            pycontent = f.read()
                    except (OSError, UnicodeDecodeError):
                        continue

                    if re.search(rf'class\s+{re.escape(n)}\b', pycontent) or re.search(rf'def\s+{re.escape(n)}\b', pycontent):
                        found = True
                        break

                if not found:
                    issues.append(f"  - {n}: 在模块中未找到定义")

        return issues

    def _check_duplicates(self, files: list[str]) -> list[str]:
        """检查重复定义"""
        issues = []
        class_defs: dict[str, list[str]] = {}

        for filepath in files:
            full_path = os.path.join(self.repo_root, filepath)
            if not os.path.exists(full_path):
                continue
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            classes = re.findall(r'class\s+(\w+)', content)
            for cls in classes:
                if cls not in class_defs:
                    class_defs[cls] = []
                class_defs[cls].append(filepath)

        for cls, defs in class_defs.items():
            if len(defs) > 1:
                issues.append(f"  - {cls}: 在 {', '.join(defs)} 中重复定义")

        return issues

    def _check_legacy_wrapper(self, filepath: str) -> list[str]:
        """检查 legacy wrapper 同步"""
        issues = []
        full_path = os.path.join(self.repo_root, filepath)

        if not os.path.exists(full_path):
            return issues

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            return issues

        if 'Legacy' in content or 'legacy' in content:
            legacy_classes = re.findall(r'class\s+(\w*Legacy\w*)', content)
            for legacy_cls in legacy_classes:
                main_cls = legacy_cls.replace('Legacy', '')
                if f'class {main_cls}' not in content:
                    issues.append(f"  - Legacy wrapper {legacy_cls} 对应的主类 {main_cls} 未找到")

        return issues


# ============================================================================
# 结果格式化
# ============================================================================
class ResultFormatter:
    """结果格式化器 (使用实例颜色，不污染全局)"""

    def __init__(self, colors: Colors):
        self.c = colors

    def format(self, result: CheckResult, show_passed: bool = False) -> str:
        """格式化检查结果"""
        lines = []

        lines.append(f"\n{self.c.BOLD}{'='*60}{self.c.RESET}")
        lines.append(f"{self.c.BOLD}Git Pre-commit Hook - Related File Check{self.c.RESET}")
        lines.append(f"{'='*60}\n")

        if result.blocks:
            lines.append(f"{self.c.RED}{self.c.BOLD}[BLOCK] The following issues must be fixed before committing:{self.c.RESET}\n")
            for block in result.blocks:
                self._format_match(lines, block, self.c.RED)

        if result.warnings:
            lines.append(f"{self.c.YELLOW}{self.c.BOLD}[WARN] The following files may need synchronized updates:{self.c.RESET}\n")
            for warning in result.warnings:
                self._format_match(lines, warning, self.c.YELLOW)

        if show_passed and not result.blocks and not result.warnings:
            lines.append(f"{self.c.GREEN}{self.c.BOLD}[PASS] All checks passed{self.c.RESET}\n")

        if result.errors:
            lines.append(f"{self.c.RED}{self.c.BOLD}[ERROR] Errors during check:{self.c.RESET}\n")
            for error in result.errors:
                lines.append(f"  {self.c.RED}* {error}{self.c.RESET}")

        lines.append(f"\n{'='*60}")
        if result.blocks:
            lines.append(f"{self.c.RED}{self.c.BOLD}Result: {len(result.blocks)} blocking issues found, please fix before committing{self.c.RESET}")
        elif result.warnings:
            lines.append(f"{self.c.YELLOW}{self.c.BOLD}Result: {len(result.warnings)} warnings found, commit allowed{self.c.RESET}")
        else:
            lines.append(f"{self.c.GREEN}{self.c.BOLD}Result: All checks passed{self.c.RESET}")
        lines.append(f"{'='*60}\n")

        return '\n'.join(lines)

    def _format_match(self, lines: list[str], match: RuleMatch, color: str):
        """格式化单个匹配结果"""
        lines.append(f"{color}{self.c.BOLD}> {match.rule_name}{self.c.RESET}")
        if match.description:
            lines.append(f"  {color}{match.description}{self.c.RESET}")
        lines.append(f"  {color}Source: {match.source_file}{self.c.RESET}")

        if match.message:
            lines.append(f"  {color}{match.message}{self.c.RESET}")

        if match.related_files:
            lines.append(f"  {color}Related files:{self.c.RESET}")
            for related in match.related_files:
                status = self._get_file_status(related)
                lines.append(f"    {color}- {related.path} {status}{self.c.RESET}")

        if match.missing_files:
            lines.append(f"  {self.c.RED}Missing files:{self.c.RESET}")
            for missing in match.missing_files:
                lines.append(f"    {self.c.RED}X {missing}{self.c.RESET}")

        lines.append("")

    def _get_file_status(self, related: RelatedFile) -> str:
        """获取文件状态标记"""
        if not related.exists:
            return f"{self.c.RED}[NOT FOUND]{self.c.RESET}"
        elif related.is_staged:
            return f"{self.c.GREEN}[STAGED]{self.c.RESET}"
        else:
            return f"{self.c.YELLOW}[NOT STAGED]{self.c.RESET}"


# ============================================================================
# JSON 输出格式化
# ============================================================================
class JsonFormatter:
    """JSON 输出格式化器"""

    @staticmethod
    def format(result: CheckResult) -> str:
        """格式化为 JSON"""

        def _rule_match_to_dict(m: RuleMatch) -> dict:
            return {
                'rule': m.rule_name,
                'description': m.description,
                'severity': m.severity,
                'message': m.message,
                'source': m.source_file,
                'related': [
                    {'path': r.path, 'exists': r.exists, 'staged': r.is_staged}
                    for r in m.related_files
                ],
                'missing': m.missing_files
            }

        output = {
            'passed': result.passed,
            'blocks': [_rule_match_to_dict(b) for b in result.blocks],
            'warnings': [_rule_match_to_dict(w) for w in result.warnings],
            'errors': result.errors
        }

        return json.dumps(output, indent=2, ensure_ascii=False)


# ============================================================================
# 主函数
# ============================================================================
def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Git Pre-commit Hook - 关联文件检测')
    parser.add_argument('--config', '-c', default='.git-hooks-config.yml',
                        help='配置文件路径 (默认: .git-hooks-config.yml)')
    parser.add_argument('--json', '-j', action='store_true',
                        help='JSON 输出格式')
    parser.add_argument('--show-passed', '-p', action='store_true',
                        help='显示通过的检查')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='详细输出')
    parser.add_argument('--no-color', action='store_true',
                        help='禁用颜色输出')

    args = parser.parse_args()

    # 获取仓库根目录
    try:
        repo_root = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        print("错误: 无法获取 Git 仓库根目录", file=sys.stderr)
        sys.exit(1)

    # 构建配置文件路径
    config_path = os.path.join(repo_root, args.config)

    # 加载配置
    try:
        loader = ConfigLoader(config_path)
        config = loader.load()
    except Exception as e:
        print(f"错误: 无法加载配置文件: {e}", file=sys.stderr)
        sys.exit(1)

    # 执行检查
    checker = RuleChecker(config, repo_root)
    result = checker.check()

    # 输出结果
    if args.json:
        print(JsonFormatter.format(result))
    else:
        colors = Colors(enabled=not args.no_color)
        formatter = ResultFormatter(colors)
        show_passed = args.show_passed or config.get('config', {}).get('show_passed', False)
        print(formatter.format(result, show_passed))

    # 返回退出码
    if result.blocks:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
