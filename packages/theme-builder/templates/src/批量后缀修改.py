import os
# 指定目标文件夹路径
folder_path = "./"
# 遍历文件夹中的所有文件
for filename in os.listdir(folder_path):
   if filename.endswith(".vue"): # 检查后缀名
       new_name = filename.replace(".vue", ".vue.tpl") # 替换后缀
       os.rename(os.path.join(folder_path, filename), os.path.join(folder_path, new_name))
print("批量修改完成！")