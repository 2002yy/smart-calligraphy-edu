"""Add permission controls to homework routes + fix Qwen prompt terminology"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in dir() else r"C:\Users\96967\Desktop\大创\code"
if not os.path.isdir(os.path.join(ROOT, "api-server")):
    ROOT = r"C:\Users\96967\Desktop\大创\code"

# === Fix 1: homework.py ===
fp = os.path.join(ROOT, "api-server", "app", "api", "routes", "homework.py")
with open(fp, encoding="utf-8") as f:
    lines = f.readlines()

# Track current function
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]

    # submit_homework: add auth
    if 'def submit_homework(payload: HomeworkSubmitRequest, db: Session = Depends(get_db)):' in line:
        new_lines.append('def submit_homework(payload: HomeworkSubmitRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):\n')
        new_lines.append('    if current_user["role"] == "student" and payload.student_id is not None and payload.student_id != current_user["id"]:\n')
        new_lines.append('        raise HTTPException(status_code=403, detail="学生只能提交自己的作业")\n')
        new_lines.append('    if current_user["role"] == "student" and payload.student_id is None:\n')
        new_lines.append('        payload.student_id = current_user["id"]\n')
        i += 1
        while i < len(lines) and 'def ' not in lines[i]:
            if 'return APIResponse' in lines[i]:
                new_lines.append(lines[i]); i += 1; break
            i += 1
        continue

    # list_homework: add auth, remove student_id param
    if 'def list_homework(' in line:
        new_lines.append('def list_homework(\n')
        i += 1
        # read params
        while i < len(lines) and '):' not in lines[i]:
            i += 1
        # finished reading params, now write ours
        new_lines.append('    task_id: int | None = None,\n')
        new_lines.append('    status: str | None = None,\n')
        new_lines.append('    current_user: dict = Depends(get_current_user),\n')
        new_lines.append('    db: Session = Depends(get_db),\n')
        new_lines.append('):\n')
        new_lines.append('    student_id = current_user["id"] if current_user["role"] == "student" else None\n')
        i += 1  # skip past ):
        # find the data = [...] block
        while i < len(lines) and '    return APIResponse' not in lines[i]:
            new_lines.append(lines[i]); i += 1
        # skip the old return
        new_lines.append('    data = [HomeworkRead(**item) for item in HomeworkService.list_homework(db, task_id=task_id, student_id=student_id, status=status)]\n')
        new_lines.append(lines[i]); i += 1  # return APIResponse line
        # skip any remaining closing bracket
        if i < len(lines) and '    ]' in lines[i]:
            i += 1  # skip ]
        continue

    # get_homework
    if 'def get_homework(homework_id: int, db: Session = Depends(get_db)):' in line:
        new_lines.append('def get_homework(homework_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):\n')
        new_lines.append('    hw = HomeworkService.get_homework(db, homework_id)\n')
        new_lines.append('    if current_user["role"] == "student" and current_user["id"] != hw["student_id"]:\n')
        new_lines.append('        raise HTTPException(status_code=403, detail="学生只能查看自己的作业")\n')
        new_lines.append('    data = HomeworkRead(**hw)\n')
        new_lines.append('    return APIResponse[HomeworkRead](data=data)\n')
        i += 1
        while i < len(lines) and 'def ' not in lines[i]:
            i += 1
        continue

    new_lines.append(line)
    i += 1

with open(fp, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("1. homework.py OK")


# === Fix 2: Qwen prompt terminology ===
fp2 = os.path.join(ROOT, "api-server", "app", "services", "qwen_evaluation_service.py")
with open(fp2, encoding="utf-8") as f:
    s = f.read()

replacements = [
    ("【评分体系】三个维度，权重不同：\n"
     '                        "1. 结构 (权重 40%)：间架结构是否合理，中宫是否收紧，主笔是否突出\n'
     '                        "2. 重心 (权重 30%)：整体重心是否平稳，左右是否平衡\n'
     '                        "3. 笔顺 (权重 30%)：笔画顺序是否正确，运笔是否流畅\n',
     '                        "【评分体系】三个维度，权重不同：\n'
     '                        "1. 结构 (权重 40%)：间架结构是否合理，中宫是否收紧，主笔是否突出\n'
     '                        "2. 重心 (权重 30%)：整体重心是否平稳，左右是否平衡\n'
     '                        "3. 笔法 (权重 30%)：笔画规范性、运笔痕迹、起收笔质量\n'),
    ("1-2 ：几乎无训练痕迹，完不成基本书写", "1-2 ：几乎无训练痕迹，完不成基本书写"),
    ('差的标签：中宫松散、重心偏左/偏右、撇捺角度过大、横画扛肩过度、\n'
     '                        "竖画不直、主笔不突出、疏密不当、笔顺有误、运笔生硬、'
     '                        "差的标签：中宫松散、重心偏左/偏右、撇捺角度过大、横画扛肩过度、\n'
     '                        "竖画不直、主笔不突出、疏密不当、笔法有误、运笔生硬、'),
]

# Simpler approach: direct string replacements
s = s.replace('笔顺 (权重 30%)：笔画顺序是否正确，运笔是否流畅', '笔法 (权重 30%)：笔画规范性、运笔痕迹、起收笔质量')
s = s.replace('差的标签：中宫松散、重心偏左/偏右、撇捺角度过大、横画扛肩过度、\n                        "竖画不直、主笔不突出、疏密不当、笔顺有误、运笔生硬、', '差的标签：中宫松散、重心偏左/偏右、撇捺角度过大、横画扛肩过度、\n                        "竖画不直、主笔不突出、疏密不当、笔法有误、运笔生硬、')
s = s.replace('差的标签：中宫松散、重心偏左/偏右、撇捺角度过大、横画扛肩过度、"竖画不直、主笔不突出、疏密不当、笔顺有误、运笔生硬、', '差的标签：中宫松散、重心偏左/偏右、撇捺角度过大、横画扛肩过度、\n                        "竖画不直、主笔不突出、疏密不当、笔法有误、运笔生硬、')
s = s.replace('5-6 ：不及格水平，结构松散、重心不稳或笔顺有明显问题', '5-6 ：不及格水平，结构松散、重心不稳或笔法有明显问题')
s = s.replace('差的标签：中宫松散、重心偏左/偏右、撇捺角度过大、横画扛肩过度、"竖画不直、主笔不突出、疏密不当、笔顺有误、运笔生硬、\n                        "结构失衡、大小不一、间距不均、笔画过细/过粗、起笔收笔草率', '差的标签：中宫松散、重心偏左/偏右、撇捺角度过大、横画扛肩过度、\n                        "竖画不直、主笔不突出、疏密不当、笔法有误、运笔生硬、\n                        "结构失衡、大小不一、间距不均、笔画过细/过粗、起笔收笔草率')
s = s.replace('"笔顺验证"', '"笔法验证"')

# stroke_order_score -> stroke_order_score (keep field names)
# In the output JSON spec, change the description
s = s.replace('"stroke_order_score": <0-10 一位小数>,\n                "stroke_order_observation": "笔顺观察，一句话",\n                "stroke_order_suggestion": "笔顺修改建议，一句话"',
              '"stroke_order_score": <0-10 一位小数>,\n                "stroke_order_observation": "笔法观察，一句话",\n                "stroke_order_suggestion": "笔法修改建议，一句话"')

# Update thinking steps Step 6
s = s.replace('{"step":6,"title":"笔顺验证","detail":"观察","score":分数}', '{"step":6,"title":"笔法验证","detail":"观察","score":分数}')

with open(fp2, "w", encoding="utf-8") as f:
    f.write(s)
print("2. qwen_evaluation_service.py OK")


print("\nDone!")
