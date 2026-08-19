# 段功能：一次性修正脚本——为 7 张 *_i18n 翻译表补 (实体id, lang) 联合主键
# 说明：原 models.py 的 i18n 表只声明了 UniqueConstraint 未声明主键，SQLAlchemy 无法映射。
#       本脚本仅对 I18n 类块生效：给实体 FK 列和 lang 列加 primary_key=True，
#       并删除冗余的 UniqueConstraint（联合主键已保证 (实体id, lang) 唯一）。
# 用法：python fix_i18n_pk.py   （仅在需要重建 models.py 时运行）

import re
import pathlib

p = pathlib.Path("app/models.py")
lines = p.read_text(encoding="utf-8").split("\n")

out = []
i = 0
n = len(lines)
in_i18n = False
fixed_fk = 0
fixed_lang = 0
removed_uc = 0

while i < n:
    line = lines[i]
    # 进入 I18n 类块
    if re.match(r"^class \w+I18n\(Base, I18nColumns\):", line):
        in_i18n = True
        out.append(line)
        i += 1
        continue
    # 离开 I18n 类块（遇到下一个顶层 class）
    if re.match(r"^class \w+\(", line) and not line.startswith("    "):
        in_i18n = False
    if in_i18n:
        # 实体 FK 列：含 ForeignKey( 的 *_id 列
        if re.match(r"^\s+\w+_id = Column\(", line) and "ForeignKey(" in line and "primary_key" not in line:
            line = re.sub(r"^((\s+)\w+_id = Column\()", r"\1primary_key=True, ", line, count=1)
            fixed_fk += 1
        # lang 列
        if re.match(r"^\s+lang = Column\(String\(8\),", line) and "primary_key" not in line:
            line = re.sub(r"^((\s+)lang = Column\()", r"\1primary_key=True, ", line, count=1)
            fixed_lang += 1
        # 删除冗余 UniqueConstraint 行（联合主键已保证唯一）
        if "__table_args__ = (UniqueConstraint(" in line:
            removed_uc += 1
            if line.rstrip().endswith(","):
                i += 1
                if i < n and lines[i].strip() == ")":
                    i += 1
            i += 1
            continue
    out.append(line)
    i += 1

p.write_text("\n".join(out), encoding="utf-8")
print(f"fixed_fk={fixed_fk} fixed_lang={fixed_lang} removed_uc={removed_uc}")
