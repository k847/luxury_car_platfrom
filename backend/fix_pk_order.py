# 段功能：一次性修正脚本——修正 primary_key 位置（原被插到位置参数前导致语法错误）
# 说明：把 `Column(primary_key=True, ...)` 改为 `Column(..., primary_key=True, comment=...)`，
#       即把 primary_key=True 作为关键字参数放到 comment 之前。
# 用法：python fix_pk_order.py

import re
import pathlib

p = pathlib.Path("app/models.py")
lines = p.read_text(encoding="utf-8").split("\n")

out = []
cnt = 0
for line in lines:
    if "Column(primary_key=True," in line:
        # 1) 移除 Column( 后的 primary_key=True,
        line = line.replace("Column(primary_key=True, ", "Column(", 1)
        # 2) 在最后的 comment="...") 前插入 primary_key=True
        line = re.sub(r'(, comment="[^"]*"\))', r", primary_key=True\1", line)
        cnt += 1
    out.append(line)

p.write_text("\n".join(out), encoding="utf-8")
print("fixed lines:", cnt)
