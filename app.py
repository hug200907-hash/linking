#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           CODE SELF-LEARNING TOOL v1.0                       ║
║  Tự học pattern từ source code → Lưu knowledge → Generate   ║
║  Author: Kyriel for Boss                                     ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import re
import json
import ast
import time
import hashlib
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import difflib
import textwrap
import subprocess
import sys

# ============================================================
# CONFIGURATION
# ============================================================
CONFIG = {
    "knowledge_file": "knowledge.json",
    "examples_dir": "examples",
    "output_dir": "generated",
    "max_pattern_history": 50,
    "min_confidence": 0.3,
    "supported_extensions": [".cpp", ".c", ".h", ".hpp", ".py", ".cs", ".java", ".js", ".ts"],
}

# ============================================================
# COLOR OUTPUT
# ============================================================
class Color:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

def c(text: str, color: str) -> str:
    return f"{color}{text}{Color.RESET}"

# ============================================================
# PARSER BASE - Phân tích source code
# ============================================================
class CodeParser:
    """Base parser - trích xuất pattern từ source code"""
    
    def __init__(self):
        self.patterns = {
            "functions": [],
            "variables": [],
            "types": [],
            "naming_style": {},
            "hooks": [],
            "offsets": [],
            "conditions": [],
            "loops": [],
            "function_calls": [],
            "math_ops": [],
            "pointer_ops": [],
            "null_checks": [],
            "includes": [],
            "macros": [],
            "structs": [],
            "classes": [],
            "comments": [],
            "indentation": 4,
            "brace_style": "same_line",
            "file_structure": [],
        }
        self.raw_code = ""
        self.language = "unknown"
    
    def parse(self, code: str, filename: str = "") -> Dict:
        """Parse code và trích xuất tất cả patterns"""
        self.raw_code = code
        self.language = self._detect_language(filename)
        
        if self.language in ["cpp", "c", "h"]:
            self._parse_cpp(code)
        elif self.language == "python":
            self._parse_python(code)
        else:
            self._parse_generic(code)
        
        return self.patterns
    
    def _detect_language(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        mapping = {
            ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp",
            ".c": "c",
            ".h": "h", ".hpp": "h",
            ".py": "python",
            ".cs": "csharp",
            ".java": "java",
            ".js": "javascript", ".ts": "typescript",
        }
        return mapping.get(ext, "unknown")
    
    def _parse_cpp(self, code: str):
        """Parse C/C++ code"""
        lines = code.split('\n')
        
        # Extract functions
        func_pattern = r'(?:static\s+|inline\s+|virtual\s+)*(?:void|int|float|double|char|unsigned\s+int|long|bool|auto|\w+(?:\s*\*|\s*&)*\w+)\s+(\w+)\s*\(([^)]*)\)\s*(?:const)?\s*(?:\{|\:)'
        for match in re.finditer(func_pattern, code):
            return_type = match.group(0).split(match.group(1))[0].strip()
            func_name = match.group(1)
            params = match.group(2)
            self.patterns["functions"].append({
                "name": func_name,
                "return_type": return_type.strip(),
                "params": params.strip(),
                "full_signature": match.group(0).strip(),
                "language": "cpp"
            })
        
        # Extract variable declarations
        var_patterns = [
            r'(?:const\s+)?(\w+(?:\s*\*)*)\s+(\w+)(?:\s*=\s*([^;]+))?\s*;',  # type name = value;
            r'(\w+(?:\s*\*)*)\s+(\w+)\s*[;\[\]]',  # type name; or type name[]
        ]
        for pat in var_patterns:
            for match in re.finditer(pat, code):
                var_type = match.group(1).strip()
                var_name = match.group(2).strip()
                if not any(kw in var_type for kw in ['if', 'while', 'for', 'return', 'switch', 'case']):
                    self.patterns["variables"].append({
                        "type": var_type,
                        "name": var_name,
                        "language": "cpp"
                    })
        
        # Extract types (structs, classes, enums)
        struct_pattern = r'(?:struct|class)\s+(\w+)(?:\s*:\s*(public|private|protected)\s+(\w+))?'
        for match in re.finditer(struct_pattern, code):
            self.patterns["structs"].append(match.group(1))
            self.patterns["types"].append(match.group(1))
        
        enum_pattern = r'enum(?:\s+class)?\s*(?:\w+)?\s*\{([^}]+)\}'
        for match in re.finditer(enum_pattern, code):
            self.patterns["types"].append(f"enum_{hash(match.group(1)) % 10000}")
        
        # Extract hooks / function pointers / offsets
        hook_patterns = [
            r'(?:DWORD|uintptr_t|uint32_t|unsigned long)\s+(\w*)\s*=\s*(?:0x[0-9A-Fa-f]+|\d+)',  # offset addresses
            r'(\w+)\s*=\s*\(\s*(\w+\s*\*)\s*\)\s*(0x[0-9A-Fa-f]+)',  # casts to addresses
            r'(?:Hook|Detour|Patch|Trampoline)\w*\(\s*([^)]+)\s*\)',  # hook functions
        ]
        for pat in hook_patterns:
            for match in re.finditer(pat, code):
                self.patterns["hooks"].append(match.group(0))
                offset_match = re.search(r'0x([0-9A-Fa-f]+)', match.group(0))
                if offset_match:
                    self.patterns["offsets"].append(f"0x{offset_match.group(1)}")
        
        # Extract conditions
        cond_pattern = r'if\s*\(([^)]+)\)'
        for match in re.finditer(cond_pattern, code):
            condition = match.group(1).strip()
            if len(condition) < 200:  # avoid huge conditions
                self.patterns["conditions"].append(condition)
        
        # Extract loops
        loop_patterns = [
            (r'for\s*\(([^)]+)\)', "for"),
            (r'while\s*\(([^)]+)\)', "while"),
            (r'do\s*\{([^}]+)\}\s*while\s*\(([^)]+)\)', "do_while"),
        ]
        for pat, loop_type in loop_patterns:
            for match in re.finditer(pat, code, re.DOTALL):
                self.patterns["loops"].append({
                    "type": loop_type,
                    "pattern": match.group(0)[:150]
                })
        
        # Extract function calls
        call_pattern = r'(\w+)\s*\(([^)]*)\)'
        reserved = {'if', 'while', 'for', 'switch', 'return', 'new', 'delete'}
        for match in re.finditer(call_pattern, code):
            func_name = match.group(1)
            if func_name not in reserved and not func_name[0].isdigit():
                args = match.group(2)[:100]
                self.patterns["function_calls"].append({
                    "name": func_name,
                    "args_preview": args
                })
        
        # Extract math/vector operations
        math_patterns = [
            r'(\w+)\.(x|y|z|w)\s*=',  # vector component assignment
            r'(?:D3DX|XM|vec|Vector)[^\n]*',  # math library calls
            r'[\+\-\*\/]=?',  # arithmetic operators in context
        ]
        for line in lines:
            for pat in math_patterns:
                if re.search(pat, line) and len(line) < 200:
                    self.patterns["math_ops"].append(line.strip())
        
        # Extract pointer operations
        ptr_patterns = [
            r'\*\s*\w+\s*=',  # dereference assignment
            r'\w+\s*->\s*\w+',  # pointer member access
            r'\(\s*\w+\s*\*\s*\)',  # pointer cast
            r'reinterpret_cast<[^>]+>',  # cpp cast
            r'static_cast<[^>]+>',
        ]
        for pat in ptr_patterns:
            for match in re.finditer(pat, code):
                self.patterns["pointer_ops"].append(match.group(0))
        
        # Extract NULL/nullptr checks
        null_patterns = [
            r'if\s*\(\s*\w+\s*==\s*(?:NULL|nullptr|nullptr|0)\s*\)',
            r'if\s*\(\s*!\s*\w+\s*\)',
            r'if\s*\(\s*(?:NULL|nullptr|nullptr|0)\s*!=\s*\w+\s*\)',
            r'assert\s*\([^)]+\)',
        ]
        for pat in null_patterns:
            for match in re.finditer(pat, code):
                self.patterns["null_checks"].append(match.group(0))
        
        # Extract includes
        include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
        for match in re.finditer(include_pattern, code):
            self.patterns["includes"].append(match.group(1))
        
        # Extract macros/defines
        define_pattern = r'#define\s+(\w+)(?:\(([^^)]+)\))?\s+([^\n]+)'
        for match in re.finditer(define_pattern, code):
            self.patterns["macros"].append({
                "name": match.group(1),
                "params": match.group(2) or "",
                "body": match.group(3).strip()
            })
        
        # Detect naming style
        self._analyze_naming_style(code)
        
        # Detect brace style and indentation
        self._detect_code_style(lines)
    
    def _parse_python(self, code: str):
        """Parse Python code using AST"""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self.patterns["functions"].append({
                        "name": node.name,
                        "return_type": "infer",
                        "params": ", ".join([arg.arg for arg in node.args.args]),
                        "full_signature": f"def {node.name}(...)",
                        "language": "python"
                    })
                
                elif isinstance(node, ast.ClassDef):
                    self.patterns["classes"].append(node.name)
                    self.patterns["types"].append(node.name)
                
                elif isinstance(node, ast.If):
                    try:
                        cond = ast.unparse(node.test) if hasattr(ast, 'unparse') else "?"
                        self.patterns["conditions"].append(cond)
                    except:
                        pass
                
                elif isinstance(node, (ast.For, ast.While)):
                    loop_type = "for" if isinstance(node, ast.For) else "while"
                    self.patterns["loops"].append({"type": loop_type, "pattern": f"{loop_type} ..."})
                
                elif isinstance(node, ast.Call):
                    try:
                        func_name = ast.unparse(node.func) if hasattr(ast, 'unparse') else "?"
                        self.patterns["function_calls"].append({"name": func_name, "args_preview": "..."})
                    except:
                        pass
            
            self._analyze_naming_style(code)
            
        except SyntaxError as e:
            print(c(f"  ⚠ Python syntax error: {e}", Color.YELLOW))
    
    def _parse_generic(self, code: str):
        """Generic parser for unsupported languages"""
        lines = code.split('\n')
        
        # Basic function detection
        func_pattern = r'(?:function|def|func)\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(func_pattern, code):
            self.patterns["functions"].append({
                "name": match.group(1),
                "params": match.group(2),
                "language": "generic"
            })
        
        # Basic variable detection
        var_pattern = r'(?:var|let|const)\s+(\w+)'
        for match in re.finditer(var_pattern, code):
            self.patterns["variables"].append({"name": match.group(1), "type": "inferred"})
        
        self._analyze_naming_style(code)
    
    def _analyze_naming_style(self, code: str):
        """Phân tích naming convention được sử dụng"""
        # Check function names
        func_names = [f["name"] for f in self.patterns["functions"]]
        var_names = [v.get("name", "") for v in self.patterns["variables"]]
        all_names = func_names + var_names
        
        camel_count = sum(1 for n in all_names if re.match(r'^[a-z][a-zA-Z0-9]*$', n) and any(c.isupper() for c in n))
        pascal_count = sum(1 for n in all_names if re.match(r'^[A-Z][a-zA-Z0-9]*$', n))
        snake_count = sum(1 for n in all_names if re.match(r'^[a-z][a-z0-9_]*$', n) and '_' in n)
        upper_snake_count = sum(1 for n in all_names if re.match(r'^[A-Z][A-Z0-9_]*$', n))
        hungarian_count = sum(1 for n in all_names if re.match(r'^[a-z]{1,3}[A-Z]', n))
        
        total = max(len(all_names), 1)
        self.patterns["naming_style"] = {
            "camelCase": camel_count / total,
            "PascalCase": pascal_count / total,
            "snake_case": snake_count / total,
            "UPPER_SNAKE": upper_snake_count / total,
            "hungarian": hungarian_count / total,
            "dominant": max([
                ("camelCase", camel_count/total),
                ("PascalCase", pascal_count/total),
                ("snake_case", snake_count/total),
                ("UPPER_SNAKE", upper_snake_count/total),
                ("hungarian", hungarian/total)
            ], key=lambda x: x[1])[0] if total > 0 else "unknown"
        }
    
    def _detect_code_style(self, lines: List[str]):
        """Detect indentation and brace style"""
        # Indentation detection
        indent_sizes = []
        for line in lines:
            if line.startswith(' ') and not line.startswith('    ' * 4):
                spaces = len(line) - len(line.lstrip())
                if spaces > 0:
                    indent_sizes.append(spaces)
        
        if indent_sizes:
            counter = Counter(indent_sizes)
            self.patterns["indentation"] = counter.most_common(1)[0][0]
        
        # Brace style detection
        same_line = 0
        next_line = 0
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped.endswith(')') or stripped.endswith('{'):
                if stripped.endswith('{'):
                    same_line += 1
                elif i + 1 < len(lines) and lines[i + 1].strip().startswith('{'):
                    next_line += 1
        
        if same_line > next_line:
            self.patterns["brace_style"] = "same_line"
        elif next_line > 0:
            self.patterns["brace_style"] = "next_line"


# ============================================================
# KNOWLEDGE ENGINE - Quản lý kiến thức
# ============================================================
class KnowledgeEngine:
    """Lưu trữ, cập nhật và truy vấn knowledge"""
    
    def __init__(self, knowledge_path: str):
        self.knowledge_path = knowledge_path
        self.knowledge = self._load_or_create()
    
    def _load_or_create(self) -> Dict:
        """Load existing knowledge hoặc tạo mới"""
        if os.path.exists(self.knowledge_path):
            try:
                with open(self.knowledge_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(c(f"  ✓ Loaded existing knowledge ({len(data.get('sources', []))} sources learned)", Color.GREEN))
                return data
            except Exception as e:
                print(c(f"  ⚠ Corrupted knowledge file, creating new: {e}", Color.YELLOW))
        
        return self._empty_knowledge()
    
    def _empty_knowledge(self) -> Dict:
        """Create empty knowledge structure"""
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "sources_learned": 0,
            "sources": [],
            "patterns": {
                "function_signatures": [],
                "function_templates": [],
                "variable_patterns": [],
                "type_definitions": [],
                "naming_convention": {"dominant": "unknown", "scores": {}},
                "hook_patterns": [],
                "offset_patterns": [],
                "condition_patterns": [],
                "loop_patterns": [],
                "common_calls": [],
                "math_operations": [],
                "pointer_patterns": [],
                "null_check_patterns": [],
                "includes_used": [],
                "macros_defined": [],
                "structs_classes": [],
                "code_style": {"indentation": 4, "brace_style": "same_line"},
                "file_structure_template": [],
            },
            "statistics": {
                "total_functions": 0,
                "total_variables": 0,
                "total_patterns": 0,
                "confidence_scores": {}
            },
            "learning_history": []
        }
    
    def learn_from_parser(self, parser: CodeParser, source_file: str, source_code: str):
        """Học từ kết quả parser và cập nhật knowledge"""
        patterns = parser.patterns
        source_hash = hashlib.md5(source_code.encode()).hexdigest()[:12]
        
        # Check if already learned this file
        if any(s.get("hash") == source_hash for s in self.knowledge["sources"]):
            print(c(f"  ℹ Source already learned (hash: {source_hash})", Color.CYAN))
            return False
        
        # === UPDATE PATTERNS ===
        
        # Functions - extract templates
        for func in patterns["functions"]:
            template = self._create_function_template(func)
            if template:
                self.knowledge["patterns"]["function_templates"].append(template)
                self.knowledge["patterns"]["function_signatures"].append(func["full_signature"])
        
        # Variables
        for var in patterns["variables"]:
            self.knowledge["patterns"]["variable_patterns"].append(var)
        
        # Types
        for t in set(patterns["types"] + patterns["structs"] + patterns["classes"]):
            if t not in self.knowledge["patterns"]["type_definitions"]:
                self.knowledge["patterns"]["type_definitions"].append(t)
        
        # Naming convention - merge scores
        ns = patterns.get("naming_style", {})
        for style, score in ns.items():
            if style != "dominant":
                current = self.knowledge["patterns"]["naming_convention"]["scores"].get(style, 0)
                self.knowledge["patterns"]["naming_convention"]["scores"][style] = current + score
        
        # Update dominant
        scores = self.knowledge["patterns"]["naming_convention"]["scores"]
        if scores:
            self.knowledge["patterns"]["naming_convention"]["dominant"] = max(scores, key=scores.get)
        
        # Hooks & Offsets
        for h in set(patterns["hooks"]):
            self.knowledge["patterns"]["hook_patterns"].append(h)
        for o in set(patterns["offsets"]):
            self.knowledge["patterns"]["offset_patterns"].append(o)
        
        # Conditions - normalize and count
        for cond in patterns["conditions"]:
            normalized = self._normalize_condition(cond)
            self.knowledge["patterns"]["condition_patterns"].append(normalized)
        
        # Loops
        for loop in patterns["loops"]:
            self.knowledge["patterns"]["loop_patterns"].append(loop)
        
        # Function calls - track frequency
        for call in patterns["function_calls"]:
            self.knowledge["patterns"]["common_calls"].append(call["name"])
        
        # Math operations
        for op in set(patterns["math_ops"][:20]):
            self.knowledge["patterns"]["math_operations"].append(op)
        
        # Pointer operations
        for ptr in set(patterns["pointer_ops"]):
            self.knowledge["patterns"]["pointer_patterns"].append(ptr)
        
        # Null checks
        for nc in set(patterns["null_checks"]):
            self.knowledge["patterns"]["null_check_patterns"].append(nc)
        
        # Includes
        for inc in set(patterns["includes"]):
            if inc not in self.knowledge["patterns"]["includes_used"]:
                self.knowledge["patterns"]["includes_used"].append(inc)
        
        # Macros
        for macro in patterns["macros"]:
            existing_names = [m["name"] for m in self.knowledge["patterns"]["macros_defined"]]
            if macro["name"] not in existing_names:
                self.knowledge["patterns"]["macros_defined"].append(macro)
        
        # Structs/Classes
        for sc in set(patterns["structs"] + patterns["classes"]):
            if sc not in self.knowledge["patterns"]["structs_classes"]:
                self.knowledge["patterns"]["structs_classes"].append(sc)
        
        # Code style
        self.knowledge["patterns"]["code_style"]["indentation"] = patterns.get("indentation", 4)
        self.knowledge["patterns"]["code_style"]["brace_style"] = patterns.get("brace_style", "same_line")
        
        # Record source
        self.knowledge["sources"].append({
            "file": source_file,
            "hash": source_hash,
            "learned_at": datetime.now().isoformat(),
            "language": patterns.get("language", "unknown"),
            "functions_found": len(patterns["functions"]),
            "variables_found": len(patterns["variables"])
        })
        
        # Update statistics
        self.knowledge["sources_learned"] += 1
        self.knowledge["last_updated"] = datetime.now().isoformat()
        self.knowledge["statistics"]["total_functions"] = len(self.knowledge["patterns"]["function_templates"])
        self.knowledge["statistics"]["total_variables"] = len(self.knowledge["patterns"]["variable_patterns"])
        self.knowledge["statistics"]["total_patterns"] = self._count_total_patterns()
        
        # Learning history
        self.knowledge["learning_history"].append({
            "action": "learn",
            "source": source_file,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim history if too long
        if len(self.knowledge["learning_history"]) > CONFIG["max_pattern_history"]:
            self.knowledge["learning_history"] = self.knowledge["learning_history"][-CONFIG["max_pattern_history"]:]
        
        self._save()
        return True
    
    def learn_from_diff(self, original_code: str, modified_code: str, description: str = ""):
        """Học từ diff khi user sửa code đã generate"""
        # Compute diff
        differ = difflib.Differ()
        diff = list(differ.compare(original_code.splitlines(), modified_code.splitlines()))
        
        changes = []
        for line in diff:
            if line.startswith('+ ') or line.startswith('- '):
                changes.append(line)
        
        if not changes:
            return
        
        # Extract patterns from the modifications
        mod_parser = CodeParser()
        mod_parser.parse(modified_code, "user_modification")
        
        # Learn new patterns from modification
        for func in mod_parser.patterns["functions"]:
            template = self._create_function_template(func)
            if template:
                template["learned_from"] = "user_correction"
                template["correction_context"] = description
                self.knowledge["patterns"]["function_templates"].append(template)
        
        # Record in history
        self.knowledge["learning_history"].append({
            "action": "correction_learned",
            "description": description,
            "changes_count": len(changes),
            "timestamp": datetime.now().isoformat()
        })
        
        self.knowledge["last_updated"] = datetime.now().isoformat()
        self._save()
        
        print(c(f"  ✓ Learned from your correction ({len(changes)} changes)", Color.GREEN))
    
    def _create_function_template(self, func: Dict) -> Optional[Dict]:
        """Create a reusable template from a function signature"""
        if not func.get("name"):
            return None
        
        # Analyze parameter pattern
        params_str = func.get("params", "")
        params = [p.strip() for p in params_str.split(',') if p.strip()] if params_str else []
        
        param_types = []
        for p in params:
            parts = p.split()
            if len(parts) >= 2:
                param_types.append(parts[0])
            elif len(parts) == 1:
                param_types.append("auto")
        
        return {
            "name_pattern": func["name"],
            "return_type": func.get("return_type", "void"),
            "param_types": param_types,
            "param_count": len(params),
            "language": func.get("language", "unknown"),
            "full_signature": func.get("full_signature", ""),
            "usage_count": 1
        }
    
    def _normalize_condition(self, condition: str) -> str:
        """Normalize condition pattern"""
        # Replace specific values with placeholders
        normalized = re.sub(r'0x[0-9A-Fa-f]+', '0xHEX', condition)
        normalized = re.sub(r'\b\d+\b', 'N', normalized)
        normalized = re.sub(r'"[^"]"*', '"STR"', normalized)
        return normalized
    
    def _count_total_patterns(self) -> int:
        count = 0
        for key in self.knowledge["patterns"]:
            if isinstance(self.knowledge["patterns"][key], list):
                count += len(self.knowledge["patterns"][key])
        return count
    
    def get_similar_functions(self, name: str, top_k: int = 5) -> List[Dict]:
        """Tìm các function tương tự trong knowledge"""
        templates = self.knowledge["patterns"]["function_templates"]
        scored = []
        
        for t in templates:
            score = difflib.SequenceMatcher(None, name.lower(), t["name_pattern"].lower()).ratio()
            scored.append((score, t))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:top_k]]
        
    def get_common_condition_patterns(self, limit: int = 10) -> List[str]:
        """Get most common condition patterns"""
        patterns = self.knowledge["patterns"]["condition_patterns"]
        counter = Counter(patterns)
        return [(p, c) for p, c in counter.most_common(limit)]
    
    def get_common_loop_patterns(self, limit: int = 10) -> List[Dict]:
        """Get most common loop patterns"""
        return self.knowledge["patterns"]["loop_patterns"][:limit]
    
    def get_common_calls(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Get most frequently called functions"""
        calls = self.knowledge["patterns"]["common_calls"]
        counter = Counter(calls)
        return counter.most_common(limit)
    
    def get_includes(self) -> List[str]:
        return self.knowledge["patterns"]["includes_used"]
    
    def get_macros(self) -> List[Dict]:
        return self.knowledge["patterns"]["macros_defined"]
    
    def get_types(self) -> List[str]:
        return self.knowledge["patterns"]["type_definitions"]
    
    def get_naming_style(self) -> str:
        return self.knowledge["patterns"]["naming_convention"]["dominant"]
    
    def get_code_style(self) -> Dict:
        return self.knowledge["patterns"]["code_style"]
    
    def get_null_check_pattern(self) -> str:
        patterns = self.knowledge["patterns"]["null_check_patterns"]
        if patterns:
            counter = Counter(patterns)
            return counter.most_common(1)[0][0]
        return "if (ptr != nullptr)"
    
    def get_pointer_pattern(self) -> List[str]:
        return self.knowledge["patterns"]["pointer_patterns"][:5]
    
    def get_statistics(self) -> Dict:
        return self.knowledge["statistics"]
    
    def get_sources(self) -> List[Dict]:
        return self.knowledge["sources"]
    
    def save(self):
        self._save()
    
    def _save(self):
        """Save knowledge to file"""
        os.makedirs(os.path.dirname(self.knowledge_path) or '.', exist_ok=True)
        with open(self.knowledge_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, indent=2, ensure_ascii=False)


# ============================================================
# CODE GENERATOR - Generate code từ knowledge
# ============================================================
class CodeGenerator:
    """Generate code dựa trên knowledge đã học"""
    
    def __init__(self, knowledge: KnowledgeEngine):
        self.knowledge = knowledge
        self.parser = CodeParser()
    
    def generate_function(self, func_name: str, description: str = "", context: str = "") -> str:
        """Generate một function dựa trên pattern đã học"""
        similar = self.knowledge.get_similar_functions(func_name)
        naming_style = self.knowledge.get_naming_style()
        code_style = self.knowledge.get_code_style()
        indent = " " * code_style.get("indentation", 4)
        
        if not similar:
            return self._generate_generic_function(func_name, description, naming_style, indent)
        
        # Use the most similar function as template
        template = similar[0]
        
        # Build the function based on learned patterns
        lines = []
        
        # Return type from template or infer from name
        return_type = template["return_type"]
        if return_type == "infer":
            return_type = self._infer_return_type(func_name)
        
        # Parameters based on template
        params = self._generate_params(template, func_name, naming_style)
        
        # Function signature
        brace_open = "{" if code_style.get("brace_style") == "same_line" else ""
        lines.append(f"{return_type} {func_name}({params}) {brace_open}")
        
        if code_style.get("brace_style") == "next_line":
            lines.append("{")
        
        # Function body based on learned patterns
        body = self._generate_body(func_name, template, description, context, indent)
        lines.extend(body)
        
        lines.append("}")
        
        return '\n'.join(lines)
    
    def generate_full_code(self, source_code: str, requirements: str = "") -> str:
        """Generate full code dựa trên source mẫu và knowledge"""
        # Parse the source to understand structure
        self.parser.parse(source_code, "input_source")
        
        lines = []
        naming_style = self.knowledge.get_naming_style()
        code_style = self.knowledge.get_code_style()
        
        # Add includes from knowledge
        includes = self.knowledge.get_includes()
        for inc in includes:
            lines.append(f"#include <{inc}>" if not inc.startswith('"') else f'#include {inc}')
        
        # Add macros from knowledge
        macros = self.knowledge.get_macros()
        if macros:
            lines.append("")
            for macro in macros:
                if macro["params"]:
                    lines.append(f'#define {macro["name"]}({macro["params"]}) {macro["body"]}')
                else:
                    lines.append(f'#define {macro["name"]} {macro["body"]}')
        
        lines.append("")
        
        # Generate functions based on source structure and knowledge
        # Apply learned patterns to enhance/modify the source
        enhanced = self._apply_learned_patterns(source_code, requirements)
        lines.append(enhanced)
        
        return '\n'.join(lines)
    
    def _generate_params(self, template: Dict, func_name: str, naming_style: str) -> str:
        """Generate parameters based on template and naming style"""
        param_types = template.get("param_types", [])
        
        if not param_types:
            # Infer from function name
            if "move" in func_name.lower() or "copy" in func_name.lower():
                return "void* src, void* dst, size_t size"
            elif "get" in func_name.lower() or "read" in func_name.lower():
                return "void* handle, void* buffer, size_t size"
            elif "set" in func_name.lower() or "write" in func_name.lower():
                return "void* handle, const void* data, size_t size"
            else:
                return "void* context"
        
        params = []
        type_names = {
            "camelCase": ["srcData", "dstBuffer", "contextPtr", "inputValue", "result"],
            "snake_case": ["src_data", "dst_buffer", "context_ptr", "input_value", "result"],
            "PascalCase": ["SrcData", "DstBuffer", "ContextPtr", "InputValue", "Result"],
            "hungarian": ["pSrc", "pDst", "pCtx", "nVal", "pResult"],
        }
        names = type_names.get(naming_style, type_names["camelCase"])
        
        for i, pt in enumerate(param_types):
            name = names[i] if i < len(names) else f"param{i}"
            params.append(f"{pt} {name}")
        
        return ', '.join(params)
    
    def _infer_return_type(self, func_name: str) -> str:
        name_lower = func_name.lower()
        if any(x in name_lower for x in ['get', 'read', 'find', 'calc', 'compute', 'size', 'count', 'is', 'has']):
            return "int"
        elif any(x in name_lower for x in ['create', 'alloc', 'new', 'open', 'init']):
            return "void*"
        elif any(x in name_lower for x in ['set', 'write', 'free', 'close', 'destroy', 'clear']):
            return "void"
        return "void"
    
    def _generate_body(self, func_name: str, template: Dict, description: str, 
                       context: str, indent: str) -> List[str]:
        """Generate function body based on learned patterns"""
        lines = []
        name_lower = func_name.lower()
        
        # Get common patterns from knowledge
        null_check = self.knowledge.get_null_check_pattern()
        common_conditions = self.knowledge.get_common_condition_patterns(3)
        common_loops = self.knowledge.get_common_loop_patterns(3)
        common_calls = self.knowledge.get_common_calls(5)
        pointer_patterns = self.knowledge.get_pointer_pattern()
        
        # Add null check if function works with pointers
        if any(x in name_lower for x in ['move', 'copy', 'read', 'write', 'set', 'get', 'process']):
            lines.append(f"{indent}// Null check (learned pattern)")
            lines.append(f"{indent}{null_check.replace('ptr', 'contextPtr' if 'contextPtr' in null_check else 'srcData')}")
            lines.append(f"{indent}{{")
            lines.append(f"{indent}{indent}return {'0' if 'int' in template.get('return_type', '') else ''};")
            lines.append(f"{indent}}}")
            lines.append(f"{indent}")
        
        # Add local variables based on learned patterns
        var_patterns = self.knowledge.knowledge["patterns"]["variable_patterns"]
        if var_patterns:
            sample_var = var_patterns[0] if var_patterns else None
            if sample_var:
                var_type = sample_var.get("type", "int")
                lines.append(f"{indent}// Local variables (learned pattern)")
                lines.append(f"{indent}{var_type} result = 0;")
                lines.append(f"{indent}")
        
        # Add logic based on function name and learned patterns
        if any(x in name_lower for x in ['move', 'copy', 'transfer']):
            lines.extend(self._gen_move_logic(indent, common_calls, common_loops))
        elif any(x in name_lower for x in ['init', 'setup', 'create', 'alloc']):
            lines.extend(self._gen_init_logic(indent, common_calls, pointer_patterns))
        elif any(x in name_lower for x in ['hook', 'patch', 'detour']):
            lines.extend(self._gen_hook_logic(indent, common_calls, pointer_patterns))
        else:
            lines.extend(self._gen_generic_logic(indent, common_conditions, common_calls))
        
        # Return statement
        return_type = template.get("return_type", "void")
        if return_type != "void" and return_type != "infer":
            lines.append(f"{indent}")
            lines.append(f"{indent}return result;")
        
        return lines
    
    def _gen_move_logic(self, indent: str, calls: List, loops: List) -> List[str]:
        lines = []
        lines.append(f"{indent}// Move/Copy logic (learned from patterns)")
        if loops:
            loop_template = loops[0] if isinstance(loops[0], dict) else {"type": "for", "pattern": "for"}
            if loop_template.get("type") == "for":
                lines.append(f"{indent}for (size_t i = 0; i < size; i++)")
                lines.append(f"{indent}{{")
                if calls:
                    lines.append(f"{indent}{indent}// Using learned call pattern: {calls[0]}")
                lines.append(f"{indent}{indent}((unsigned char*)dst)[i] = ((unsigned char*)src)[i];")
                lines.append(f"{indent}}}")
        else:
            lines.append(f"{indent}memcpy(dst, src, size);")
        return lines
    
    def _gen_init_logic(self, indent: str, calls: List, ptr_patterns: List) -> List[str]:
        lines = []
        lines.append(f"{indent}// Initialization logic (learned from patterns)")
        if ptr_patterns:
            lines.append(f"{indent}// Pointer pattern observed: {ptr_patterns[0][:50]}")
        lines.append(f"{indent}memset(context, 0, sizeof(*context));")
        if calls:
            for call in calls[:3]:
                if call not in ['memcpy', 'memset', 'malloc']:
                    lines.append(f"{indent}{call}();")
        return lines
    
    def _gen_hook_logic(self, indent: str, calls: List, ptr_patterns: List) -> List[str]:
        lines = []
        lines.append(f"{indent}// Hook/Detour logic (learned from patterns)")
        offset_patterns = self.knowledge.knowledge["patterns"]["offset_patterns"]
        if offset_patterns:
            lines.append(f"{indent}// Offset pattern observed: {offset_patterns[0]}")
        hook_patterns = self.knowledge.knowledge["patterns"]["hook_patterns"]
        if hook_patterns:
            lines.append(f"{indent}// Hook pattern: {hook_patterns[0][:60]}")
        lines.append(f"{indent}void* original = nullptr;")
        lines.append(f"{indent}// TODO: Apply learned hook pattern here")
        return lines
    
    def _gen_generic_logic(self, indent: str, conditions: List, calls: List) -> List[str]:
        lines = []
        lines.append(f"{indent}// Logic based on learned patterns")
        if conditions:
            cond = conditions[0][0] if isinstance(conditions[0], tuple) else conditions[0]
            clean_cond = cond.replace('0xHEX', 'value').replace('N', '0').replace('"STR"', '"test"')
            lines.append(f"{indent}if ({clean_cond})")
            lines.append(f"{indent}{{")
            if calls:
                lines.append(f"{indent}{indent}{calls[0]}();")
            lines.append(f"{indent}{indent}result = 1;")
            lines.append(f"{indent}}}")
        else:
            if calls:
                lines.append(f"{indent}result = {calls[0]}();")
            else:
                lines.append(f"{indent}result = 0;")
        return lines
    
    def _apply_learned_patterns(self, source_code: str, requirements: str) -> str:
        """Apply learned patterns to enhance source code"""
        enhanced = source_code
        
        # This is where we would apply transformations based on learned patterns
        # For now, return the source with comments about what could be applied
        
        patterns_applied = []
        
        # Check if we should add null checks
        null_checks = self.knowledge.knowledge["patterns"]["null_check_patterns"]
        if null_checks:
            patterns_applied.append(f"// Could apply null-check pattern: {null_checks[0]}")
        
        # Check naming convention
        naming = self.knowledge.get_naming_style()
        if naming != "unknown":
            patterns_applied.append(f"// Naming convention: {naming}")
        
        if patterns_applied:
            enhanced += "\n\n/* Learned Patterns Available:\n"
            enhanced += '\n'.join(f" * {p}" for p in patterns_applied)
            enhanced += "\n*/"
        
        return enhanced
    
    def _generate_generic_function(self, func_name: str, description: str, 
                                    naming_style: str, indent: str) -> str:
        """Generate function when no similar pattern found"""
        return_type = self._infer_return_type(func_name)
        return f"""{return_type} {func_name}(void* context)
{{
{indent}// Auto-generated - no similar pattern found in knowledge
{indent}// Description: {description or 'N/A'}
{indent}// Consider learning more source files for better generation
    
{indent}return {'0' if return_type != 'void' else ''};
}}"""


# ============================================================
# FLOW EXTRACTOR - Tự tạo flow từ code
# ============================================================
class FlowExtractor:
    """Extract và hiển thị flow từ code"""
    
    def __init__(self, knowledge: KnowledgeEngine):
        self.knowledge = knowledge
    
    def extract_from_code(self, code: str) -> str:
        """Extract flow visualization from code"""
        parser = CodeParser()
        patterns = parser.parse(code, "flow_analysis")
        
        lines = []
        lines.append(c("═" * 50, Color.CYAN))
        lines.append(c("  📊 EXTRACTED FLOW", Color.BOLD))
        lines.append(c("═" * 50, Color.CYAN))
        lines.append("")
        
        # Functions found
        if patterns["functions"]:
            lines.append(c("  FUNCTIONS:", Color.GREEN))
            for func in patterns["functions"]:
                lines.append(c(f"    ▸ {func['full_signature']}", Color.WHITE))
            lines.append("")
        
        # Variables
        if patterns["variables"]:
            unique_vars = {}
            for v in patterns["variables"]:
                key = v["name"]
                if key not in unique_vars:
                    unique_vars[key] = v
            lines.append(c("  VARIABLES:", Color.GREEN))
            for v in list(unique_vars.values())[:15]:
                lines.append(c(f"    ▸ {v.get('type', '?')} {v['name']}", Color.WHITE))
            lines.append("")
        
        # Flow diagram
        lines.append(c("  CONTROL FLOW:", Color.GREEN))
        
        # Conditions
        if patterns["conditions"]:
            lines.append(c("    ┌─ CONDITIONS", Color.YELLOW))
            for cond in patterns["conditions"][:5]:
                short_cond = cond[:60] + "..." if len(cond) > 60 else cond
                lines.append(c(f"    │  ◇ if ({short_cond})", Color.DIM))
            lines.append(c("    └───────────", Color.YELLOW))
        
        # Loops
        if patterns["loops"]:
            lines.append(c("    ┌─ LOOPS", Color.YELLOW))
            for loop in patterns["loops"][:5]:
                if isinstance(loop, dict):
                    lines.append(c(f"    │  ↻ {loop.get('type', '?')}: {str(loop.get('pattern', ''))[:50]}", Color.DIM))
                else:
                    lines.append(c(f"    │  ↻ {loop}", Color.DIM))
            lines.append(c("    └───────────", Color.YELLOW))
        
        # Function calls
        if patterns["function_calls"]:
            call_counts = Counter([c["name"] for c in patterns["function_calls"]])
            lines.append(c("    ┌─ FUNCTION CALLS", Color.YELLOW))
            for name, count in call_counts.most_common(10):
                lines.append(c(f"    │  ▸ {name}() (×{count})", Color.DIM))
            lines.append(c("    └───────────", Color.YELLOW))
        
        # Pointer operations
        if patterns["pointer_ops"]:
            lines.append(c("    ┌─ POINTER OPS", Color.MAGENTA))
            for ptr in set(patterns["pointer_ops"])[:5]:
                lines.append(c(f"    │  ▸ {ptr}", Color.DIM))
            lines.append(c("    └───────────", Color.MAGENTA))
        
        # Null checks
        if patterns["null_checks"]:
            lines.append(c("    ┌─ SAFETY CHECKS", Color.GREEN))
            for nc in set(patterns["null_checks"])[:3]:
                lines.append(c(f"    │  ✓ {nc[:50]}", Color.DIM))
            lines.append(c("    └───────────", Color.GREEN))
        
        lines.append("")
        lines.append(c("  CODE STYLE:", Color.GREEN))
        lines.append(c(f"    • Naming: {patterns.get('naming_style', {}).get('dominant', 'unknown')}", Color.WHITE))
        lines.append(c(f"    • Indentation: {patterns.get('indentation', 4)} spaces", Color.WHITE))
        lines.append(c(f"    • Brace style: {patterns.get('brace_style', 'unknown')}", Color.WHITE))
        lines.append("")
        lines.append(c("═" * 50, Color.CYAN))
        
        return '\n'.join(lines)
    
    def show_knowledge_flow(self) -> str:
        """Show flow/patterns from learned knowledge"""
        stats = self.knowledge.get_statistics()
        sources = self.knowledge.get_sources()
        
        lines = []
        lines.append(c("═" * 50, Color.MAGENTA))
        lines.append(c("  🧠 KNOWLEDGE FLOW", Color.BOLD))
        lines.append(c("═" * 50, Color.MAGENTA))
        lines.append("")
        
        # Stats
        lines.append(c("  STATISTICS:", Color.GREEN))
        lines.append(c(f"    • Sources learned: {self.knowledge.knowledge['sources_learned']}", Color.WHITE))
        lines.append(c(f"    • Total functions: {stats.get('total_functions', 0)}", Color.WHITE))
        lines.append(c(f"    • Total variables: {stats.get('total_variables', 0)}", Color.WHITE))
        lines.append(c(f"    • Total patterns: {stats.get('total_patterns', 0)}", Color.WHITE))
        lines.append("")
        
        # Sources
        if sources:
            lines.append(c("  LEARNED SOURCES:", Color.GREEN))
            for src in sources:
                lines.append(c(f"    📄 {src['file']} ({src.get('language', '?')}) - {src.get('functions_found', 0)} funcs", Color.WHITE))
            lines.append("")
        
        # Common patterns
        common_calls = self.knowledge.get_common_calls(5)
        if common_calls:
            lines.append(c("  TOP CALLED FUNCTIONS:", Color.YELLOW))
            for name, count in common_calls:
                lines.append(c(f"    ▸ {name}() — ×{count}", Color.WHITE))
            lines.append("")
        
        # Naming convention
        lines.append(c("  NAMING CONVENTION:", Color.YELLOW))
        lines.append(c(f"    → {self.knowledge.get_naming_style()}", Color.WHITE))
        lines.append("")
        
        # Types discovered
        types = self.knowledge.get_types()
        if types:
            lines.append(c("  TYPES DISCOVERED:", Color.CYAN))
            lines.append(c(f"    {', '.join(types[:20])}", Color.WHITE))
            lines.append("")
        
        lines.append(c("═" * 50, Color.MAGENTA))
        
        return '\n'.join(lines)


# ============================================================
# CHAT INTERFACE
# ============================================================
class ChatInterface:
    """Giao diện chat đơn giản"""
    
    def __init__(self, knowledge: KnowledgeEngine, generator: CodeGenerator, flow_extractor: FlowExtractor):
        self.knowledge = knowledge
        self.generator = generator
        self.flow_extractor = flow_extractor
        self.history = []
        self.current_code = ""
        self.last_generated = ""
    
    def start(self):
        """Start chat loop"""
        print(c("\n" + "═" * 56, Color.CYAN))
        print(c("  🔧 CODE SELF-LEARNING TOOL - CHAT MODE", Color.BOLD))
        print(c("═" * 56, Color.CYAN))
        print(c("  Type 'help' for commands | 'exit' to quit", Color.DIM))
        print(c("═" * 56 + "\n", Color.CYAN))
        
        while True:
            try:
                user_input = input(c("❯ ", Color.GREEN)).strip()
                
                if not user_input:
                    continue
                
                self.history.append(("user", user_input))
                response = self._process_input(user_input)
                
                if response is None:
                    break
                
                if response:
                    print(c("\n🤖 ", Color.MAGENTA), end="")
                    print(response)
                    print()
                    
            except KeyboardInterrupt:
                print(c("\n\n👋 Goodbye!", Color.YELLOW))
                break
            except Exception as e:
                print(c(f"\n⚠ Error: {e}", Color.RED))
    
    def _process_input(self, user_input: str) -> Optional[str]:
        """Xử lý input từ user"""
        cmd = user_input.lower()
        
        # Commands
        if cmd in ['exit', 'quit', 'q']:
            return None
        
        elif cmd == 'help':
            return self._show_help()
        
        elif cmd == 'show flow':
            if self.current_code:
                return self.flow_extractor.extract_from_code(self.current_code)
            else:
                return self.flow_extractor.show_knowledge_flow()
        
        elif cmd == 'show knowledge':
            return self.flow_extractor.show_knowledge_flow()
        
        elif cmd == 'show stats':
            stats = self.knowledge.get_statistics()
            return json.dumps(stats, indent=2)
        
        elif cmd.startswith('learn '):
            filepath = user_input[6:].strip()
            return self._learn_file(filepath)
        
        elif cmd.startswith('learn all'):
            return self._learn_all_examples()
        
        elif cmd.startswith('generate '):
            func_desc = user_input[9:].strip()
            return self._generate_function_cmd(func_desc)
        
        elif cmd.startswith('analyze '):
            filepath = user_input[8:].strip()
            return self._analyze_file(filepath)
        
        elif cmd.startswith('load '):
            filepath = user_input[5:].strip()
            return self._load_file(filepath)
        
        elif cmd.startswith('save '):
            filepath = user_input[5:].strip()
            return self._save_generated(filepath)
        
        elif cmd.startswith('correct '):
            # User wants to teach from correction
            desc = user_input[9:].strip()
            return c("Please paste the corrected code (end with empty line):\n", Color.CYAN)
        
        elif cmd == 'clear':
            self.current_code = ""
            self.last_generated = ""
            return c("✓ Current code cleared.", Color.GREEN)
        
        elif cmd == 'history':
            return '\n'.join(f"  {u}: {m}" for u, m in self.history[-10:])
        
        else:
            # Try to interpret as generate request
            return self._generate_function_cmd(user_input)
    
    def _show_help(self) -> str:
        return textwrap.dedent("""
        ════════════════════════════════════════════
          AVAILABLE COMMANDS
        ════════════════════════════════════════════
        
          📚 LEARNING:
            learn <path>       - Learn from a file
            learn all          - Learn from examples/
            correct <desc>     - Teach from your correction
        
          🔍 ANALYSIS:
            analyze <path>     - Show flow of a file
            load <path>        - Load file as current code
            show flow          - Show extracted flow
            show knowledge     - Show learned knowledge
            show stats         - Show statistics
        
          ⚡ GENERATION:
            generate <func>    - Generate a function
            <any text>         - Auto-generate (interpreted)
        
          💾 FILE OPS:
            save <path>        - Save last generated code
            clear              - Clear current code
            history            - Show chat history
        
          🎮 SYSTEM:
            help               - Show this help
            exit               - Quit
        ════════════════════════════════════════════
        """)
    
    def _learn_file(self, filepath: str) -> str:
        """Learn from a single file"""
        if not os.path.exists(filepath):
            return c(f"✗ File not found: {filepath}", Color.RED)
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            parser = CodeParser()
            parser.parse(code, filepath)
            
            if self.knowledge.learn_from_parser(parser, filepath, code):
                return c(f"✓ Learned from: {filepath}\n"
                        f"  Functions found: {len(parser.patterns['functions'])}\n"
                        f"  Variables found: {len(parser.patterns['variables'])}", Color.GREEN)
            else:
                return c(f"ℹ Already learned: {filepath}", Color.CYAN)
                
        except Exception as e:
            return c(f"✗ Error learning file: {e}", Color.RED)
    
    def _learn_all_examples(self) -> str:
        """Learn all files from examples directory"""
        examples_dir = Path(CONFIG["examples_dir"])
        
        if not examples_dir.exists():
            return c(f"✗ Examples directory not found: {CONFIG['examples_dir']}", Color.RED)
        
        results = []
        files_learned = 0
        
        for ext in CONFIG["supported_extensions"]:
            for filepath in examples_dir.glob(f"*{ext}"):
                result = self._learn_file(str(filepath))
                results.append(result)
                if "✓" in result:
                    files_learned += 1
        
        summary = c(f"\n═══ SUMMARY: {files_learned} files learned ═══\n", Color.BOLD)
        return '\n\n'.join(results) + ('\n' + summary if results else '')
    
    def _generate_function_cmd(self, func_desc: str) -> str:
        """Generate a function from description"""
        # Try to extract function name
        func_name = func_desc.split()[0] if func_desc else "unnamed"
        # Clean function name
        func_name = re.sub(r'[^\w]', '', func_name)
        
        if not func_name:
            return c("✗ Please specify a function name", Color.RED)
        
        generated = self.generator.generate_function(func_name, func_desc, self.current_code)
        self.last_generated = generated
        
        return c(f"✓ Generated function: {func_name}\n", Color.GREEN) + c(generated, Color.WHITE)
    
    def _analyze_file(self, filepath: str) -> str:
        """Analyze a file and show its flow"""
        if not os.path.exists(filepath):
            return c(f"✗ File not found: {filepath}", Color.RED)
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            return self.flow_extractor.extract_from_code(code)
        except Exception as e:
            return c(f"✗ Error analyzing file: {e}", Color.RED)
    
    def _load_file(self, filepath: str) -> str:
        """Load a file as current working code"""
        if not os.path.exists(filepath):
            return c(f"✗ File not found: {filepath}", Color.RED)
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                self.current_code = f.read()
            return c(f"✓ Loaded: {filepath} ({len(self.current_code)} chars)", Color.GREEN)
        except Exception as e:
            return c(f"✗ Error loading file: {e}", Color.RED)
    
    def _save_generated(self, filepath: str) -> str:
        """Save last generated code to file"""
        if not self.last_generated:
            return c("✗ No generated code to save", Color.RED)
        
        try:
            os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.last_generated)
            return c(f"✓ Saved to: {filepath}", Color.GREEN)
        except Exception as e:
            return c(f"✗ Error saving: {e}", Color.RED)
    
    def learn_correction(self, original: str, modified: str, description: str = ""):
        """Learn from user's correction"""
        self.knowledge.learn_from_diff(original, modified, description)


# ============================================================
# MAIN APPLICATION
# ============================================================
class SelfLearningTool:
    """Main application class"""
    
    def __init__(self):
        self.knowledge = KnowledgeEngine(CONFIG["knowledge_file"])
        self.generator = CodeGenerator(self.knowledge)
        self.flow_extractor = FlowExtractor(self.knowledge)
        self.chat = ChatInterface(self.knowledge, self.generator, self.flow_extractor)
    
    def run_cli(self, args: List[str] = None):
        """Run in CLI mode"""
        if not args:
            args = sys.argv[1:]
        
        if not args:
            # No args - start interactive mode
            self._print_banner()
            self.chat.start()
            return
        
        # Process command line arguments
        cmd = args[0]
        
        if cmd == "learn":
            if len(args) > 1:
                print(self.chat._learn_file(args[1]))
            else:
                print(self.chat._learn_all_examples())
        
        elif cmd == "generate":
            if len(args) > 1:
                func_name = args[1]
                desc = ' '.join(args[2:]) if len(args) > 2 else ""
                print(self.generator.generate_function(func_name, desc))
            else:
                print(c("Usage: main.py generate <function_name> [description]", Color.YELLOW))
        
        elif cmd == "analyze":
            if len(args) > 1:
                print(self.chat._analyze_file(args[1]))
            else:
                print(c("Usage: main.py analyze <file>", Color.YELLOW))
        
        elif cmd == "flow":
            print(self.flow_extractor.show_knowledge_flow())
        
        elif cmd == "chat":
            self._print_banner()
            self.chat.start()
        
        else:
            # Treat as function name to generate
            print(self.generator.generate_function(cmd, ' '.join(args[1:])))
    
    def _print_banner(self):
        """Print ASCII banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║   ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗                 ║
║   ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝                 ║
║   ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗                 ║
║   ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║                 ║
║   ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║                 ║
║   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝                 ║
║                                                                ║
║              CODE SELF-LEARNING TOOL v1.0                      ║
║         "Show me code → I learn → I generate"                  ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(c(banner, Color.CYAN))


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    tool = SelfLearningTool()
    tool.run_cli()
